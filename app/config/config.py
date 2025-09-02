import os
from datetime import timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
    
@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str
    pool_pre_ping: bool = True
    pool_recycle: int = 300
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False


@dataclass
class JWTConfig:
    """JWT配置"""
    secret_key: str
    access_token_expires: timedelta = timedelta(hours=24)
    refresh_token_expires: timedelta = timedelta(days=30)
    algorithm: str = 'HS256'


@dataclass
class S3Config:
    """S3配置"""
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    region: str = 'us-east-1'
    bucket_name: Optional[str] = None
    use_ssl: bool = True


@dataclass
class FileConfig:
    """文件上传配置"""
    max_content_length: int = 500 * 1024 * 1024  # 500MB
    allowed_extensions: set = None
    upload_folder: str = None
    models_folder: str = None
    temp_folder: str = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}


@dataclass
class MeshroomConfig:
    """Meshroom服务配置"""
    path: str = 'meshroom_batch'
    cache_dir: str = '/tmp/meshroom_cache'
    quality_presets: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.quality_presets is None:
            self.quality_presets = {
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


@dataclass
class LogConfig:
    """日志配置"""
    level: str = 'INFO'
    log_file: str = 'app.log'
    log_dir: str = 'logs'
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True
    console_format: str = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    file_format: str = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'


class Config:
    """统一的配置类 - 动态根据环境变量获取配置"""

    def __init__(self):
        load_dotenv()
    
    @classmethod
    def get_secret_key(cls):
        """获取 SECRET_KEY"""
        return os.environ.get('SECRET_KEY') or 'mvs-designer-secret-key-change-in-production'
    
    @classmethod
    def get_host(cls):
        """获取 HOST"""
        return os.environ.get('HOST', '0.0.0.0')
    
    @classmethod
    def get_port(cls):
        """获取 PORT"""
        return int(os.environ.get('PORT', 5000))
    
    @classmethod
    def get_debug(cls):
        """获取 DEBUG"""
        return os.environ.get('DEBUG', 'false').lower() == 'true'
    
    @classmethod
    def get_database_config(cls):
        """获取数据库配置"""
        return DatabaseConfig(
            url=os.environ.get('DATABASE_URL') or 
                'postgresql://mvs_user:mvs_password@localhost:5432/mvs_designer',
            pool_pre_ping=os.environ.get('DB_POOL_PRE_PING', 'true').lower() == 'true',
            pool_recycle=int(os.environ.get('DB_POOL_RECYCLE', 300)),
            pool_size=int(os.environ.get('DB_POOL_SIZE', 10)),
            max_overflow=int(os.environ.get('DB_MAX_OVERFLOW', 20)),
            echo=os.environ.get('DB_ECHO', 'false').lower() == 'true'
        )
    
    @classmethod
    def get_jwt_config(cls):
        """获取 JWT 配置"""
        return JWTConfig(
            secret_key=os.environ.get('JWT_SECRET_KEY') or cls.get_secret_key(),
            access_token_expires=timedelta(hours=int(os.environ.get('JWT_ACCESS_EXPIRES_HOURS', 24))),
            refresh_token_expires=timedelta(days=int(os.environ.get('JWT_REFRESH_EXPIRES_DAYS', 30))),
            algorithm=os.environ.get('JWT_ALGORITHM', 'HS256')
        )
    
    @classmethod
    def get_s3_config(cls):
        """获取 S3 配置"""
        return S3Config(
            access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region=os.environ.get('AWS_REGION', 'us-east-1'),
            bucket_name=os.environ.get('S3_BUCKET_NAME'),
            use_ssl=os.environ.get('S3_USE_SSL', 'true').lower() == 'true'
        )
    
    @classmethod
    def get_file_config(cls):
        """获取文件配置"""
        return FileConfig(
            max_content_length=int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)),
            upload_folder=os.environ.get('UPLOAD_FOLDER') or 
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads'),
            models_folder=os.environ.get('MODELS_FOLDER') or 
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'models'),
            temp_folder=os.environ.get('TEMP_FOLDER') or 
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'temp')
        )
    
    @classmethod
    def get_meshroom_config(cls):
        """获取 Meshroom 配置"""
        return MeshroomConfig(
            path=os.environ.get('MESHROOM_PATH', 'meshroom_batch'),
            cache_dir=os.environ.get('MESHROOM_CACHE_DIR', '/tmp/meshroom_cache')
        )
    
    @classmethod
    def get_log_config(cls):
        """获取日志配置"""
        return LogConfig(
            level=os.environ.get('LOG_LEVEL', 'INFO'),
            log_file=os.environ.get('LOG_FILE', 'app.log'),
            log_dir=os.environ.get('LOG_DIR', 'logs'),
            max_file_size=int(os.environ.get('LOG_MAX_SIZE', 10 * 1024 * 1024)),
            backup_count=int(os.environ.get('LOG_BACKUP_COUNT', 5)),
            enable_console=os.environ.get('LOG_CONSOLE', 'true').lower() == 'true',
            enable_file=os.environ.get('LOG_FILE_ENABLE', 'true').lower() == 'true',
            console_format=os.environ.get('LOG_CONSOLE_FORMAT', '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'),
            file_format=os.environ.get('LOG_FILE_FORMAT', '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        )
    
    # 属性访问器，用于向后兼容
    @property
    def SECRET_KEY(self):
        return self.get_secret_key()
    
    @property
    def HOST(self):
        return self.get_host()
    
    @property
    def PORT(self):
        return self.get_port()
    
    @property
    def DEBUG(self):
        return self.get_debug()
    
    @property
    def DATABASE(self):
        return self.get_database_config()
    
    @property
    def JWT(self):
        return self.get_jwt_config()
    
    @property
    def S3(self):
        return self.get_s3_config()
    
    @property
    def FILE(self):
        return self.get_file_config()
    
    @property
    def MESHROOM(self):
        return self.get_meshroom_config()
    
    @property
    def LOG(self):
        return self.get_log_config()
    
    # Flask-SQLAlchemy配置
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return self.DATABASE.url
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        return {
            'pool_pre_ping': self.DATABASE.pool_pre_ping,
            'pool_recycle': self.DATABASE.pool_recycle,
            'pool_size': self.DATABASE.pool_size,
            'max_overflow': self.DATABASE.max_overflow,
            'echo': self.DATABASE.echo
        }
    
    # JWT配置 (Flask-JWT-Extended)
    @property
    def JWT_SECRET_KEY(self):
        return self.JWT.secret_key
    
    @property
    def JWT_ACCESS_TOKEN_EXPIRES(self):
        return self.JWT.access_token_expires
    
    @property
    def JWT_REFRESH_TOKEN_EXPIRES(self):
        return self.JWT.refresh_token_expires
    
    @property
    def JWT_ALGORITHM(self):
        return self.JWT.algorithm
    
    # 文件上传配置
    @property
    def MAX_CONTENT_LENGTH(self):
        return self.FILE.max_content_length
    
    @property
    def ALLOWED_EXTENSIONS(self):
        return self.FILE.allowed_extensions
    
    @property
    def UPLOAD_FOLDER(self):
        return self.FILE.upload_folder
    
    @property
    def MODELS_FOLDER(self):
        return self.FILE.models_folder
    
    @property
    def TEMP_FOLDER(self):
        return self.FILE.temp_folder
    
    # AWS S3配置
    @property
    def AWS_ACCESS_KEY_ID(self):
        return self.S3.access_key_id
    
    @property
    def AWS_SECRET_ACCESS_KEY(self):
        return self.S3.secret_access_key
    
    @property
    def AWS_REGION(self):
        return self.S3.region
    
    @property
    def S3_BUCKET_NAME(self):
        return self.S3.bucket_name
    
    @property
    def S3_USE_SSL(self):
        return self.S3.use_ssl
    
    # Meshroom配置
    @property
    def MESHROOM_PATH(self):
        return self.MESHROOM.path
    
    @property
    def MESHROOM_CACHE_DIR(self):
        return self.MESHROOM.cache_dir
    
    @property
    def QUALITY_PRESETS(self):
        return self.MESHROOM.quality_presets
    
    def init_app(self, app):
        """初始化应用特定配置"""
        # 确保必要的目录存在
        for folder in [self.UPLOAD_FOLDER, self.MODELS_FOLDER, self.TEMP_FOLDER]:
            os.makedirs(folder, exist_ok=True)
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 创建配置实例来访问属性
        config = cls()
        
        # 验证必需设置
        if not config.SECRET_KEY or config.SECRET_KEY == 'mvs-designer-secret-key-change-in-production':
            warnings.append("使用默认 SECRET_KEY - 生产环境请修改")
        
        if not config.S3.access_key_id or not config.S3.secret_access_key or not config.S3.bucket_name:
            warnings.append("S3配置不完整 - S3功能将被禁用")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
