import os
import sys

os.environ['TMPDIR'] = '/tmp'
os.environ['SQLITE_TMPDIR'] = '/tmp'

# Ensure erp-system directory is in Python path for Vercel/local execution
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env'))
except ImportError:
    pass



from flask import Flask
from config import Config
from core.extensions import db, csrf
from core.models import Order
from routes import dashboard_bp, orders_bp, crm_bp, finance_bp, analytics_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("DB init exception:", e)


    
    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(analytics_bp)
    
    # Register context processors
    @app.context_processor
    def inject_global_dates():
        first_order = Order.query.order_by(Order.book_date.asc()).first()
        last_order = Order.query.order_by(Order.book_date.desc()).first()
        return dict(
            db_first_date=first_order.book_date if first_order and first_order.book_date else "2020-01-01",
            db_last_date=last_order.book_date if last_order and last_order.book_date else ""
        )
        
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    app.run(debug=debug, port=port)
