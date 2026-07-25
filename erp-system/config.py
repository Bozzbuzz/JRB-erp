import os
import shutil

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'erp.db')

if os.environ.get('VERCEL') == '1':
    tmp_db_path = '/tmp/erp.db'
    if not os.path.exists(tmp_db_path):
        if os.path.exists(db_path):
            shutil.copyfile(db_path, tmp_db_path)
        else:
            # Touch /tmp/erp.db or create empty file
            os.makedirs('/tmp', exist_ok=True)
    db_uri = 'sqlite:///' + tmp_db_path
else:
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_uri = 'sqlite:///' + db_path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-jakarta-rent-bus-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', db_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

