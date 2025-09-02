#!/usr/bin/env python3
"""
Database initialization script for MVS Designer.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from app import create_app
from app.models import db, User


def init_database():
    """Initialize the database with tables and sample data."""
    app = create_app()
    
    with app.app_context():
        print("Initializing database...")
        
        # Drop all tables (for development)
        db.drop_all()
        print("Dropped existing tables")
        
        # Create all tables
        db.create_all()
        print("Created database tables")
        
        # Create sample admin user
        admin_user = User(
            username='admin',
            email='admin@mvs-designer.com',
            password='admin123456'
        )
        
        db.session.add(admin_user)
        
        # Create sample regular user
        demo_user = User(
            username='demo',
            email='demo@mvs-designer.com',
            password='demo123456'
        )
        
        db.session.add(demo_user)
        
        try:
            db.session.commit()
            print("Created sample users:")
            print("  Admin: admin@mvs-designer.com / admin123456")
            print("  Demo:  demo@mvs-designer.com / demo123456")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to create sample users: {e}")
        
        print("Database initialization completed!")


if __name__ == '__main__':
    init_database()