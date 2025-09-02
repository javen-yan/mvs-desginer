#!/usr/bin/env python3
"""
Setup script for MVS Designer application.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def check_postgresql():
    """Check if PostgreSQL is available."""
    try:
        result = subprocess.run(['pg_config', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ PostgreSQL detected: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠ PostgreSQL not found. Please install PostgreSQL:")
    print("  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib libpq-dev")
    print("  CentOS/RHEL:   sudo yum install postgresql postgresql-server postgresql-devel")
    print("  macOS:         brew install postgresql")
    return False


def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, cwd=project_root)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def setup_environment():
    """Setup environment configuration."""
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            content = src.read()
            # Generate a random secret key
            import secrets
            secret_key = secrets.token_urlsafe(32)
            jwt_key = secrets.token_urlsafe(32)
            
            content = content.replace('your-secret-key-here', secret_key)
            content = content.replace('your-jwt-secret-key-here', jwt_key)
            
            dst.write(content)
        
        print("✓ Created .env file with generated secret keys")
        print("⚠ Please edit .env file to configure your database and S3 settings")
    elif env_file.exists():
        print("✓ .env file already exists")
    else:
        print("⚠ No .env.example file found")


def setup_database():
    """Setup database."""
    print("Setting up database...")
    
    # Check if we can connect to the database
    try:
        from app import create_app
        from app.models import db
        
        app = create_app()
        with app.app_context():
            # Test database connection
            db.engine.execute('SELECT 1')
            print("✓ Database connection successful")
            
            # Create tables
            db.create_all()
            print("✓ Database tables created")
            
            return True
            
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        print("Please ensure PostgreSQL is running and configured correctly")
        return False


def create_admin_user():
    """Create initial admin user."""
    try:
        from app import create_app
        from app.models import db, User
        
        app = create_app()
        with app.app_context():
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print("✓ Admin user already exists")
                return True
            
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@mvs-designer.com',
                password='admin123456'
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✓ Created admin user:")
            print("  Username: admin")
            print("  Email: admin@mvs-designer.com")
            print("  Password: admin123456")
            print("  ⚠ Please change the admin password after first login!")
            
            return True
            
    except Exception as e:
        print(f"✗ Failed to create admin user: {e}")
        return False


def check_meshroom():
    """Check if Meshroom is available."""
    meshroom_path = os.environ.get('MESHROOM_PATH', 'meshroom_batch')
    
    try:
        result = subprocess.run([meshroom_path, '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ Meshroom found at: {meshroom_path}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("⚠ Meshroom not found. Please install Meshroom:")
    print("  Download from: https://github.com/alicevision/meshroom/releases")
    print("  Or set MESHROOM_PATH environment variable to point to meshroom_batch executable")
    return False


def main():
    """Main setup function."""
    print("MVS Designer Setup")
    print("==================")
    
    success = True
    
    # Check requirements
    check_python_version()
    
    if not check_postgresql():
        success = False
    
    if not install_dependencies():
        success = False
    
    setup_environment()
    
    if not setup_database():
        success = False
    
    if not create_admin_user():
        success = False
    
    check_meshroom()  # Non-critical
    
    print("\n" + "=" * 50)
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file to configure your settings")
        print("2. Start the application: python app.py")
        print("3. Open http://localhost:5000 in your browser")
    else:
        print("✗ Setup completed with errors")
        print("Please fix the issues above and run setup again")
    
    print("=" * 50)


if __name__ == '__main__':
    main()