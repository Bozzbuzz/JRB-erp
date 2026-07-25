import os
import sys
import shutil
import sqlite3

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

def ensure_database_file():
    basedir = os.path.abspath(os.path.dirname(__file__))
    is_serverless = (
        'VERCEL' in os.environ
        or 'VERCEL_ENV' in os.environ
        or 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        or '/var/task' in basedir
    )
    if is_serverless:
        tmp_db_path = '/tmp/erp.db'
        try:
            os.makedirs('/tmp', exist_ok=True)
            if not os.path.exists(tmp_db_path) or os.path.getsize(tmp_db_path) == 0:
                found_src = None
                for sroot in ['/var/task', basedir, os.path.dirname(basedir)]:
                    if os.path.exists(sroot):
                        for root, dirs, files in os.walk(sroot):
                            if 'erp.db' in files and os.path.join(root, 'erp.db') != tmp_db_path:
                                found_src = os.path.join(root, 'erp.db')
                                break
                        if found_src:
                            break
                    if found_src:
                        break
                if found_src:
                    with open(found_src, 'rb') as f_in:
                        db_data = f_in.read()
                    with open(tmp_db_path, 'wb') as f_out:
                        f_out.write(db_data)
                    os.chmod(tmp_db_path, 0o777)
                else:
                    conn = sqlite3.connect(tmp_db_path)
                    conn.close()
                    os.chmod(tmp_db_path, 0o777)

        except Exception as e:
            print("ensure_database_file exception:", e)

def create_app(config_class=Config):
    ensure_database_file()
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    @app.before_request
    def before_request_db_check():
        ensure_database_file()

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
        try:
            first_order = Order.query.order_by(Order.book_date.asc()).first()
            last_order = Order.query.order_by(Order.book_date.desc()).first()
            return dict(
                db_first_date=first_order.book_date if first_order and first_order.book_date else "2020-01-01",
                db_last_date=last_order.book_date if last_order and last_order.book_date else ""
            )
        except Exception as e:
            print("inject_global_dates exception:", e)
            return dict(db_first_date="2020-01-01", db_last_date="")


    @app.route('/test-db')
    def test_db():
        import sqlite3
        db_path = '/tmp/erp.db'
        results = {
            'exists': os.path.exists(db_path),
            'size': os.path.getsize(db_path) if os.path.exists(db_path) else -1,
            'var_task_files': []
        }
        try:
            for root, dirs, files in os.walk('/var/task'):
                for f in files:
                    if f.endswith('.db') or f == 'app.py':
                        results['var_task_files'].append(os.path.join(root, f))
        except Exception as e:
            results['walk_error'] = str(e)
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            conn.close()
            results['tables'] = tables
        except Exception as e:
            results['sqlite_error'] = str(e)
        return results

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    app.run(debug=debug, port=port)
