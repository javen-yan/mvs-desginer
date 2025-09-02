"""
MVS Designer Flask application factory.
Uses the new modular architecture.
"""
from .factory import create_app    

# Re-export the create_app function from factory
__all__ = ['create_app']