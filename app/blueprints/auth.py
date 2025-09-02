"""
Authentication blueprint.
"""
from flask import Blueprint, request, jsonify

from ..extensions import db
from ..models import User
from ..auth import AuthService
from ..middleware.auth import auth_required
from ..middleware.validation import validate_json
from ..logger import get_logger

logger = get_logger('auth')
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@validate_json(required_fields=['username', 'email', 'password'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        # Validate registration data
        is_valid, error_message = AuthService.validate_registration_data(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Register user
        result = AuthService.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'user': result['user']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
@validate_json(required_fields=['username', 'password'])
def login():
    """Authenticate user and return access token."""
    try:
        data = request.get_json()
        
        username_or_email = data.get('username') or data.get('email')
        password = data.get('password')
        
        if not username_or_email or not password:
            return jsonify({'error': 'Username/email and password are required'}), 400
        
        # Authenticate user
        result = AuthService.authenticate_user(username_or_email, password)
        
        if result['success']:
            return jsonify({
                'message': 'Login successful',
                'user': result['user'],
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'expires_in': result['expires_in']
            }), 200
        else:
            return jsonify({'error': result['error']}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
@auth_required
def logout():
    """Logout current user."""
    try:
        result = AuthService.logout_user()
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@auth_required
def refresh():
    """Refresh user's access token."""
    try:
        result = AuthService.refresh_token()
        
        if result['success']:
            return jsonify({
                'access_token': result['access_token'],
                'expires_in': result['expires_in']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    """Get current user's profile information."""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500


@auth_bp.route('/profile', methods=['PUT'])
@auth_required
@validate_json(optional_fields=['email', 'password'])
def update_profile():
    """Update current user's profile information."""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'email' in data:
            email = data['email'].strip().lower()
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                User.email == email,
                User.id != user.id
            ).first()
            
            if existing_user:
                return jsonify({'error': 'Email already registered'}), 400
            
            user.email = email
        
        if 'password' in data:
            if len(data['password']) < 8:
                return jsonify({'error': 'Password must be at least 8 characters long'}), 400
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update profile error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500
