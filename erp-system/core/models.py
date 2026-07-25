from core.extensions import db

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    nik = db.Column(db.String(50), nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    orders = db.relationship('Order', backref='vendor', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    id_bitrix = db.Column(db.String(50), nullable=True, index=True)
    book_date = db.Column(db.Date, nullable=True, index=True)
    departure_date = db.Column(db.Date, nullable=True, index=True)
    return_date = db.Column(db.Date, nullable=True, index=True)
    origin = db.Column(db.String(100), nullable=True)
    destination = db.Column(db.String(100), nullable=True, index=True)
    vehicle_type = db.Column(db.String(50), nullable=True)
    marketing = db.Column(db.String(100), nullable=True, index=True)
    
    qty_sell = db.Column(db.Float, default=0)
    sell_price = db.Column(db.Float, default=0)
    total_sell = db.Column(db.Float, default=0)
    
    qty_buy = db.Column(db.Float, default=0)
    buy_price = db.Column(db.Float, default=0)
    total_buy = db.Column(db.Float, default=0)
    
    status = db.Column(db.String(50), nullable=True, index=True)
    
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True, index=True)
    
    payments = db.relationship('Payment', backref='order', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_type = db.Column(db.String(50), nullable=False) # 'DP' or 'FULL'
    amount = db.Column(db.Float, default=0)
    payment_date = db.Column(db.Date, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
