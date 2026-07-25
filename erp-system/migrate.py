import os
import pandas as pd
from datetime import datetime
from flask import Flask
from core.extensions import db
from core.models import Customer, Vendor, Order, Payment

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def clean_date(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val).date()
    except:
        return None

def clean_float(val):
    if pd.isna(val):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

def clean_string(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None

def run_migration():
    print("Reading Excel file...")
    # Path is relative to the parent folder since Data Order.xlsx is there
    df = pd.read_excel('../Data Order.xlsx')
    
    with app.app_context():
        print("Creating database tables...")
        db.drop_all()
        db.create_all()
        
        print("Migrating Customers and Vendors...")
        customer_map = {}
        vendor_map = {}
        
        # Identify unique customers (by NAME or COMPANY) and vendors (by MITRA)
        for index, row in df.iterrows():
            # Handle Customer
            name = clean_string(row.get('NAME'))
            company = clean_string(row.get('COMPANY'))
            phone = clean_string(row.get('PHONE'))
            email = clean_string(row.get('EMAIL'))
            
            cust_key = f"{name}_{company}_{phone}"
            if cust_key not in customer_map and (name or company):
                cust = Customer(name=name, company=company, phone=phone, email=email)
                db.session.add(cust)
                customer_map[cust_key] = cust
            
            # Handle Vendor
            vendor_name = clean_string(row.get('MITRA'))
            if vendor_name and vendor_name not in vendor_map:
                vendor = Vendor(name=vendor_name)
                db.session.add(vendor)
                vendor_map[vendor_name] = vendor
                
        db.session.commit()
        
        print(f"Added {len(customer_map)} Customers and {len(vendor_map)} Vendors.")
        print("Migrating Orders...")
        
        orders_to_add = []
        for index, row in df.iterrows():
            name = clean_string(row.get('NAME'))
            company = clean_string(row.get('COMPANY'))
            phone = clean_string(row.get('PHONE'))
            cust_key = f"{name}_{company}_{phone}"
            cust = customer_map.get(cust_key)
            
            vendor_name = clean_string(row.get('MITRA'))
            vendor = vendor_map.get(vendor_name)
            
            total_sell = clean_float(row.get('TOTAL SELL'))
            if total_sell <= 0:
                continue # Skip invalid/empty orders
                
            order = Order(
                id_bitrix=clean_string(row.get('ID BITRIX')),
                book_date=clean_date(row.get('BOOK DATE')),
                departure_date=clean_date(row.get('DEPARTURE DATE')),
                return_date=clean_date(row.get('RETURN DATE')),
                origin=clean_string(row.get('ORIGIN')),
                destination=clean_string(row.get('DESTINATION')),
                vehicle_type=clean_string(row.get('TYPE')),
                marketing=clean_string(row.get('MARKETING')),
                qty_sell=clean_float(row.get('QTY SELL')),
                sell_price=clean_float(row.get('SELL PRICE')),
                total_sell=total_sell,
                qty_buy=clean_float(row.get('QTY BUY')),
                buy_price=clean_float(row.get('BUY PRICE')),
                total_buy=clean_float(row.get('TOTAL BUY')),
                status=clean_string(row.get('STATUS')),
                customer_id=cust.id if cust else None,
                vendor_id=vendor.id if vendor else None
            )
            
            db.session.add(order)
            
            # Flush to get order.id for payments
            db.session.flush()
            
            # Handle DP Payment
            amount_dp = clean_float(row.get('AMOUNT DP'))
            if amount_dp > 0:
                dp = Payment(order_id=order.id, payment_type='DP', amount=amount_dp, payment_date=clean_date(row.get('DATE DP')))
                db.session.add(dp)
                
            # Handle FULL Payment
            amount_full = clean_float(row.get('AMOUNT FULL'))
            if amount_full > 0:
                full = Payment(order_id=order.id, payment_type='FULL', amount=amount_full, payment_date=clean_date(row.get('DATE FULL')))
                db.session.add(full)
                
        db.session.commit()
        print("Migration complete!")

if __name__ == '__main__':
    run_migration()
