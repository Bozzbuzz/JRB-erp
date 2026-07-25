from flask import Blueprint, render_template, request
from core.extensions import db
from core.models import Order
from datetime import date, datetime
import calendar
from sqlalchemy import func

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def dashboard():
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
    total_fleet = 173  # static total fleet
    
    # Orders not fully paid (usually we want all pending, not just this month)
    pending_orders = Order.query.filter(Order.status != 'COMPLETE').limit(4).all()
    
    # Recent orders (filtered by date)
    recent_orders = base_query.order_by(Order.book_date.desc()).limit(5).all()
    
    try:
        sd = datetime.strptime(start_date, '%Y-%m-%d')
        ed = datetime.strptime(end_date, '%Y-%m-%d')
        date_label = f"{sd.strftime('%b %d, %Y')} - {ed.strftime('%b %d, %Y')}"
    except ValueError:
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
