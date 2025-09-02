"""
Authentication and authorization utilities.
"""
import logging
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Optional, Dict, Any, Tuple

from flask import request, jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, \
    jwt_required, get_jwt_identity, get_jwt
from email_validator import validate_email, EmailNotValidError

from .models import db, User, UserSession


logger = logging.getLogger(__name__)
jwt = JWTManager()


def init_jwt(app):
    """Initialize JWT manager with the Flask app."""
    jwt.init_app(app)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token required'}), 401


class AuthService:
    """Service for handling user authentication and authorization."""
    
    @staticmethod
    def validate_registration_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate user registration data.
        
        Args:
            data: Registration data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ['username', 'email', 'password']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f'Missing required field: {field}'
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate username
        if len(username) < 3 or len(username) > 80:
            return False, 'Username must be between 3 and 80 characters'
        
        if not username.replace('_', '').replace('-', '').isalnum():
            return False, 'Username can only contain letters, numbers, hyphens, and underscores'
        
        # Validate email
        try:
            validate_email(email)
        except EmailNotValidError as e:
            return False, f'Invalid email address: {str(e)}'
        
        # Validate password
        if len(password) < 8:
            return False, 'Password must be at least 8 characters long'
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return False, 'Username already exists'
            else:
                return False, 'Email already registered'
        
        return True, None
    
    @staticmethod
    def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: User's username
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary containing registration result
        """
        try:
            # Create new user
            user = User(
                username=username.strip(),
                email=email.strip().lower(),
                password=password
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            
            return {
                'success': True,
                'user': user.to_dict(),
                'message': 'User registered successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to register user: {e}")
            return {
                'success': False,
                'error': 'Registration failed'
            }
    
    @staticmethod
    def authenticate_user(username_or_email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with username/email and password.
        
        Args:
            username_or_email: Username or email address
            password: User's password
            
        Returns:
            Dictionary containing authentication result
        """
        try:
            # Find user by username or email
            user = User.query.filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email.lower())
            ).first()
            
            if not user or not user.check_password(password):
                return {
                    'success': False,
                    'error': 'Invalid username/email or password'
                }
            
            if not user.is_active:
                return {
                    'success': False,
                    'error': 'Account is disabled'
                }
            
            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            # Create session record
            session_token = access_token
            expires_at = datetime.now(timezone.utc) + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            
            session = UserSession(
                user_id=user.id,
                session_token=session_token,
                expires_at=expires_at,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            db.session.add(session)
            db.session.commit()
            
            logger.info(f"User authenticated: {user.username}")
            
            return {
                'success': True,
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Authentication failed: {e}")
            return {
                'success': False,
                'error': 'Authentication failed'
            }
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """
        Get the current authenticated user.
        
        Returns:
            User object or None if not authenticated
        """
        try:
            user_id = get_jwt_identity()
            if user_id:
                return User.query.get(user_id)
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
        
        return None
    
    @staticmethod
    def logout_user() -> Dict[str, Any]:
        """
        Logout the current user by invalidating their session.
        
        Returns:
            Dictionary containing logout result
        """
        try:
            # Get current token
            token = get_jwt()
            jti = token.get('jti')  # JWT ID
            
            # Find and deactivate session
            session = UserSession.query.filter_by(
                session_token=jti,
                is_active=True
            ).first()
            
            if session:
                session.is_active = False
                db.session.commit()
            
            return {
                'success': True,
                'message': 'Logged out successfully'
            }
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return {
                'success': False,
                'error': 'Logout failed'
            }
    
    @staticmethod
    def refresh_token() -> Dict[str, Any]:
        """
        Refresh user's access token.
        
        Returns:
            Dictionary containing new access token
        """
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or not user.is_active:
                return {
                    'success': False,
                    'error': 'User not found or inactive'
                }
            
            # Generate new access token
            access_token = create_access_token(identity=str(user.id))
            
            return {
                'success': True,
                'access_token': access_token,
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return {
                'success': False,
                'error': 'Token refresh failed'
            }


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