import os
import shutil
import sqlite3

os.environ['TMPDIR'] = '/tmp'
os.environ['SQLITE_TMPDIR'] = '/tmp'

basedir = os.path.abspath(os.path.dirname(__file__))


def get_database_uri():
    if os.environ.get('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    
    # Check if running in Vercel / Lambda / Read-only environment
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
                for search_root in ['/var/task', basedir, os.path.dirname(basedir)]:
                    if os.path.exists(search_root):
                        for root, dirs, files in os.walk(search_root):
                            for f in files:
                                if f == 'erp.db':
                                    found_src = os.path.join(root, f)
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
                    print(f"DEBUG: COPIED SEED DB {found_src} -> {tmp_db_path} ({len(db_data)} bytes)")
                else:
                    print("DEBUG: NO SEED DB FOUND, CREATING NEW BLANK DB")
                    conn = sqlite3.connect(tmp_db_path)
                    conn.close()
                    os.chmod(tmp_db_path, 0o777)

        except Exception as e:
            print("DEBUG ERROR SETUP SERVERLESS DB:", e)
            
        return 'sqlite:///' + tmp_db_path
    else:
        instance_dir = os.path.join(basedir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, 'erp.db')
        return 'sqlite:///' + db_path



from sqlalchemy.pool import NullPool

def sqlite_creator():
    basedir = os.path.abspath(os.path.dirname(__file__))
    is_serverless = (
        'VERCEL' in os.environ
        or 'VERCEL_ENV' in os.environ
        or 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        or '/var/task' in basedir
    )
    if is_serverless:
        return sqlite3.connect('/tmp/erp.db', timeout=30, check_same_thread=False)
    else:
        db_path = os.path.join(basedir, 'instance', 'erp.db')
        return sqlite3.connect(db_path, timeout=30, check_same_thread=False)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-jakarta-rent-bus-2026')
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'creator': sqlite_creator,
        'poolclass': NullPool
    }







