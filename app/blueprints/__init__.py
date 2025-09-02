"""
Blueprint registration for the application.
"""
from flask import Flask


def register_blueprints(app: Flask):
    """
    Register all blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Import blueprints
    from .main import main_bp
    from .auth import auth_bp
    from .api import api_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
