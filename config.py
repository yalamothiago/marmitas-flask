# config.py
import os

class Config:
    SECRET_KEY = '91edcba69af85051f6e4169f1092ce9e445a63705d0036cc' # SEU VALOR AQUI, COMO STRING LITERAL
    # Remover ou comentar a linha `if not SECRET_KEY:` se ela ainda estiver lá

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
    WTF_CSRF_ENABLED = True # Garanta que isso seja True
    WTF_CSRF_CHECK_DEFAULT = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')