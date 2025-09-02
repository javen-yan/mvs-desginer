"""
Flask extensions initialization.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()


def init_jwt_callbacks(jwt_manager):
    """Initialize JWT callbacks."""
    
    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        from flask import jsonify
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        from flask import jsonify
        return jsonify({'error': 'Authorization token required'}), 401
    
    @jwt_manager.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({'error': 'Fresh token required'}), 401


def init_extensions(app):
    """Initialize all extensions with the Flask app."""
    # Initialize JWT callbacks
    init_jwt_callbacks(jwt)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
