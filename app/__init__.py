"""
MVS Designer Flask application factory.
"""
import logging
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from .config import get_config
from .models import db, bcrypt
from .auth import init_jwt
from .services import create_s3_service


def create_app() -> Flask:
    """
    Create and configure Flask application.
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize CORS
    CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    init_jwt(app)
    
    # Initialize database migration
    Migrate(app, db)
    
    # Initialize S3 service
    s3_service = create_s3_service(config_class)
    app.s3_service = s3_service
    
    # Initialize configuration
    config_class.init_app(app)
    
    # Register blueprints
    from .routes import main
    from .auth_routes import auth_bp
    app.register_blueprint(main)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Configure logging
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Failed to create database tables: {e}")
    
    return app