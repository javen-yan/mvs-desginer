"""
API blueprint for job management.
"""
import os
from flask import Blueprint, request, jsonify, current_app, send_file

from ..extensions import db
from ..models import User, ReconstructionJob, JobImage
from ..auth import AuthService
from ..middleware.auth import auth_required
from ..middleware.validation import validate_json, validate_file_upload
from ..services.job_service import JobService
from ..services.meshroom_service import MeshroomService
from ..logger import get_logger

logger = get_logger('api')
api_bp = Blueprint('api', __name__)


@api_bp.route('/upload', methods=['POST'])
@auth_required
@validate_file_upload(
    allowed_extensions={'png', 'jpg', 'jpeg', 'tiff', 'bmp'},
    max_size=50 * 1024 * 1024,  # 50MB
    min_files=3
)
def upload_images():
    """上传多角度照片"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Get job information
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        # Create job service
        job_service = JobService(current_app.config, current_app.s3_service)
        
        # Create job
        job_result = job_service.create_job(user, title, description)
        if not job_result['success']:
            return jsonify({'error': job_result['error']}), 500
        
        job_id = job_result['job_id']
        
        # Upload images
        files = request.files.getlist('images')
        upload_result = job_service.upload_images(
            job_id, user, files, title, description
        )
        
        if not upload_result['success']:
            return jsonify({'error': upload_result['error']}), 400
        
        logger.info(f"User {user.username} uploaded {len(upload_result['uploaded_files'])} images for job {job_id}")
        
        return jsonify({
            'job_id': job_id,
            'uploaded_files': upload_result['uploaded_files'],
            'images': upload_result['images'],
            'message': upload_result['message'],
            'next_step': f'使用job_id调用/api/reconstruct进行3D重建'
        })
        
    except Exception as e:
        logger.error(f"Upload failed for user {user.username if 'user' in locals() else 'unknown'}: {e}")
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@api_bp.route('/reconstruct', methods=['POST'])
@auth_required
@validate_json(required_fields=['job_id'])
def reconstruct_3d():
    """开始3D重建任务"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        data = request.get_json()
        job_id = data['job_id']
        
        # Get job
        job_service = JobService(current_app.config, current_app.s3_service)
        job_result = job_service.get_job(job_id, user)
        
        if not job_result['success']:
            return jsonify({'error': job_result['error']}), 404
        
        job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if job.status not in ['pending', 'failed']:
            return jsonify({'error': f'任务状态为{job.status}，无法重新开始'}), 400
        
        # Get reconstruction parameters
        quality = data.get('quality', 'medium')
        preset = data.get('preset', 'default')
        
        # Validate parameters
        if quality not in current_app.config['QUALITY_PRESETS']:
            return jsonify({'error': f'无效的质量参数: {quality}'}), 400
        
        # Update job parameters
        job.quality = quality
        job.preset = preset
        job.update_status('running', 0.0)
        
        # Create Meshroom service
        meshroom_service = MeshroomService(current_app.config)
        
        # Start reconstruction
        result = meshroom_service.start_reconstruction(
            job_id, 
            job.input_folder, 
            quality, 
            preset
        )
        
        if result['success']:
            job.update_status('running', 5.0)
            db.session.commit()
            
            estimated_time = current_app.config['QUALITY_PRESETS'][quality]['estimated_time']
            
            logger.info(f"User {user.username} started reconstruction for job {job_id}")
            
            return jsonify({
                'job_id': job_id,
                'status': 'running',
                'message': '3D重建任务已启动',
                'quality': quality,
                'preset': preset,
                'estimated_time': estimated_time,
                'check_status': f'/api/status/{job_id}'
            })
        else:
            job.update_status('failed', error_message=result['error'])
            db.session.commit()
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reconstruction start failed: {e}")
        return jsonify({'error': f'重建启动失败: {str(e)}'}), 500


@api_bp.route('/status/<job_id>', methods=['GET'])
@auth_required
def check_status(job_id):
    """检查3D重建任务状态"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Get job
        job_service = JobService(current_app.config, current_app.s3_service)
        job_result = job_service.get_job(job_id, user)
        
        if not job_result['success']:
            return jsonify({'error': job_result['error']}), 404
        
        job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        # Get Meshroom status
        meshroom_service = MeshroomService(current_app.config)
        meshroom_status = meshroom_service.get_reconstruction_status(job_id)
        
        # Update database status
        if meshroom_status.get('status') != job.status:
            job.update_status(
                status=meshroom_status.get('status', job.status),
                progress=meshroom_status.get('progress', job.progress),
                error_message=meshroom_status.get('error')
            )
            
            # If completed, save model file path
            if meshroom_status.get('status') == 'completed' and meshroom_status.get('output_file'):
                job.model_file_path = meshroom_status['output_file']
                job.output_folder = os.path.dirname(meshroom_status['output_file'])
                
                # Upload model to S3 if configured
                if current_app.s3_service and os.path.exists(meshroom_status['output_file']):
                    s3_key = f"jobs/{job_id}/models/model.obj"
                    upload_result = current_app.s3_service.upload_local_file(
                        local_path=meshroom_status['output_file'],
                        key=s3_key,
                        content_type='application/octet-stream',
                        metadata={
                            'job_id': job_id,
                            'user_id': str(user.id),
                            'file_type': '3d_model'
                        }
                    )
                    
                    if upload_result['success']:
                        job.s3_key_prefix = f"jobs/{job_id}"
                        logger.info(f"Uploaded 3D model to S3: {s3_key}")
            
            db.session.commit()
        
        # Return complete status information
        status_data = job.to_dict()
        status_data.update({
            'meshroom_status': meshroom_status,
            'images': [img.to_dict() for img in job.images]
        })
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': f'状态查询失败: {str(e)}'}), 500


@api_bp.route('/download/<job_id>', methods=['GET'])
@auth_required
def download_model(job_id):
    """下载生成的3D模型"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Get job
        job_service = JobService(current_app.config, current_app.s3_service)
        job_result = job_service.get_job(job_id, user)
        
        if not job_result['success']:
            return jsonify({'error': job_result['error']}), 404
        
        job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if job.status != 'completed':
            return jsonify({'error': '任务尚未完成，无法下载'}), 400
        
        # Try S3 download first
        if current_app.s3_service and job.s3_key_prefix:
            s3_key = f"{job.s3_key_prefix}/models/model.obj"
            download_url = current_app.s3_service.get_object_url(s3_key, expires_in=3600)
            
            if download_url:
                return jsonify({
                    'download_url': download_url,
                    'expires_in': 3600,
                    'filename': f'model_{job_id}.obj'
                })
        
        # Local file download
        if job.model_file_path and os.path.exists(job.model_file_path):
            return send_file(
                job.model_file_path, 
                as_attachment=True, 
                download_name=f'model_{job_id}.obj'
            )
        
        # Fallback path
        models_folder = current_app.config['MODELS_FOLDER']
        model_file = os.path.join(models_folder, f'{job_id}.obj')
        
        if os.path.exists(model_file):
            return send_file(model_file, as_attachment=True, download_name=f'model_{job_id}.obj')
        
        return jsonify({'error': '3D模型文件不存在'}), 404
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({'error': f'下载失败: {str(e)}'}), 500


@api_bp.route('/jobs', methods=['GET'])
@auth_required
def list_jobs():
    """列出用户的所有任务"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        
        # Use job service
        job_service = JobService(current_app.config, current_app.s3_service)
        result = job_service.list_jobs(user, page, per_page, status_filter)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'jobs': result['jobs'],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page'],
            'per_page': result['per_page'],
            'status_filter': status_filter
        })
        
    except Exception as e:
        logger.error(f"List jobs failed: {e}")
        return jsonify({'error': f'获取任务列表失败: {str(e)}'}), 500


@api_bp.route('/jobs/<job_id>', methods=['GET'])
@auth_required
def get_job_detail(job_id):
    """获取任务详细信息"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Use job service
        job_service = JobService(current_app.config, current_app.s3_service)
        result = job_service.get_job(job_id, user)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 404
        
        job_data = result['job']
        
        # Add preview information
        if job_data['status'] == 'completed':
            job_data['preview_available'] = True
            job_data['preview_url'] = f'/api/preview/{job_id}'
        
        return jsonify(job_data)
        
    except Exception as e:
        logger.error(f"Get job detail failed: {e}")
        return jsonify({'error': f'获取任务详情失败: {str(e)}'}), 500


@api_bp.route('/jobs/<job_id>', methods=['PUT'])
@auth_required
@validate_json(optional_fields=['title', 'description'])
def update_job(job_id):
    """更新任务信息"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Get job
        job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if not job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            job.title = data['title'].strip()
        
        if 'description' in data:
            job.description = data['description'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': '任务信息更新成功',
            'job': job.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update job failed: {e}")
        return jsonify({'error': f'更新任务失败: {str(e)}'}), 500


@api_bp.route('/jobs/<job_id>', methods=['DELETE'])
@auth_required
def delete_job(job_id):
    """删除任务及相关文件"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Use job service
        job_service = JobService(current_app.config, current_app.s3_service)
        result = job_service.delete_job(job_id, user)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 404
        
        logger.info(f"User {user.username} deleted job {job_id}")
        
        return jsonify({'message': result['message']})
        
    except Exception as e:
        logger.error(f"Delete job failed: {e}")
        return jsonify({'error': f'删除任务失败: {str(e)}'}), 500


@api_bp.route('/stats', methods=['GET'])
@auth_required
def get_user_stats():
    """获取用户统计信息"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Count user jobs
        total_jobs = ReconstructionJob.query.filter_by(user_id=user.id).count()
        completed_jobs = ReconstructionJob.query.filter_by(user_id=user.id, status='completed').count()
        running_jobs = ReconstructionJob.query.filter_by(user_id=user.id, status='running').count()
        failed_jobs = ReconstructionJob.query.filter_by(user_id=user.id, status='failed').count()
        
        # Count images
        total_images = db.session.query(JobImage).join(ReconstructionJob).filter(
            ReconstructionJob.user_id == user.id
        ).count()
        
        stats = {
            'user': user.to_dict(),
            'jobs': {
                'total': total_jobs,
                'completed': completed_jobs,
                'running': running_jobs,
                'failed': failed_jobs,
                'pending': total_jobs - completed_jobs - running_jobs - failed_jobs
            },
            'images': {
                'total': total_images
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Get user stats failed: {e}")
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500
