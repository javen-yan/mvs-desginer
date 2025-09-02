"""
Database models for MVS Designer application.
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """User model for authentication and task ownership."""
    
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    jobs = relationship('ReconstructionJob', back_populates='user', lazy='dynamic')
    
    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.set_password(password)
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> dict:
        """Convert user to dictionary representation."""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'job_count': self.jobs.count()
        }
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'


class ReconstructionJob(db.Model):
    """Model for 3D reconstruction jobs."""
    
    __tablename__ = 'reconstruction_jobs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    job_id = Column(String(36), unique=True, nullable=False, index=True)  # External job ID
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='pending', nullable=False, index=True)
    quality = Column(String(10), default='medium', nullable=False)
    preset = Column(String(20), default='default', nullable=False)
    progress = Column(Float, default=0.0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # File paths
    input_folder = Column(String(500), nullable=True)
    output_folder = Column(String(500), nullable=True)
    model_file_path = Column(String(500), nullable=True)
    s3_bucket = Column(String(100), nullable=True)
    s3_key_prefix = Column(String(200), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', back_populates='jobs')
    images = relationship('JobImage', back_populates='job', cascade='all, delete-orphan')
    
    def __init__(self, user_id: str, job_id: str, title: str = None, description: str = None):
        self.user_id = user_id
        self.job_id = job_id
        self.title = title
        self.description = description
    
    def update_status(self, status: str, progress: float = None, error_message: str = None) -> None:
        """Update job status and related fields."""
        self.status = status
        if progress is not None:
            self.progress = progress
        if error_message is not None:
            self.error_message = error_message
        
        if status == 'running' and self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        elif status in ['completed', 'failed']:
            self.completed_at = datetime.now(timezone.utc)
    
    def to_dict(self, include_user: bool = False) -> dict:
        """Convert job to dictionary representation."""
        result = {
            'id': str(self.id),
            'job_id': self.job_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'quality': self.quality,
            'preset': self.preset,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'image_count': len(self.images)
        }
        
        if include_user and self.user:
            result['user'] = {
                'id': str(self.user.id),
                'username': self.user.username
            }
        
        return result
    
    def __repr__(self) -> str:
        return f'<ReconstructionJob {self.job_id} - {self.status}>'


class JobImage(db.Model):
    """Model for images associated with reconstruction jobs."""
    
    __tablename__ = 'job_images'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('reconstruction_jobs.id'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=True)  # Local path
    s3_key = Column(String(500), nullable=True)     # S3 object key
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    job = relationship('ReconstructionJob', back_populates='images')
    
    def __init__(self, job_id: str, filename: str, original_filename: str, file_size: int):
        self.job_id = job_id
        self.filename = filename
        self.original_filename = original_filename
        self.file_size = file_size
    
    def to_dict(self) -> dict:
        """Convert image to dictionary representation."""
        return {
            'id': str(self.id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'uploaded_at': self.uploaded_at.isoformat(),
            's3_key': self.s3_key
        }
    
    def __repr__(self) -> str:
        return f'<JobImage {self.filename}>'


class UserSession(db.Model):
    """Model for tracking user sessions."""
    
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    session_token = Column(Text, unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User')
    
    def __init__(self, user_id: str, session_token: str, expires_at: datetime, ip_address: str = None, user_agent: str = None):
        self.user_id = user_id
        self.session_token = session_token
        self.expires_at = expires_at
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert session to dictionary representation."""
        return {
            'id': str(self.id),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
    
    def __repr__(self) -> str:
        return f'<UserSession {self.user.username if self.user else "Unknown"}>'