"""
Authentication middleware and decorators.
"""
import logging
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from ..models import User
from ..auth import AuthService

logger = logging.getLogger(__name__)


def auth_required(f):
    """
    Decorator to require authentication for a route.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    Decorator for optional authentication.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    @jwt_required(optional=True)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin privileges.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403
        
        # Check if user is admin (you can implement this based on your user model)
        if not getattr(user, 'is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(max_requests=100, window=3600):
    """
    Rate limiting decorator.
    
    Args:
        max_requests: Maximum requests per window
        window: Time window in seconds
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple rate limiting implementation
            # In production, use Redis or similar
            client_ip = request.remote_addr
            # TODO: Implement actual rate limiting logic
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
