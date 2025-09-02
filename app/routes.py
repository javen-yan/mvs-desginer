"""
Main application routes with authentication and database integration.
"""
import os
import uuid
import shutil
import logging
from typing import Optional, Dict, Any

from flask import Blueprint, request, jsonify, current_app, send_file, render_template
from werkzeug.utils import secure_filename
from PIL import Image

from .models import db, User, ReconstructionJob, JobImage
from .auth import auth_required, optional_auth, AuthService
from .meshroom_service import MeshroomService
from .utils import allowed_file, validate_images


logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
@optional_auth
def index():
    """主页面 - 返回Web界面或API信息"""
    if request.headers.get('Accept', '').startswith('application/json'):
        user = AuthService.get_current_user()
        
        endpoints = {
            'auth': {
                'register': '/api/auth/register',
                'login': '/api/auth/login',
                'logout': '/api/auth/logout',
                'profile': '/api/auth/profile'
            },
            'jobs': {
                'upload': '/api/upload',
                'reconstruct': '/api/reconstruct',
                'status': '/api/status/<job_id>',
                'download': '/api/download/<job_id>',
                'list': '/api/jobs',
                'preview': '/api/preview/<job_id>'
            }
        }
        
        response_data = {
            'service': 'MVS Designer',
            'description': '基于Meshroom的多维度照片3D建模服务',
            'version': '2.0.0',
            'endpoints': endpoints,
            'features': [
                'User Authentication',
                'PostgreSQL Database',
                'S3 Object Storage',
                '3D Model Preview',
                'Multi-quality Reconstruction'
            ]
        }
        
        if user:
            response_data['user'] = user.to_dict()
        
        return jsonify(response_data)
    else:
        return render_template('index.html')

@main.route('/api/upload', methods=['POST'])
@auth_required
def upload_images():
    """上传多角度照片"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        if 'images' not in request.files:
            return jsonify({'error': '没有找到图片文件'}), 400
        
        files = request.files.getlist('images')
        if not files or len(files) < 3:
            return jsonify({'error': '至少需要3张不同角度的照片'}), 400
        
        # 获取任务信息
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        # 生成唯一的任务ID
        job_id = str(uuid.uuid4())
        
        # 创建数据库记录
        reconstruction_job = ReconstructionJob(
            user_id=user.id,
            job_id=job_id,
            title=title if title else f'3D重建任务 - {job_id[:8]}',
            description=description
        )
        
        db.session.add(reconstruction_job)
        db.session.flush()  # 获取数据库ID
        
        # 创建本地文件夹
        job_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        os.makedirs(job_folder, exist_ok=True)
        
        uploaded_files = []
        job_images = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(job_folder, filename)
                
                # 保存本地文件
                file.save(filepath)
                
                # 获取图片信息
                try:
                    with Image.open(filepath) as img:
                        width, height = img.size
                except Exception:
                    width, height = None, None
                
                # 创建图片记录
                job_image = JobImage(
                    job_id=reconstruction_job.id,
                    filename=filename,
                    original_filename=file.filename,
                    file_size=os.path.getsize(filepath)
                )
                job_image.file_path = filepath
                job_image.image_width = width
                job_image.image_height = height
                
                # 上传到S3（如果配置了）
                if current_app.s3_service:
                    s3_key = f"jobs/{job_id}/images/{filename}"
                    
                    # 重新打开文件进行S3上传
                    file.stream.seek(0)
                    upload_result = current_app.s3_service.upload_file(
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
                        logger.info(f"Uploaded image to S3: {s3_key}")
                
                job_images.append(job_image)
                uploaded_files.append(filename)
        
        if len(uploaded_files) < 3:
            shutil.rmtree(job_folder, ignore_errors=True)
            db.session.rollback()
            return jsonify({'error': '有效图片文件少于3张'}), 400
        
        # 验证图片
        validation_result = validate_images(job_folder)
        if not validation_result['valid']:
            shutil.rmtree(job_folder, ignore_errors=True)
            db.session.rollback()
            return jsonify({'error': f'图片验证失败: {validation_result["message"]}'}), 400
        
        # 保存所有图片记录
        for job_image in job_images:
            db.session.add(job_image)
        
        # 更新任务文件夹路径
        reconstruction_job.input_folder = job_folder
        
        db.session.commit()
        
        logger.info(f"User {user.username} uploaded {len(uploaded_files)} images for job {job_id}")
        
        return jsonify({
            'job_id': job_id,
            'uploaded_files': uploaded_files,
            'images': [img.to_dict() for img in job_images],
            'message': f'成功上传{len(uploaded_files)}张照片',
            'next_step': f'使用job_id调用/api/reconstruct进行3D重建'
        })
        
    except Exception as e:
        db.session.rollback()
        if 'job_folder' in locals():
            shutil.rmtree(job_folder, ignore_errors=True)
        logger.error(f"Upload failed for user {user.username if 'user' in locals() else 'unknown'}: {e}")
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@main.route('/api/reconstruct', methods=['POST'])
@auth_required
def reconstruct_3d():
    """开始3D重建任务"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        data = request.get_json()
        if not data or 'job_id' not in data:
            return jsonify({'error': '缺少job_id参数'}), 400
        
        job_id = data['job_id']
        
        # 从数据库查找任务
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id  # 确保用户只能操作自己的任务
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        if reconstruction_job.status not in ['pending', 'failed']:
            return jsonify({'error': f'任务状态为{reconstruction_job.status}，无法重新开始'}), 400
        
        # 获取重建参数
        quality = data.get('quality', 'medium')  # low, medium, high
        preset = data.get('preset', 'default')   # default, fast, detailed
        
        # 验证参数
        if quality not in current_app.config['QUALITY_PRESETS']:
            return jsonify({'error': f'无效的质量参数: {quality}'}), 400
        
        # 更新任务参数
        reconstruction_job.quality = quality
        reconstruction_job.preset = preset
        reconstruction_job.update_status('running', 0.0)
        
        # 创建Meshroom服务实例
        meshroom_service = MeshroomService(current_app.config)
        
        # 启动异步重建任务
        result = meshroom_service.start_reconstruction(
            job_id, 
            reconstruction_job.input_folder, 
            quality, 
            preset
        )
        
        if result['success']:
            # 更新数据库状态
            reconstruction_job.update_status('running', 5.0)
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
            # 更新失败状态
            reconstruction_job.update_status('failed', error_message=result['error'])
            db.session.commit()
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reconstruction start failed: {e}")
        return jsonify({'error': f'重建启动失败: {str(e)}'}), 500

@main.route('/api/status/<job_id>', methods=['GET'])
@auth_required
def check_status(job_id):
    """检查3D重建任务状态"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 从数据库查找任务
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id  # 确保用户只能查看自己的任务
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        # 获取Meshroom状态
        meshroom_service = MeshroomService(current_app.config)
        meshroom_status = meshroom_service.get_reconstruction_status(job_id)
        
        # 更新数据库状态
        if meshroom_status.get('status') != reconstruction_job.status:
            reconstruction_job.update_status(
                status=meshroom_status.get('status', reconstruction_job.status),
                progress=meshroom_status.get('progress', reconstruction_job.progress),
                error_message=meshroom_status.get('error')
            )
            
            # 如果完成了，保存模型文件路径
            if meshroom_status.get('status') == 'completed' and meshroom_status.get('output_file'):
                reconstruction_job.model_file_path = meshroom_status['output_file']
                reconstruction_job.output_folder = os.path.dirname(meshroom_status['output_file'])
                
                # 上传模型到S3（如果配置了）
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
                        reconstruction_job.s3_key_prefix = f"jobs/{job_id}"
                        logger.info(f"Uploaded 3D model to S3: {s3_key}")
            
            db.session.commit()
        
        # 返回完整状态信息
        status_data = reconstruction_job.to_dict()
        status_data.update({
            'meshroom_status': meshroom_status,
            'images': [img.to_dict() for img in reconstruction_job.images]
        })
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': f'状态查询失败: {str(e)}'}), 500


@main.route('/api/download/<job_id>', methods=['GET'])
@auth_required
def download_model(job_id):
    """下载生成的3D模型"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 从数据库查找任务
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id  # 确保用户只能下载自己的模型
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        if reconstruction_job.status != 'completed':
            return jsonify({'error': '任务尚未完成，无法下载'}), 400
        
        # 优先从S3下载
        if current_app.s3_service and reconstruction_job.s3_key_prefix:
            s3_key = f"{reconstruction_job.s3_key_prefix}/models/model.obj"
            download_url = current_app.s3_service.get_object_url(s3_key, expires_in=3600)
            
            if download_url:
                return jsonify({
                    'download_url': download_url,
                    'expires_in': 3600,
                    'filename': f'model_{job_id}.obj'
                })
        
        # 本地文件下载
        if reconstruction_job.model_file_path and os.path.exists(reconstruction_job.model_file_path):
            return send_file(
                reconstruction_job.model_file_path, 
                as_attachment=True, 
                download_name=f'model_{job_id}.obj'
            )
        
        # 备用路径
        models_folder = current_app.config['MODELS_FOLDER']
        model_file = os.path.join(models_folder, f'{job_id}.obj')
        
        if os.path.exists(model_file):
            return send_file(model_file, as_attachment=True, download_name=f'model_{job_id}.obj')
        
        return jsonify({'error': '3D模型文件不存在'}), 404
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({'error': f'下载失败: {str(e)}'}), 500


@main.route('/api/jobs', methods=['GET'])
@auth_required
def list_jobs():
    """列出用户的所有任务"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        
        # 构建查询
        query = ReconstructionJob.query.filter_by(user_id=user.id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # 按创建时间倒序排列
        query = query.order_by(ReconstructionJob.created_at.desc())
        
        # 分页
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
        
        return jsonify({
            'jobs': jobs_data,
            'total': jobs.total,
            'pages': jobs.pages,
            'current_page': page,
            'per_page': per_page,
            'status_filter': status_filter
        })
        
    except Exception as e:
        logger.error(f"List jobs failed: {e}")
        return jsonify({'error': f'获取任务列表失败: {str(e)}'}), 500


@main.route('/api/preview/<job_id>', methods=['GET'])
@auth_required
def preview_model(job_id):
    """预览3D模型"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 从数据库查找任务
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        if reconstruction_job.status != 'completed':
            return jsonify({'error': '任务尚未完成，无法预览'}), 400
        
        preview_data = {
            'job_id': job_id,
            'title': reconstruction_job.title,
            'status': reconstruction_job.status,
            'quality': reconstruction_job.quality,
            'created_at': reconstruction_job.created_at.isoformat(),
            'completed_at': reconstruction_job.completed_at.isoformat() if reconstruction_job.completed_at else None
        }
        
        # 添加模型文件信息
        if current_app.s3_service and reconstruction_job.s3_key_prefix:
            # S3预览URL
            s3_key = f"{reconstruction_job.s3_key_prefix}/models/model.obj"
            preview_url = current_app.s3_service.get_object_url(s3_key, expires_in=7200)  # 2小时
            
            if preview_url:
                preview_data['model_url'] = preview_url
                preview_data['model_source'] = 's3'
        
        elif reconstruction_job.model_file_path and os.path.exists(reconstruction_job.model_file_path):
            # 本地文件预览
            preview_data['model_path'] = f'/api/download/{job_id}'
            preview_data['model_source'] = 'local'
        
        # 添加输入图片信息
        preview_data['input_images'] = []
        for img in reconstruction_job.images:
            img_data = img.to_dict()
            
            # 添加图片预览URL
            if current_app.s3_service and img.s3_key:
                img_preview_url = current_app.s3_service.get_object_url(img.s3_key, expires_in=3600)
                img_data['preview_url'] = img_preview_url
            elif img.file_path and os.path.exists(img.file_path):
                img_data['preview_path'] = f'/api/image/{job_id}/{img.filename}'
            
            preview_data['input_images'].append(img_data)
        
        return jsonify(preview_data)
        
    except Exception as e:
        logger.error(f"Model preview failed: {e}")
        return jsonify({'error': f'模型预览失败: {str(e)}'}), 500


@main.route('/api/image/<job_id>/<filename>', methods=['GET'])
@auth_required
def serve_image(job_id, filename):
    """提供图片文件服务"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 验证用户权限
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        # 查找图片记录
        job_image = JobImage.query.filter_by(
            job_id=reconstruction_job.id,
            filename=filename
        ).first()
        
        if not job_image:
            return jsonify({'error': '图片不存在'}), 404
        
        # 优先从S3获取
        if current_app.s3_service and job_image.s3_key:
            image_url = current_app.s3_service.get_object_url(job_image.s3_key, expires_in=3600)
            if image_url:
                return jsonify({'image_url': image_url, 'expires_in': 3600})
        
        # 本地文件服务
        if job_image.file_path and os.path.exists(job_image.file_path):
            return send_file(job_image.file_path)
        
        return jsonify({'error': '图片文件不存在'}), 404
        
    except Exception as e:
        logger.error(f"Image serving failed: {e}")
        return jsonify({'error': f'图片服务失败: {str(e)}'}), 500


@main.route('/api/jobs/<job_id>', methods=['GET'])
@auth_required
def get_job_detail(job_id):
    """获取任务详细信息"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 从数据库查找任务
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        job_data = reconstruction_job.to_dict()
        job_data['images'] = [img.to_dict() for img in reconstruction_job.images]
        
        # 添加预览信息
        if reconstruction_job.status == 'completed':
            job_data['preview_available'] = True
            job_data['preview_url'] = f'/api/preview/{job_id}'
        
        return jsonify(job_data)
        
    except Exception as e:
        logger.error(f"Get job detail failed: {e}")
        return jsonify({'error': f'获取任务详情失败: {str(e)}'}), 500


@main.route('/api/jobs/<job_id>', methods=['PUT'])
@auth_required
def update_job(job_id):
    """更新任务信息"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 从数据库查找任务
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        # 更新允许的字段
        if 'title' in data:
            reconstruction_job.title = data['title'].strip()
        
        if 'description' in data:
            reconstruction_job.description = data['description'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': '任务信息更新成功',
            'job': reconstruction_job.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update job failed: {e}")
        return jsonify({'error': f'更新任务失败: {str(e)}'}), 500


@main.route('/api/jobs/<job_id>', methods=['DELETE'])
@auth_required
def delete_job(job_id):
    """删除任务及相关文件"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 从数据库查找任务
        reconstruction_job = ReconstructionJob.query.filter_by(
            job_id=job_id,
            user_id=user.id
        ).first()
        
        if not reconstruction_job:
            return jsonify({'error': '任务不存在或无权限访问'}), 404
        
        # 删除S3文件
        if current_app.s3_service and reconstruction_job.s3_key_prefix:
            s3_objects = current_app.s3_service.list_objects(prefix=reconstruction_job.s3_key_prefix)
            if s3_objects['success'] and s3_objects['objects']:
                keys_to_delete = [obj['key'] for obj in s3_objects['objects']]
                delete_result = current_app.s3_service.delete_objects(keys_to_delete)
                logger.info(f"Deleted {delete_result.get('deleted_count', 0)} S3 objects for job {job_id}")
        
        # 删除本地文件
        if reconstruction_job.input_folder and os.path.exists(reconstruction_job.input_folder):
            shutil.rmtree(reconstruction_job.input_folder, ignore_errors=True)
        
        if reconstruction_job.output_folder and os.path.exists(reconstruction_job.output_folder):
            shutil.rmtree(reconstruction_job.output_folder, ignore_errors=True)
        
        # 删除数据库记录（级联删除图片记录）
        db.session.delete(reconstruction_job)
        db.session.commit()
        
        logger.info(f"User {user.username} deleted job {job_id}")
        
        return jsonify({'message': '任务删除成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete job failed: {e}")
        return jsonify({'error': f'删除任务失败: {str(e)}'}), 500


@main.route('/api/stats', methods=['GET'])
@auth_required
def get_user_stats():
    """获取用户统计信息"""
    try:
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 统计用户任务
        total_jobs = ReconstructionJob.query.filter_by(user_id=user.id).count()
        completed_jobs = ReconstructionJob.query.filter_by(user_id=user.id, status='completed').count()
        running_jobs = ReconstructionJob.query.filter_by(user_id=user.id, status='running').count()
        failed_jobs = ReconstructionJob.query.filter_by(user_id=user.id, status='failed').count()
        
        # 统计图片数量
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