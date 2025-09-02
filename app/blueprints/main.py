"""
Main application blueprint.
"""
import logging
from flask import Blueprint, request, jsonify, render_template

from ..middleware.auth import auth_required, optional_auth
from ..auth import AuthService

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
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


@main_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'MVS Designer',
        'version': '2.0.0'
    })


@main_bp.route('/info', methods=['GET'])
def service_info():
    """服务信息端点"""
    return jsonify({
        'service': 'MVS Designer',
        'description': '基于Meshroom的多维度照片3D建模服务',
        'version': '2.0.0',
        'features': [
            'User Authentication',
            'PostgreSQL Database', 
            'S3 Object Storage',
            '3D Model Preview',
            'Multi-quality Reconstruction'
        ],
        'api_version': 'v2',
        'documentation': '/api/docs'
    })
