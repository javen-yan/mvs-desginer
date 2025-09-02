from flask import Blueprint, request, jsonify, current_app, send_file, render_template
import os
import uuid
import shutil
from werkzeug.utils import secure_filename
from .meshroom_service import MeshroomService
from .utils import allowed_file, validate_images

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    """主页面 - 可以返回Web界面或API信息"""
    if request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({
            'service': 'MVS Designer',
            'description': '基于Meshroom的多维度照片3D建模服务',
            'version': '1.0.0',
            'endpoints': {
                'upload': '/api/upload',
                'reconstruct': '/api/reconstruct',
                'status': '/api/status/<job_id>',
                'download': '/api/download/<job_id>'
            }
        })
    else:
        return render_template('index.html')

@main.route('/api/upload', methods=['POST'])
def upload_images():
    """上传多角度照片"""
    try:
        if 'images' not in request.files:
            return jsonify({'error': '没有找到图片文件'}), 400
        
        files = request.files.getlist('images')
        if not files or len(files) < 3:
            return jsonify({'error': '至少需要3张不同角度的照片'}), 400
        
        # 生成唯一的任务ID
        job_id = str(uuid.uuid4())
        job_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        os.makedirs(job_folder, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(job_folder, filename)
                file.save(filepath)
                uploaded_files.append(filename)
        
        if len(uploaded_files) < 3:
            shutil.rmtree(job_folder)
            return jsonify({'error': '有效图片文件少于3张'}), 400
        
        # 验证图片
        validation_result = validate_images(job_folder)
        if not validation_result['valid']:
            shutil.rmtree(job_folder)
            return jsonify({'error': f'图片验证失败: {validation_result["message"]}'}), 400
        
        return jsonify({
            'job_id': job_id,
            'uploaded_files': uploaded_files,
            'message': f'成功上传{len(uploaded_files)}张照片',
            'next_step': f'使用job_id调用/api/reconstruct进行3D重建'
        })
        
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@main.route('/api/reconstruct', methods=['POST'])
def reconstruct_3d():
    """开始3D重建任务"""
    try:
        data = request.get_json()
        if not data or 'job_id' not in data:
            return jsonify({'error': '缺少job_id参数'}), 400
        
        job_id = data['job_id']
        job_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        
        if not os.path.exists(job_folder):
            return jsonify({'error': '任务不存在'}), 404
        
        # 获取重建参数
        quality = data.get('quality', 'medium')  # low, medium, high
        preset = data.get('preset', 'default')   # default, fast, detailed
        
        # 创建Meshroom服务实例
        meshroom_service = MeshroomService(current_app.config)
        
        # 启动异步重建任务
        result = meshroom_service.start_reconstruction(job_id, job_folder, quality, preset)
        
        if result['success']:
            return jsonify({
                'job_id': job_id,
                'status': 'started',
                'message': '3D重建任务已启动',
                'estimated_time': result.get('estimated_time', '10-30分钟'),
                'check_status': f'/api/status/{job_id}'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': f'重建启动失败: {str(e)}'}), 500

@main.route('/api/status/<job_id>', methods=['GET'])
def check_status(job_id):
    """检查3D重建任务状态"""
    try:
        meshroom_service = MeshroomService(current_app.config)
        status = meshroom_service.get_reconstruction_status(job_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'状态查询失败: {str(e)}'}), 500

@main.route('/api/download/<job_id>', methods=['GET'])
def download_model(job_id):
    """下载生成的3D模型"""
    try:
        models_folder = current_app.config['MODELS_FOLDER']
        model_file = os.path.join(models_folder, f'{job_id}.obj')
        
        if not os.path.exists(model_file):
            return jsonify({'error': '3D模型文件不存在'}), 404
        
        return send_file(model_file, as_attachment=True, download_name=f'model_{job_id}.obj')
        
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

@main.route('/api/jobs', methods=['GET'])
def list_jobs():
    """列出所有任务"""
    try:
        meshroom_service = MeshroomService(current_app.config)
        jobs = meshroom_service.list_all_jobs()
        return jsonify({'jobs': jobs})
    except Exception as e:
        return jsonify({'error': f'获取任务列表失败: {str(e)}'}), 500