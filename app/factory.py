"""
Application factory with improved structure and error handling.
"""
import os
from typing import Optional
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from .config import Config
from .extensions import db, bcrypt, jwt
from .services import ServiceManager
from .blueprints import register_blueprints
from .logger import setup_logging, get_logger


# Setup logging first
config = Config()
logger = setup_logging(config.LOG)


class AppFactory:
    """Factory for creating Flask applications."""
    
    def __init__(self):
        self.app: Optional[Flask] = None
        self.service_manager: Optional[ServiceManager] = None
    
    def create_app(self, env: str = 'development') -> Flask:
        """
        Create and configure Flask application.
        
        Args:
            config_name: Configuration environment name
            
        Returns:
            Configured Flask application
        """
        try:
            # Create Flask app
            self.app = Flask(
                __name__,
                template_folder='../templates',
                static_folder='../static'
            )
            
            # Load configuration
            self.app.config.from_object(config)
            
            # Validate configuration
            validation_result = Config.validate()
            if not validation_result['valid']:
                logger.error(f"Configuration validation failed: {validation_result['errors']}")
                raise ValueError("Invalid configuration")
            
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    logger.warning(f"Configuration warning: {warning}")
            
            # Initialize extensions
            self._init_extensions()
            
            # Initialize services
            self._init_services()
            
            # Register blueprints
            register_blueprints(self.app)
            
            # Initialize configuration
            config.init_app(self.app)
            
            # Create database tables
            self._init_database()
            
            logger.info(f"Application created successfully with configuration")
            return self.app
            
        except Exception as e:
            logger.error(f"Failed to create application: {e}")
            if self.app:
                self._cleanup()
            raise
    
    def _init_extensions(self):
        """Initialize Flask extensions."""
        try:
            # Initialize CORS
            CORS(
                self.app,
                origins="*",
                allow_headers=["Content-Type", "Authorization"],
                supports_credentials=True
            )
            
            # Initialize extensions using the new system
            from .extensions import init_extensions
            init_extensions(self.app)
            
            # Initialize database migration
            Migrate(self.app, db)
            
            logger.info("Extensions initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize extensions: {e}")
            raise
    
    def _init_services(self):
        """Initialize application services."""
        try:
            self.service_manager = ServiceManager(self.app)
            self.service_manager.init_services()
            
            # Attach services to app for easy access
            self.app.s3_service = self.service_manager.get_service('s3')
            self.app.meshroom_service = self.service_manager.get_service('meshroom')
            
            logger.info("Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with self.app.app_context():
                db.create_all()
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def _cleanup(self):
        """Cleanup resources on failure."""
        try:
            if self.service_manager:
                self.service_manager.cleanup()
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


def create_app():
    """Create Flask application instance for Flask-Migrate."""
    factory = AppFactory()
    return factory.create_app()
