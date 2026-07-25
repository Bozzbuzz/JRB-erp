import os
import shutil

basedir = os.path.abspath(os.path.dirname(__file__))

if os.environ.get('VERCEL') == '1':
    tmp_db_path = '/tmp/erp.db'
    if not os.path.exists(tmp_db_path):
        os.makedirs('/tmp', exist_ok=True)
        candidates = [
            os.path.join(basedir, 'instance', 'erp.db'),
            os.path.join(os.path.dirname(basedir), 'instance', 'erp.db'),
            '/var/task/erp-system/instance/erp.db',
            '/var/task/instance/erp.db'
        ]
        copied = False
        for src in candidates:
            if os.path.exists(src):
                try:
                    shutil.copyfile(src, tmp_db_path)
                    copied = True
                    break
                except Exception as e:
                    pass
        if not copied:
            with open(tmp_db_path, 'w') as f:
                pass
    db_uri = 'sqlite:///' + tmp_db_path
else:
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'erp.db')
    db_uri = 'sqlite:///' + db_path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-jakarta-rent-bus-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', db_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


