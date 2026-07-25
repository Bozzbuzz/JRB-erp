import os
import shutil
import sqlite3

basedir = os.path.abspath(os.path.dirname(__file__))

def get_database_uri():
    if os.environ.get('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    
    # Check if running in Vercel / Lambda / Read-only environment
    is_vercel = (
        os.environ.get('VERCEL') == '1'
        or 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        or not os.access(basedir, os.W_OK)
    )
    
    if is_vercel:
        tmp_db_path = '/tmp/erp.db'
        if not os.path.exists(tmp_db_path) or os.path.getsize(tmp_db_path) == 0:
            os.makedirs('/tmp', exist_ok=True)
            candidates = [
                os.path.join(basedir, 'instance', 'erp.db'),
                os.path.join(os.path.dirname(basedir), 'instance', 'erp.db'),
                '/var/task/erp-system/instance/erp.db',
                '/var/task/instance/erp.db'
            ]
            copied = False
            for src in candidates:
                if os.path.exists(src) and os.path.getsize(src) > 0:
                    try:
                        shutil.copyfile(src, tmp_db_path)
                        copied = True
                        print(f"Successfully copied DB from {src} to {tmp_db_path}")
                        break
                    except Exception as e:
                        print(f"Failed to copy {src}: {e}")
            if not copied:
                print("No candidate DB found, creating fresh SQLite DB in /tmp")
                conn = sqlite3.connect(tmp_db_path)
                conn.close()
        return 'sqlite:///' + tmp_db_path
    else:
        instance_dir = os.path.join(basedir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, 'erp.db')
        return 'sqlite:///' + db_path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-jakarta-rent-bus-2026')
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False




