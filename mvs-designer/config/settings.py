"""
MVS Designer 配置文件
"""
import os

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mvs-designer-secret-key'
    
    # Meshroom配置
    MESHROOM_PATH = os.environ.get('MESHROOM_PATH') or 'meshroom_batch'
    MESHROOM_TIMEOUT = int(os.environ.get('MESHROOM_TIMEOUT', 3600))  # 1小时超时
    
    # 文件配置
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
    
    # 目录配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MODELS_FOLDER = os.path.join(BASE_DIR, 'static', 'models')
    TEMP_FOLDER = os.path.join(BASE_DIR, 'static', 'temp')
    
    # 重建质量配置
    QUALITY_PRESETS = {
        'low': {
            'preset': 'draft',
            'max_images': 50,
            'downscale': 2,
            'description': '快速重建，质量较低'
        },
        'medium': {
            'preset': 'default',
            'max_images': 100,
            'downscale': 1,
            'description': '平衡质量和速度'
        },
        'high': {
            'preset': 'detailed',
            'max_images': 200,
            'downscale': 1,
            'description': '高质量重建，耗时较长'
        }
    }
    
    # GPU配置
    USE_GPU = os.environ.get('USE_GPU', 'True').lower() == 'true'
    CUDA_VISIBLE_DEVICES = os.environ.get('CUDA_VISIBLE_DEVICES', '0')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境的安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}