from flask import Blueprint, render_template, request, redirect, url_for, current_app
from core.extensions import db
from core.models import Customer
from core.security import allowed_file
import os
import uuid

bp = Blueprint('crm', __name__)

@bp.route('/crm')
def crm():
    customers = Customer.query.order_by(Customer.id.desc()).all()
    return render_template('crm.html', customers=customers)

@bp.route('/api/customers/search')
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

@bp.route('/api/customers/new', methods=['POST'])
def api_customers_new():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    nik = request.form.get('nik')
    company = request.form.get('company')
    
    photo_filename = None
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename != '':
            # Security check: whitelist file extensions
            if allowed_file(photo.filename):
                ext = os.path.splitext(photo.filename)[1]
                photo_filename = f"{uuid.uuid4()}{ext}"
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                photo.save(os.path.join(upload_dir, photo_filename))
            else:
                return {'success': False, 'message': 'Invalid file format. Only images are allowed.'}, 400
            
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

@bp.route('/crm/<int:customer_id>')
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
