from flask import Blueprint, render_template, request
from core.extensions import db
from core.models import Order, Customer, Vendor
from datetime import date, datetime
import calendar
from sqlalchemy import func

bp = Blueprint('analytics', __name__)

@bp.route('/analytics')
def analytics():
    # Build filter conditions
    filters = []
    
    # Default to current month if no dates provided
    today = date.today()
    default_start = today.replace(day=1).strftime('%Y-%m-%d')
    last_day = calendar.monthrange(today.year, today.month)[1]
    default_end = today.replace(day=last_day).strftime('%Y-%m-%d')
    
    start_date = request.args.get('start_date') if 'start_date' in request.args else default_start
    end_date = request.args.get('end_date') if 'end_date' in request.args else default_end
    
    customer_name = request.args.get('customer')
    marketing_name = request.args.get('marketing')
    vendor_name = request.args.get('vendor')
    page = request.args.get('page', 1, type=int)
    
    try:
        sd = datetime.strptime(start_date, '%Y-%m-%d')
        ed = datetime.strptime(end_date, '%Y-%m-%d')
        date_label = f"{sd.strftime('%b %d, %Y')} - {ed.strftime('%b %d, %Y')}"
    except ValueError:
        date_label = f"{start_date} - {end_date}"
    
    # For template rendering
    active_filters = {
        'start_date': start_date,
        'end_date': end_date,
        'customer': customer_name,
        'marketing': marketing_name,
        'vendor': vendor_name
    }
    
    if start_date:
        try:
            sd_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            filters.append(Order.departure_date >= sd_obj)
        except ValueError:
            pass
    if end_date:
        try:
            ed_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            filters.append(Order.departure_date <= ed_obj)
        except ValueError:
            pass
    if customer_name:
        filters.append(Customer.name == customer_name)
    if marketing_name:
        filters.append(Order.marketing == marketing_name)
    if vendor_name:
        filters.append(Vendor.name == vendor_name)
        
    # Base query template
    base_query = (db.session.query(Order)
                  .join(Customer, Order.customer_id == Customer.id, isouter=True)
                  .join(Vendor, Order.vendor_id == Vendor.id, isouter=True)
                  .filter(*filters))
    
    # 1. Calculate Metrics via DB
    metrics = base_query.with_entities(func.sum(Order.qty_sell), func.sum(Order.total_sell)).first()
    total_qty_sell = metrics[0] or 0
    total_sell = metrics[1] or 0
    
    # 2. Purchase Summary via DB Group By
    ps_data = base_query.with_entities(func.coalesce(Customer.name, 'Unknown'), 
                                       func.sum(Order.qty_sell), 
                                       func.sum(Order.total_sell), 
                                       func.sum(Order.total_buy)) \
                        .group_by(func.coalesce(Customer.name, 'Unknown')).all()
    purchase_summary = {row[0]: {'unit': row[1] or 0, 'sell': row[2] or 0, 'buy': row[3] or 0} for row in ps_data}
    
    # 3. Marketing Performance via DB Group By
    mp_data = base_query.with_entities(func.coalesce(Order.marketing, 'Unknown'), 
                                       func.sum(Order.total_sell), 
                                       func.count(Order.id)) \
                        .group_by(func.coalesce(Order.marketing, 'Unknown')).all()
    marketing_performance = {}
    for row in mp_data:
        m_name = row[0]
        title = 'Mr.' if len(m_name) % 2 == 0 else 'Ms.'
        marketing_performance[m_name] = {'total': row[1] or 0, 'count': row[2] or 0, 'title': title}
        
    # 4. Destination Count via DB Group By
    ds_data = base_query.with_entities(func.coalesce(Order.destination, 'Unknown'), 
                                       func.count(Order.id)) \
                        .group_by(func.coalesce(Order.destination, 'Unknown')).all()
    destination_summary = {row[0]: row[1] for row in ds_data}
    
    # 5. Mitra / Qty Sell by Date via DB Group By
    md_data = base_query.with_entities(func.coalesce(Vendor.name, 'Unknown'), 
                                       Order.departure_date, 
                                       func.sum(Order.qty_sell)) \
                        .group_by(func.coalesce(Vendor.name, 'Unknown'), Order.departure_date).all()
    mitra_date_summary = {}
    for row in md_data:
        v_name = row[0]
        date_str = row[1].strftime('%Y-%m-%d') if row[1] else 'Unknown'
        if v_name not in mitra_date_summary:
            mitra_date_summary[v_name] = {}
        mitra_date_summary[v_name][date_str] = row[2] or 0
        
    # 6. Paginated Orders for the main table (Server-Side Pagination)
    orders_page = base_query.order_by(Order.departure_date.desc()).paginate(page=page, per_page=20, error_out=False)
    
    # Dropdown lists
    customers = db.session.query(Customer.name).distinct().all()
    marketings = db.session.query(Order.marketing).distinct().all()
    vendors = db.session.query(Vendor.name).distinct().all()
    
    return render_template('analytics.html', 
                           orders_page=orders_page,
                           total_qty_sell=total_qty_sell,
                           total_sell=total_sell,
                           purchase_summary=purchase_summary,
                           marketing_performance=marketing_performance,
                           destination_summary=destination_summary,
                           mitra_date_summary=mitra_date_summary,
                           customers=[c[0] for c in customers if c[0]],
                           marketings=[m[0] for m in marketings if m[0]],
                           vendors=[v[0] for v in vendors if v[0]],
                           filters=active_filters,
                           date_label=date_label,
                           start_date=start_date,
                           end_date=end_date)

@bp.route('/settings')
def settings():
    return render_template('settings.html')

@bp.route('/kpi')
def kpi_dashboard():
    return render_template('kpi.html')

@bp.route('/api/kpi-data')
def api_kpi_data():
    orders = Order.query.all()
    data = []
    for o in orders:
        data.append({
            'id': o.id_bitrix or str(o.id),
            'bookDate': o.book_date.isoformat() if o.book_date else None,
            'marketing': o.marketing or 'Unknown',
            'type': o.vehicle_type or 'Unknown',
            'destination': o.destination or 'Unknown',
            'qtySell': o.qty_sell or 0.0,
            'qtyBuy': o.qty_buy or 0.0,
            'totalSell': o.total_sell or 0.0,
            'totalBuy': o.total_buy or 0.0
        })
    return {'data': data}
