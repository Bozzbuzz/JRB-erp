from flask import Blueprint, render_template, request, redirect, url_for
from core.extensions import db
from core.models import Order, Vendor
from datetime import date, datetime
import calendar
import random

bp = Blueprint('orders', __name__)

@bp.route('/orders', methods=['GET'])
def orders():
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
    except ValueError:
        date_label = f"{start_date} - {end_date}"
        
    return render_template('orders.html', 
                           orders=orders_list,
                           date_label=date_label,
                           start_date=start_date,
                           end_date=end_date)

@bp.route('/orders/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        departure_date_str = request.form.get('departure_date')
        return_date_str = request.form.get('return_date')
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        
        dep_date = datetime.strptime(departure_date_str, '%Y-%m-%d').date() if departure_date_str else None
        ret_date = datetime.strptime(return_date_str, '%Y-%m-%d').date() if return_date_str else None
        
        vendors = request.form.getlist('vendor_id[]')
        vehicle_types = request.form.getlist('vehicle_type[]')
        qtys = request.form.getlist('qty[]')
        sell_prices = request.form.getlist('sell_price[]')
        
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
                customer_id=int(customer_id) if customer_id else None,
                vendor_id=int(v_id) if v_id else None,
                vehicle_type=v_type,
                qty_sell=qty,
                sell_price=price,
                total_sell=qty * price,
                status='NEW'
            )
            db.session.add(new_order)
            
        db.session.commit()
        return redirect(url_for('orders.orders'))
    
    # fetch vendors for the dropdown
    vendors_list = Vendor.query.order_by(Vendor.name).all()
    # fetch distinct vehicle types dynamically
    vehicle_types_query = db.session.query(Order.vehicle_type).distinct().filter(Order.vehicle_type.isnot(None)).order_by(Order.vehicle_type).all()
    vehicle_types_list = [v[0] for v in vehicle_types_query if v[0].strip()]
    return render_template('order_new.html', vendors=vendors_list, vehicle_types=vehicle_types_list)

@bp.route('/kanban')
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

@bp.route('/api/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.json
    new_status = data.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        return {'success': True}
    return {'success': False}, 400
