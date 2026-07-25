import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Key configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-jakarta-rent-bus-2026')
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'instance', 'erp.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
