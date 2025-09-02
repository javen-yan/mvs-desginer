"""
Meshroom service for 3D reconstruction with database integration.
"""
import os
import json
import subprocess
import threading
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ..extensions import db
from ..models import ReconstructionJob
from ..utils import allowed_file
from ..logger import get_logger

logger = get_logger('meshroom_service')


class MeshroomService:
    def __init__(self, config):
        self.config = config
        self.jobs_status = {}  # 存储任务状态
        self.meshroom_path = self._find_meshroom_executable()
        
    def _find_meshroom_executable(self):
        """查找Meshroom可执行文件路径"""
        # 常见的Meshroom安装路径
        possible_paths = [
            '/usr/local/bin/meshroom_batch',
            '/opt/Meshroom/meshroom_batch',
            '/usr/bin/meshroom_batch',
            'meshroom_batch',  # 如果在PATH中
            # Windows路径
            'C:\\Program Files\\Meshroom\\meshroom_batch.exe',
            # macOS路径
            '/Applications/Meshroom.app/Contents/MacOS/meshroom_batch'
        ]
        
        for path in possible_paths:
            if shutil.which(path) or os.path.exists(path):
                return path
        
        # 如果没找到，返回默认值，让用户自己配置
        return 'meshroom_batch'
    
    def start_reconstruction(self, job_id: str, input_folder: str, 
                           quality: str = 'medium', preset: str = 'default') -> Dict[str, Any]:
        """启动3D重建任务"""
        try:
            # 设置输出路径
            output_folder = os.path.join(self.config['MODELS_FOLDER'], job_id)
            temp_folder = os.path.join(self.config['TEMP_FOLDER'], job_id)
            
            os.makedirs(output_folder, exist_ok=True)
            os.makedirs(temp_folder, exist_ok=True)
            
            # 更新数据库中的任务状态
            reconstruction_job = ReconstructionJob.query.filter_by(job_id=job_id).first()
            if reconstruction_job:
                reconstruction_job.update_status('initializing', 0.0)
                reconstruction_job.output_folder = output_folder
                db.session.commit()
            
            # 初始化任务状态
            self.jobs_status[job_id] = {
                'status': 'initializing',
                'progress': 0,
                'start_time': datetime.now().isoformat(),
                'message': '初始化重建任务...',
                'input_folder': input_folder,
                'output_folder': output_folder,
                'temp_folder': temp_folder,
                'quality': quality,
                'preset': preset
            }
            
            # 在后台线程中执行重建
            thread = threading.Thread(
                target=self._run_reconstruction,
                args=(job_id, input_folder, output_folder, temp_folder, quality, preset)
            )
            thread.daemon = True
            thread.start()
            
            return {
                'success': True,
                'estimated_time': self._estimate_time(input_folder, quality)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _run_reconstruction(self, job_id: str, input_folder: str, output_folder: str, 
                           temp_folder: str, quality: str, preset: str) -> None:
        """执行Meshroom重建流程"""
        try:
            # 更新内存状态
            self.jobs_status[job_id]['status'] = 'running'
            self.jobs_status[job_id]['message'] = '正在进行3D重建...'
            
            # 更新数据库状态
            self._update_job_status(job_id, 'running', 5.0, '正在进行3D重建...')
            
            # 构建Meshroom命令
            cmd = self._build_meshroom_command(input_folder, output_folder, temp_folder, quality, preset)
            
            # 更新状态
            self.jobs_status[job_id]['progress'] = 10
            self.jobs_status[job_id]['message'] = '启动Meshroom处理...'
            self._update_job_status(job_id, 'running', 10.0, '启动Meshroom处理...')
            
            logger.info(f"Starting Meshroom reconstruction for job {job_id}")
            
            # 执行Meshroom命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=temp_folder
            )
            
            # 监控进度
            self._monitor_progress(job_id, process)
            
            # 等待完成
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # 处理输出文件
                output_file = self._process_output(job_id, temp_folder, output_folder)
                
                self.jobs_status[job_id]['status'] = 'completed'
                self.jobs_status[job_id]['progress'] = 100
                self.jobs_status[job_id]['message'] = '3D重建完成'
                self.jobs_status[job_id]['end_time'] = datetime.now().isoformat()
                self.jobs_status[job_id]['output_file'] = output_file
                
                # 更新数据库状态
                self._update_job_status(job_id, 'completed', 100.0, '3D重建完成')
                
                # 生成模型信息
                self._generate_model_info(job_id, output_folder)
                
                logger.info(f"Reconstruction completed for job {job_id}")
                
            else:
                error_msg = f'重建失败: {stderr}'
                self.jobs_status[job_id]['status'] = 'failed'
                self.jobs_status[job_id]['message'] = error_msg
                
                # 更新数据库状态
                self._update_job_status(job_id, 'failed', error_message=error_msg)
                
                logger.error(f"Reconstruction failed for job {job_id}: {stderr}")
                
        except Exception as e:
            error_msg = f'重建过程出错: {str(e)}'
            self.jobs_status[job_id]['status'] = 'failed'
            self.jobs_status[job_id]['message'] = error_msg
            
            # 更新数据库状态
            self._update_job_status(job_id, 'failed', error_message=error_msg)
            
            logger.error(f"Reconstruction error for job {job_id}: {e}")
    
    def _update_job_status(self, job_id: str, status: str, progress: float = None, 
                          message: str = None, error_message: str = None) -> None:
        """更新数据库中的任务状态"""
        try:
            reconstruction_job = ReconstructionJob.query.filter_by(job_id=job_id).first()
            if reconstruction_job:
                reconstruction_job.update_status(
                    status=status,
                    progress=progress,
                    error_message=error_message
                )
                db.session.commit()
        except Exception as e:
            logger.error(f"Failed to update job status in database: {e}")
            db.session.rollback()
    
    def _build_meshroom_command(self, input_folder, output_folder, temp_folder, quality, preset):
        """构建Meshroom命令行参数"""
        cmd = [
            self.meshroom_path,
            '--input', input_folder,
            '--output', output_folder,
            '--cache', temp_folder
        ]
        
        # 根据质量设置参数
        quality_settings = {
            'low': ['--preset', 'draft'],
            'medium': ['--preset', 'default'],
            'high': ['--preset', 'detailed']
        }
        
        if quality in quality_settings:
            cmd.extend(quality_settings[quality])
        
        # 添加其他参数
        cmd.extend([
            '--verbose', 'info',
            '--save', os.path.join(temp_folder, 'pipeline.mg')
        ])
        
        return cmd
    
    def _monitor_progress(self, job_id, process):
        """监控Meshroom进程进度"""
        # 这里可以解析Meshroom的输出来更新进度
        # 由于Meshroom输出格式复杂，这里使用简单的时间估算
        start_time = time.time()
        
        while process.poll() is None:
            elapsed = time.time() - start_time
            # 简单的进度估算（实际应该解析Meshroom日志）
            progress = min(90, int(elapsed / 60 * 10))  # 假设每分钟增加10%
            
            if job_id in self.jobs_status:
                self.jobs_status[job_id]['progress'] = progress
                
            time.sleep(30)  # 每30秒更新一次
    
    def _process_output(self, job_id, temp_folder, output_folder):
        """处理Meshroom输出文件"""
        # 查找生成的模型文件
        possible_output_paths = [
            os.path.join(temp_folder, 'Texturing', '*.obj'),
            os.path.join(temp_folder, 'Meshing', '*.obj'),
            os.path.join(temp_folder, '*.obj')
        ]
        
        model_file = None
        for pattern in possible_output_paths:
            import glob
            files = glob.glob(pattern)
            if files:
                model_file = files[0]
                break
        
        if model_file:
            # 复制模型文件到输出目录
            output_model = os.path.join(output_folder, f'{job_id}.obj')
            shutil.copy2(model_file, output_model)
            
            # 复制相关的纹理文件
            model_dir = os.path.dirname(model_file)
            for ext in ['*.jpg', '*.png', '*.mtl']:
                import glob
                texture_files = glob.glob(os.path.join(model_dir, ext))
                for texture_file in texture_files:
                    shutil.copy2(texture_file, output_folder)
    
    def _generate_model_info(self, job_id, output_folder):
        """生成模型信息文件"""
        info = {
            'job_id': job_id,
            'generated_at': datetime.now().isoformat(),
            'files': os.listdir(output_folder),
            'main_model': f'{job_id}.obj'
        }
        
        info_file = os.path.join(output_folder, 'model_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    
    def _estimate_time(self, input_folder, quality):
        """估算处理时间"""
        num_images = len([f for f in os.listdir(input_folder) if allowed_file(f)])
        
        time_multiplier = {
            'low': 1,
            'medium': 2,
            'high': 4
        }
        
        base_minutes = num_images * 3 * time_multiplier.get(quality, 2)
        return f'{base_minutes}-{base_minutes * 2}分钟'
    
    def get_reconstruction_status(self, job_id):
        """获取重建任务状态"""
        if job_id not in self.jobs_status:
            return {'error': '任务不存在'}
        
        status = self.jobs_status[job_id].copy()
        
        # 检查输出文件是否存在
        if status['status'] == 'completed':
            output_folder = status['output_folder']
            model_file = os.path.join(output_folder, f'{job_id}.obj')
            status['model_ready'] = os.path.exists(model_file)
            
            if status['model_ready']:
                status['download_url'] = f'/api/download/{job_id}'
                status['file_size'] = os.path.getsize(model_file)
        
        return status
    
    def list_all_jobs(self):
        """列出所有任务"""
        jobs = []
        for job_id, status in self.jobs_status.items():
            job_info = {
                'job_id': job_id,
                'status': status['status'],
                'start_time': status.get('start_time'),
                'progress': status.get('progress', 0)
            }
            jobs.append(job_info)
        
        return jobs
    
    def cleanup_job(self, job_id):
        """清理任务文件"""
        try:
            # 删除上传文件
            upload_folder = os.path.join(self.config['UPLOAD_FOLDER'], job_id)
            if os.path.exists(upload_folder):
                shutil.rmtree(upload_folder)
            
            # 删除临时文件
            temp_folder = os.path.join(self.config['TEMP_FOLDER'], job_id)
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
            
            # 从状态字典中移除
            if job_id in self.jobs_status:
                del self.jobs_status[job_id]
                
            return True
        except Exception as e:
            print(f"清理任务{job_id}失败: {e}")
            return False