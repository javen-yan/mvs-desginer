"""
Configuration settings for MVS Designer application.
"""
import os
from datetime import timedelta
from typing import Optional


class Config:
    """Base configuration class."""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mvs-designer-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://mvs_user:mvs_password@localhost:5432/mvs_designer'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
    
    # Directory configuration
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MODELS_FOLDER = os.path.join(BASE_DIR, 'static', 'models')
    TEMP_FOLDER = os.path.join(BASE_DIR, 'static', 'temp')
    
    # AWS S3 configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_USE_SSL = os.environ.get('S3_USE_SSL', 'true').lower() == 'true'
    
    # Meshroom configuration
    MESHROOM_PATH = os.environ.get('MESHROOM_PATH', '/opt/Meshroom')
    MESHROOM_CACHE_DIR = os.environ.get('MESHROOM_CACHE_DIR', '/tmp/meshroom_cache')
    
    # Quality presets
    QUALITY_PRESETS = {
        'low': {
            'describer_density': 'low',
            'max_input_points': 100000,
            'max_points': 500000,
            'estimated_time': '5-15分钟'
        },
        'medium': {
            'describer_density': 'normal',
            'max_input_points': 500000,
            'max_points': 2000000,
            'estimated_time': '15-45分钟'
        },
        'high': {
            'describer_density': 'high',
            'max_input_points': 1000000,
            'max_points': 5000000,
            'estimated_time': '45-120分钟'
        }
    }
    
    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration."""
        # Ensure required directories exist
        for folder in [Config.UPLOAD_FOLDER, Config.MODELS_FOLDER, Config.TEMP_FOLDER]:
            os.makedirs(folder, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://mvs_user:mvs_password@localhost:5432/mvs_designer_dev'


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://mvs_user:mvs_password@localhost:5432/mvs_designer'
    
    # Additional production settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 30
    }


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])