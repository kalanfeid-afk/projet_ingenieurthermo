import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration de base."""
    SECRET_KEY                     = os.environ.get('SECRET_KEY', 'processinsight-secret-2026')
    SQLALCHEMY_DATABASE_URI        = os.environ.get('DATABASE_URL',
                                        f"sqlite:///{os.path.join(BASE_DIR, 'processinsight.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME     = timedelta(hours=2)
    MAX_CONTENT_LENGTH             = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig
}