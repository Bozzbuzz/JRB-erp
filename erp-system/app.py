import os
import sys
# Ensure erp-system directory is in Python path for Vercel/local execution
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, render_template, request, redirect, url_for
from models import db, Customer, Vendor, Order, Payment
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.context_processor
def inject_global_dates():
    first_order = Order.query.order_by(Order.book_date.asc()).first()
    last_order = Order.query.order_by(Order.book_date.desc()).first()
    return dict(
        db_first_date=first_order.book_date if first_order and first_order.book_date else "2020-01-01",
        db_last_date=last_order.book_date if last_order and last_order.book_date else ""
    )
@app.route('/')
def dashboard():
    import calendar
    from datetime import date, datetime
    
    today = date.today()
    default_start = today.replace(day=1).strftime('%Y-%m-%d')
    last_day = calendar.monthrange(today.year, today.month)[1]
    default_end = today.replace(day=last_day).strftime('%Y-%m-%d')
    
    start_date = request.args.get('start_date', default_start)
    end_date = request.args.get('end_date', default_end)
    
    base_query = db.session.query(Order).filter(Order.book_date >= start_date, Order.book_date <= end_date)
    
    total_sales = base_query.with_entities(func.sum(Order.total_sell)).scalar() or 0
    total_buy = base_query.with_entities(func.sum(Order.total_buy)).scalar() or 0
    profit = total_sales - total_buy
    
    # Dynamic metrics based on date range
    total_orders = base_query.count()
    active_fleet = base_query.filter(Order.status != 'CANCEL').count()
    total_fleet = 173 # static total fleet
    
    # Orders not fully paid (usually we want all pending, not just this month)
    pending_orders = Order.query.filter(Order.status != 'COMPLETE').limit(4).all()
    
    # Recent orders (filtered by date)
    recent_orders = base_query.order_by(Order.book_date.desc()).limit(5).all()
    
    try:
        sd = datetime.strptime(start_date, '%Y-%m-%d')
        ed = datetime.strptime(end_date, '%Y-%m-%d')
        date_label = f"{sd.strftime('%b %d, %Y')} - {ed.strftime('%b %d, %Y')}"
    except:
        date_label = f"{start_date} - {end_date}"
    
    return render_template('dashboard.html', 
                           total_sales=total_sales, 
                           profit=profit, 
                           total_orders=total_orders,
                           active_fleet=active_fleet,
                           total_fleet=total_fleet,
                           pending_orders=pending_orders, 
                           recent_orders=recent_orders,
                           date_label=date_label,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/orders', methods=['GET'])
def orders():
    import calendar
    from datetime import date, datetime
    
    today = date.today()
    default_start = today.replace(day=1).strftime('%Y-%m-%d')
    last_day = calendar.monthrange(today.year, today.month)[1]
    default_end = today.replace(day=last_day).strftime('%Y-%m-%d')
    
    start_date = request.args.get('start_date', default_start)
    end_date = request.args.get('end_date', default_end)
    
    base_query = db.session.query(Order).filter(Order.book_date >= start_date, Order.book_date <= end_date)
    orders_list = base_query.order_by(Order.book_date.desc()).limit(100).all()
    
    try:
        sd = datetime.strptime(start_date, '%Y-%m-%d')
        ed = datetime.strptime(end_date, '%Y-%m-%d')
        date_label = f"{sd.strftime('%b %d, %Y')} - {ed.strftime('%b %d, %Y')}"
    except:
        date_label = f"{start_date} - {end_date}"
        
    return render_template('orders.html', 
                           orders=orders_list,
                           date_label=date_label,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/orders/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        departure_date_str = request.form.get('departure_date')
        return_date_str = request.form.get('return_date')
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        
        from datetime import datetime
        dep_date = datetime.strptime(departure_date_str, '%Y-%m-%d').date() if departure_date_str else None
        ret_date = datetime.strptime(return_date_str, '%Y-%m-%d').date() if return_date_str else None
        
        vendors = request.form.getlist('vendor_id[]')
        vehicle_types = request.form.getlist('vehicle_type[]')
        qtys = request.form.getlist('qty[]')
        sell_prices = request.form.getlist('sell_price[]')
        
        import random
        base_id = f"JRB-{random.randint(100000, 999999)}"
        
        for i in range(len(vendors)):
            v_id = vendors[i]
            v_type = vehicle_types[i] if i < len(vehicle_types) else ''
            qty = float(qtys[i]) if i < len(qtys) and qtys[i] else 1.0
            price = float(sell_prices[i]) if i < len(sell_prices) and sell_prices[i] else 0.0
            
            new_order = Order(
                id_bitrix=f"{base_id}.{i}",
                book_date=datetime.now().date(),
                departure_date=dep_date,
                return_date=ret_date,
                origin=origin,
                destination=destination,
                customer_id=customer_id if customer_id else None,
                vendor_id=v_id if v_id else None,
                vehicle_type=v_type,
                qty_sell=qty,
                sell_price=price,
                total_sell=qty * price,
                status='NEW'
            )
            db.session.add(new_order)
            
        db.session.commit()
        return redirect(url_for('orders'))
    
    # fetch vendors for the dropdown
    vendors_list = Vendor.query.order_by(Vendor.name).all()
    # fetch distinct vehicle types dynamically
    vehicle_types_query = db.session.query(Order.vehicle_type).distinct().filter(Order.vehicle_type != None).order_by(Order.vehicle_type).all()
    vehicle_types_list = [v[0] for v in vehicle_types_query if v[0].strip()]
    return render_template('order_new.html', vendors=vendors_list, vehicle_types=vehicle_types_list)

@app.route('/crm')
def crm():
    customers = Customer.query.order_by(Customer.id.desc()).all()
    return render_template('crm.html', customers=customers)

@app.route('/api/customers/search')
def api_customers_search():
    query = request.args.get('q', '').strip()
    if not query:
        return {'results': []}
    
    # Search by name or phone
    search_term = f"%{query}%"
    customers = Customer.query.filter(
        db.or_(Customer.name.ilike(search_term), Customer.phone.ilike(search_term))
    ).limit(10).all()
    
    results = [{'id': c.id, 'name': c.name, 'phone': c.phone} for c in customers]
    return {'results': results}

@app.route('/api/customers/new', methods=['POST'])
def api_customers_new():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    nik = request.form.get('nik')
    company = request.form.get('company')
    
    # Save photo if exists
    photo_filename = None
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename != '':
            # Simple unique filename
            import uuid
            import os
            ext = os.path.splitext(photo.filename)[1]
            photo_filename = f"{uuid.uuid4()}{ext}"
            upload_dir = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            photo.save(os.path.join(upload_dir, photo_filename))
            
    customer = Customer(
        name=name,
        phone=phone,
        email=email,
        address=address,
        nik=nik,
        company=company,
        photo=photo_filename
    )
    db.session.add(customer)
    db.session.commit()
    
    return {'success': True, 'customer': {'id': customer.id, 'name': customer.name, 'phone': customer.phone}}

@app.route('/crm/<int:customer_id>')
def crm_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Calculate metrics
    total_sales = sum([order.total_sell for order in customer.orders])
    total_profit = sum([(order.total_sell - order.total_buy) for order in customer.orders])
    total_units = sum([order.qty_sell for order in customer.orders])
    
    return render_template('crm_detail.html', 
                           customer=customer, 
                           total_sales=total_sales, 
                           total_profit=total_profit, 
                           total_units=total_units)

@app.route('/vendors')
def vendors():
    vendors_list = Vendor.query.all()
    # Fetch recent orders that represent a buy from a vendor
    buy_history = Order.query.filter(Order.vendor_id != None).order_by(Order.book_date.desc()).limit(10).all()
    
    return render_template('vendors.html', vendors=vendors_list, buy_history=buy_history)

@app.route('/finance')
def finance():
    # Calculate global totals
    total_sales = db.session.query(func.sum(Order.total_sell)).scalar() or 0
    total_dp = db.session.query(func.sum(Payment.amount)).filter(Payment.payment_type == 'DP').scalar() or 0
    total_full = db.session.query(func.sum(Payment.amount)).filter(Payment.payment_type == 'FULL').scalar() or 0
    total_receivables = total_sales - (total_dp + total_full)
    
    # Process orders for the table
    orders_query = Order.query.order_by(Order.book_date.desc()).limit(100).all()
    finance_orders = []
    
    for order in orders_query:
        dp = sum([p.amount for p in order.payments if p.payment_type == 'DP'])
        full = sum([p.amount for p in order.payments if p.payment_type == 'FULL'])
        balance = order.total_sell - (dp + full)
        
        finance_orders.append({
            'order': order,
            'dp': dp,
            'full': full,
            'balance': balance
        })
        
    return render_template('finance.html', 
                           total_receivables=total_receivables,
                           total_dp=total_dp,
                           total_full=total_full,
                           finance_orders=finance_orders)

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/kpi-data')
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

@app.route('/kanban')
def kanban():
    orders_query = Order.query.order_by(Order.book_date.desc()).limit(300).all()
    orders_by_status = {
        'NEW': [],
        'FOLLOW UP': [],
        'QUOTATION': [],
        'OPERATION': [],
        'WON': [],
        'LOST': []
    }
    for order in orders_query:
        # Default to NEW if no status or unmapped status
        status = order.status if order.status in orders_by_status else 'NEW'
        orders_by_status[status].append(order)
        
    return render_template('kanban.html', orders_by_status=orders_by_status)

@app.route('/api/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.json
    new_status = data.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        return {'success': True}
    return {'success': False}, 400

@app.route('/analytics')
def analytics():
    import calendar
    from datetime import date
    
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
    
    from datetime import datetime
    try:
        sd = datetime.strptime(start_date, '%Y-%m-%d')
        ed = datetime.strptime(end_date, '%Y-%m-%d')
        date_label = f"{sd.strftime('%b %d, %Y')} - {ed.strftime('%b %d, %Y')}"
    except:
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
        filters.append(Order.departure_date >= start_date)
    if end_date:
        filters.append(Order.departure_date <= end_date)
    if customer_name:
        filters.append(Customer.name == customer_name)
    if marketing_name:
        filters.append(Order.marketing == marketing_name)
    if vendor_name:
        filters.append(Vendor.name == vendor_name)
        
    # Base query template
    base_query = db.session.query(Order).join(Customer, Order.customer_id == Customer.id, isouter=True) \
                                        .join(Vendor, Order.vendor_id == Vendor.id, isouter=True) \
                                        .filter(*filters)
    
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

@app.route('/kpi')
def kpi_dashboard():
    return render_template('kpi.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
