"""
Job management service.
"""
import os
import uuid
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..extensions import db
from ..models import User, ReconstructionJob, JobImage
from ..utils import allowed_file, validate_images
from .s3_service import S3Service
from ..logger import get_logger

logger = get_logger('job_service')


class JobService:
    """Service for managing reconstruction jobs."""
    
    def __init__(self, config: dict, s3_service: Optional[S3Service] = None):
        self.config = config
        self.s3_service = s3_service
    
    def create_job(self, user: User, title: str = None, description: str = None) -> Dict[str, Any]:
        """
        Create a new reconstruction job.
        
        Args:
            user: User creating the job
            title: Job title
            description: Job description
            
        Returns:
            Job creation result
        """
        try:
            job_id = str(uuid.uuid4())
            
            # Create job record
            job = ReconstructionJob(
                user_id=user.id,
                job_id=job_id,
                title=title or f'3D重建任务 - {job_id[:8]}',
                description=description
            )
            
            db.session.add(job)
            db.session.flush()  # Get database ID
            
            # Create local folder
            job_folder = os.path.join(self.config['UPLOAD_FOLDER'], job_id)
            os.makedirs(job_folder, exist_ok=True)
            job.input_folder = job_folder
            
            db.session.commit()
            
            logger.info(f"Job {job_id} created for user {user.username}")
            
            return {
                'success': True,
                'job': job.to_dict(),
                'job_id': job_id
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_images(self, job_id: str, user: User, files: List, 
                     title: str = None, description: str = None) -> Dict[str, Any]:
        """
        Upload images for a job.
        
        Args:
            job_id: Job ID
            user: User uploading images
            files: List of uploaded files
            title: Job title
            description: Job description
            
        Returns:
            Upload result
        """
        try:
            # Find job
            job = ReconstructionJob.query.filter_by(
                job_id=job_id,
                user_id=user.id
            ).first()
            
            if not job:
                return {
                    'success': False,
                    'error': 'Job not found or access denied'
                }
            
            if job.status not in ['pending', 'failed']:
                return {
                    'success': False,
                    'error': f'Cannot upload images for job with status: {job.status}'
                }
            
            # Update job info if provided
            if title:
                job.title = title
            if description:
                job.description = description
            
            # Validate files
            if not files or len(files) < 3:
                return {
                    'success': False,
                    'error': 'At least 3 images are required'
                }
            
            # Process uploaded files
            uploaded_files = []
            job_images = []
            
            for file in files:
                if file and allowed_file(file.filename):
                    filename = file.filename
                    filepath = os.path.join(job.input_folder, filename)
                    
                    # Save local file
                    file.save(filepath)
                    
                    # Get image info
                    try:
                        from PIL import Image
                        with Image.open(filepath) as img:
                            width, height = img.size
                    except Exception:
                        width, height = None, None
                    
                    # Create image record
                    job_image = JobImage(
                        job_id=job.id,
                        filename=filename,
                        original_filename=file.filename,
                        file_size=os.path.getsize(filepath)
                    )
                    job_image.file_path = filepath
                    job_image.image_width = width
                    job_image.image_height = height
                    
                    # Upload to S3 if available
                    if self.s3_service:
                        s3_key = f"jobs/{job_id}/images/{filename}"
                        file.stream.seek(0)
                        upload_result = self.s3_service.upload_file(
                            file_obj=file,
                            key=s3_key,
                            content_type=file.content_type,
                            metadata={
                                'job_id': job_id,
                                'user_id': str(user.id),
                                'original_filename': file.filename
                            }
                        )
                        
                        if upload_result['success']:
                            job_image.s3_key = s3_key
                    
                    job_images.append(job_image)
                    uploaded_files.append(filename)
            
            if len(uploaded_files) < 3:
                shutil.rmtree(job.input_folder, ignore_errors=True)
                return {
                    'success': False,
                    'error': 'Less than 3 valid images uploaded'
                }
            
            # Validate images
            validation_result = validate_images(job.input_folder)
            if not validation_result['valid']:
                shutil.rmtree(job.input_folder, ignore_errors=True)
                return {
                    'success': False,
                    'error': f'Image validation failed: {validation_result["message"]}'
                }
            
            # Save image records
            for job_image in job_images:
                db.session.add(job_image)
            
            db.session.commit()
            
            logger.info(f"Uploaded {len(uploaded_files)} images for job {job_id}")
            
            return {
                'success': True,
                'job_id': job_id,
                'uploaded_files': uploaded_files,
                'images': [img.to_dict() for img in job_images],
                'message': f'Successfully uploaded {len(uploaded_files)} images'
            }
            
        except Exception as e:
            db.session.rollback()
            if 'job' in locals() and job and hasattr(job, 'input_folder'):
                shutil.rmtree(job.input_folder, ignore_errors=True)
            logger.error(f"Image upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_job(self, job_id: str, user: User) -> Dict[str, Any]:
        """
        Get job details.
        
        Args:
            job_id: Job ID
            user: User requesting job
            
        Returns:
            Job details
        """
        try:
            job = ReconstructionJob.query.filter_by(
                job_id=job_id,
                user_id=user.id
            ).first()
            
            if not job:
                return {
                    'success': False,
                    'error': 'Job not found or access denied'
                }
            
            job_data = job.to_dict()
            job_data['images'] = [img.to_dict() for img in job.images]
            
            return {
                'success': True,
                'job': job_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_jobs(self, user: User, page: int = 1, per_page: int = 20, 
                  status_filter: str = None) -> Dict[str, Any]:
        """
        List user's jobs.
        
        Args:
            user: User requesting jobs
            page: Page number
            per_page: Items per page
            status_filter: Filter by status
            
        Returns:
            Jobs list
        """
        try:
            query = ReconstructionJob.query.filter_by(user_id=user.id)
            
            if status_filter:
                query = query.filter_by(status=status_filter)
            
            query = query.order_by(ReconstructionJob.created_at.desc())
            
            jobs = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            jobs_data = []
            for job in jobs.items:
                job_dict = job.to_dict()
                job_dict['images'] = [img.to_dict() for img in job.images]
                jobs_data.append(job_dict)
            
            return {
                'success': True,
                'jobs': jobs_data,
                'total': jobs.total,
                'pages': jobs.pages,
                'current_page': page,
                'per_page': per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_job(self, job_id: str, user: User) -> Dict[str, Any]:
        """
        Delete a job and its files.
        
        Args:
            job_id: Job ID
            user: User deleting job
            
        Returns:
            Deletion result
        """
        try:
            job = ReconstructionJob.query.filter_by(
                job_id=job_id,
                user_id=user.id
            ).first()
            
            if not job:
                return {
                    'success': False,
                    'error': 'Job not found or access denied'
                }
            
            # Delete S3 files
            if self.s3_service and job.s3_key_prefix:
                s3_objects = self.s3_service.list_objects(prefix=job.s3_key_prefix)
                if s3_objects['success'] and s3_objects['objects']:
                    keys_to_delete = [obj['key'] for obj in s3_objects['objects']]
                    self.s3_service.delete_objects(keys_to_delete)
            
            # Delete local files
            if job.input_folder and os.path.exists(job.input_folder):
                shutil.rmtree(job.input_folder, ignore_errors=True)
            
            if job.output_folder and os.path.exists(job.output_folder):
                shutil.rmtree(job.output_folder, ignore_errors=True)
            
            # Delete database record
            db.session.delete(job)
            db.session.commit()
            
            logger.info(f"Job {job_id} deleted by user {user.username}")
            
            return {
                'success': True,
                'message': 'Job deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
