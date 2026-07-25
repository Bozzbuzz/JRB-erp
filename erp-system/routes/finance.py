from flask import Blueprint, render_template
from core.extensions import db
from core.models import Order, Payment, Vendor
from sqlalchemy import func

bp = Blueprint('finance', __name__)

@bp.route('/finance')
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
        dp = sum(p.amount for p in order.payments if p.payment_type == 'DP')
        full = sum(p.amount for p in order.payments if p.payment_type == 'FULL')
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

@bp.route('/vendors')
def vendors():
    vendors_list = Vendor.query.all()
    # Fetch recent orders that represent a buy from a vendor
    buy_history = Order.query.filter(Order.vendor_id.isnot(None)).order_by(Order.book_date.desc()).limit(10).all()
    
    return render_template('vendors.html', vendors=vendors_list, buy_history=buy_history)
