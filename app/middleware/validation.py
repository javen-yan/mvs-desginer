"""
Request validation middleware.
"""
import logging
from functools import wraps
from flask import request, jsonify
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)


def validate_json(required_fields=None, optional_fields=None):
    """
    Validate JSON request data.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body must contain JSON data'}), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            
            # Validate field types and values
            for field, value in data.items():
                if field in (required_fields or []) and not value:
                    return jsonify({
                        'error': f'Field {field} cannot be empty'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_file_upload(allowed_extensions=None, max_size=None, min_files=1, max_files=None):
    """
    Validate file upload request.
    
    Args:
        allowed_extensions: Set of allowed file extensions
        max_size: Maximum file size in bytes
        min_files: Minimum number of files
        max_files: Maximum number of files
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'images' not in request.files:
                return jsonify({'error': 'No files uploaded'}), 400
            
            files = request.files.getlist('images')
            
            # Check file count
            if len(files) < min_files:
                return jsonify({
                    'error': f'At least {min_files} files required'
                }), 400
            
            if max_files and len(files) > max_files:
                return jsonify({
                    'error': f'Maximum {max_files} files allowed'
                }), 400
            
            # Validate each file
            valid_files = []
            for file in files:
                if not file or not file.filename:
                    continue
                
                # Check file extension
                if allowed_extensions:
                    if not file.filename.lower().endswith(tuple(f'.{ext}' for ext in allowed_extensions)):
                        return jsonify({
                            'error': f'File {file.filename} has invalid extension'
                        }), 400
                
                # Check file size
                if max_size:
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    file.seek(0)  # Reset to beginning
                    
                    if file_size > max_size:
                        return jsonify({
                            'error': f'File {file.filename} is too large'
                        }), 400
                
                valid_files.append(file)
            
            if len(valid_files) < min_files:
                return jsonify({
                    'error': f'At least {min_files} valid files required'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_content_type(allowed_types=None):
    """
    Validate request content type.
    
    Args:
        allowed_types: List of allowed content types
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if allowed_types:
                content_type = request.content_type
                if not any(content_type.startswith(allowed_type) for allowed_type in allowed_types):
                    return jsonify({
                        'error': f'Content type {content_type} not allowed'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
