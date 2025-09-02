"""
Utility functions for MVS Designer application.
"""
import os
import time
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
from .logger import get_logger


logger = get_logger('utils')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}


def allowed_file(filename: str) -> bool:
    """
    检查文件扩展名是否允许
    
    Args:
        filename: 文件名
        
    Returns:
        是否允许的文件类型
    """
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS

def validate_images(folder_path: str) -> Dict[str, Any]:
    """
    验证上传的图片质量和格式
    
    Args:
        folder_path: 图片文件夹路径
        
    Returns:
        验证结果字典
    """
    try:
        if not os.path.exists(folder_path):
            return {'valid': False, 'message': '文件夹不存在'}
        
        image_files = [f for f in os.listdir(folder_path) if allowed_file(f)]
        
        if len(image_files) < 3:
            return {'valid': False, 'message': '图片数量不足，至少需要3张'}
        
        valid_images = []
        validation_details = []
        
        for image_file in image_files:
            image_path = os.path.join(folder_path, image_file)
            
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    file_size = os.path.getsize(image_path)
                    
                    # 检查分辨率
                    if width < 800 or height < 600:
                        validation_details.append({
                            'file': image_file,
                            'status': 'rejected',
                            'reason': f'分辨率过低 ({width}x{height})'
                        })
                        continue
                    
                    # 检查文件大小
                    if file_size > 50 * 1024 * 1024:  # 50MB
                        validation_details.append({
                            'file': image_file,
                            'status': 'rejected',
                            'reason': '文件过大 (>50MB)'
                        })
                        continue
                    
                    # 检查图片是否损坏
                    img.verify()
                    
                    valid_images.append(image_file)
                    validation_details.append({
                        'file': image_file,
                        'status': 'valid',
                        'resolution': f'{width}x{height}',
                        'size_mb': round(file_size / 1024 / 1024, 2)
                    })
                    
            except Exception as e:
                validation_details.append({
                    'file': image_file,
                    'status': 'rejected',
                    'reason': f'图片损坏: {str(e)}'
                })
                continue
        
        if len(valid_images) < 3:
            return {
                'valid': False, 
                'message': '有效图片数量不足，至少需要3张高质量图片',
                'details': validation_details
            }
        
        return {
            'valid': True, 
            'message': f'验证通过，共{len(valid_images)}张有效图片',
            'valid_images': valid_images,
            'details': validation_details
        }
        
    except Exception as e:
        logger.error(f"Image validation error: {e}")
        return {'valid': False, 'message': f'验证过程出错: {str(e)}'}

def get_image_metadata(image_path: str) -> Dict[str, Any]:
    """
    获取图片元数据
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        图片元数据字典
    """
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            metadata = {}
            
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                data = exifdata.get(tag_id)
                
                # 转换复杂数据类型为字符串
                if isinstance(data, (bytes, tuple)):
                    data = str(data)
                
                metadata[tag] = data
            
            return {
                'size': img.size,
                'mode': img.mode,
                'format': img.format,
                'file_size': os.path.getsize(image_path),
                'exif': metadata
            }
    except Exception as e:
        logger.error(f"Failed to get image metadata for {image_path}: {e}")
        return {'error': str(e)}


def estimate_reconstruction_time(num_images: int, quality: str = 'medium') -> str:
    """
    估算重建时间
    
    Args:
        num_images: 图片数量
        quality: 重建质量
        
    Returns:
        估算时间字符串
    """
    base_time = {
        'low': 2,      # 每张图片2分钟
        'medium': 4,   # 每张图片4分钟  
        'high': 8      # 每张图片8分钟
    }
    
    time_per_image = base_time.get(quality, 4)
    total_minutes = num_images * time_per_image
    
    if total_minutes < 60:
        return f'{total_minutes}分钟'
    else:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if minutes == 0:
            return f'{hours}小时'
        return f'{hours}小时{minutes}分钟'


def cleanup_old_jobs(config: Dict[str, Any], days: int = 7) -> Dict[str, Any]:
    """
    清理旧的任务文件
    
    Args:
        config: 应用配置
        days: 保留天数
        
    Returns:
        清理结果
    """
    try:
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        cleaned_folders = 0
        cleaned_files = 0
        
        # 清理上传文件夹
        uploads_folder = config.get('UPLOAD_FOLDER')
        if uploads_folder and os.path.exists(uploads_folder):
            for job_folder in os.listdir(uploads_folder):
                job_path = os.path.join(uploads_folder, job_folder)
                if os.path.isdir(job_path):
                    if os.path.getctime(job_path) < cutoff_time:
                        shutil.rmtree(job_path)
                        cleaned_folders += 1
        
        # 清理模型文件夹
        models_folder = config.get('MODELS_FOLDER')
        if models_folder and os.path.exists(models_folder):
            for model_file in os.listdir(models_folder):
                model_path = os.path.join(models_folder, model_file)
                if os.path.isfile(model_path):
                    if os.path.getctime(model_path) < cutoff_time:
                        os.remove(model_path)
                        cleaned_files += 1
        
        # 清理临时文件夹
        temp_folder = config.get('TEMP_FOLDER')
        if temp_folder and os.path.exists(temp_folder):
            for temp_item in os.listdir(temp_folder):
                temp_path = os.path.join(temp_folder, temp_item)
                if os.path.getctime(temp_path) < cutoff_time:
                    if os.path.isdir(temp_path):
                        shutil.rmtree(temp_path)
                        cleaned_folders += 1
                    else:
                        os.remove(temp_path)
                        cleaned_files += 1
        
        logger.info(f"Cleanup completed: {cleaned_folders} folders, {cleaned_files} files removed")
        
        return {
            'success': True,
            'cleaned_folders': cleaned_folders,
            'cleaned_files': cleaned_files,
            'cutoff_days': days
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_s3_config(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    验证S3配置
    
    Args:
        config: 应用配置
        
    Returns:
        (是否有效, 错误信息)
    """
    required_keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME']
    
    for key in required_keys:
        if not config.get(key):
            return False, f"Missing required S3 configuration: {key}"
    
    return True, None


def create_safe_filename(filename: str) -> str:
    """
    创建安全的文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    # 移除或替换不安全的字符
    import re
    
    # 保留文件扩展名
    name, ext = os.path.splitext(filename)
    
    # 移除特殊字符，只保留字母、数字、下划线和连字符
    safe_name = re.sub(r'[^\w\-_.]', '_', name)
    
    # 限制长度
    if len(safe_name) > 100:
        safe_name = safe_name[:100]
    
    return f"{safe_name}{ext}"


def get_image_quality_score(image_path: str) -> Dict[str, Any]:
    """
    评估图片质量分数
    
    Args:
        image_path: 图片路径
        
    Returns:
        质量评估结果
    """
    try:
        # 使用OpenCV读取图片
        img = cv2.imread(image_path)
        if img is None:
            return {'error': '无法读取图片'}
        
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 计算拉普拉斯方差（模糊度检测）
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 计算图片亮度
        brightness = np.mean(gray)
        
        # 计算对比度
        contrast = gray.std()
        
        # 质量评分
        blur_score = min(laplacian_var / 100, 10)  # 0-10分
        brightness_score = 10 - abs(brightness - 127) / 12.7  # 0-10分
        contrast_score = min(contrast / 25, 10)  # 0-10分
        
        overall_score = (blur_score + brightness_score + contrast_score) / 3
        
        return {
            'overall_score': round(overall_score, 2),
            'blur_score': round(blur_score, 2),
            'brightness_score': round(brightness_score, 2),
            'contrast_score': round(contrast_score, 2),
            'brightness': round(brightness, 2),
            'contrast': round(contrast, 2),
            'sharpness': round(laplacian_var, 2)
        }
        
    except Exception as e:
        logger.error(f"Quality assessment failed for {image_path}: {e}")
        return {'error': str(e)}