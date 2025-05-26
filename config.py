import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set for Flask application")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 0,
        'pool_timeout': 30,
        'pool_recycle': 1800
    }
    # Outras configurações como DEBUG, TESTING, etc.
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')