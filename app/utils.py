import os
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_images(folder_path):
    """验证上传的图片质量和格式"""
    try:
        image_files = [f for f in os.listdir(folder_path) if allowed_file(f)]
        
        if len(image_files) < 3:
            return {'valid': False, 'message': '图片数量不足，至少需要3张'}
        
        valid_images = []
        for image_file in image_files:
            image_path = os.path.join(folder_path, image_file)
            
            # 检查图片是否可以正常打开
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    
                    # 检查分辨率
                    if width < 800 or height < 600:
                        continue  # 跳过分辨率过低的图片
                    
                    # 检查图片是否损坏
                    img.verify()
                    valid_images.append(image_file)
                    
            except Exception:
                continue  # 跳过损坏的图片
        
        if len(valid_images) < 3:
            return {'valid': False, 'message': '有效图片数量不足，至少需要3张高质量图片'}
        
        return {
            'valid': True, 
            'message': f'验证通过，共{len(valid_images)}张有效图片',
            'valid_images': valid_images
        }
        
    except Exception as e:
        return {'valid': False, 'message': f'验证过程出错: {str(e)}'}

def get_image_metadata(image_path):
    """获取图片元数据"""
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            metadata = {}
            
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                data = exifdata.get(tag_id)
                metadata[tag] = data
            
            return {
                'size': img.size,
                'mode': img.mode,
                'format': img.format,
                'exif': metadata
            }
    except Exception as e:
        return {'error': str(e)}

def estimate_reconstruction_time(num_images, quality='medium'):
    """估算重建时间"""
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
        return f'{hours}小时{minutes}分钟'

def cleanup_old_jobs(config, days=7):
    """清理旧的任务文件"""
    import time
    import shutil
    from datetime import datetime, timedelta
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    # 清理上传文件夹
    uploads_folder = config['UPLOAD_FOLDER']
    for job_folder in os.listdir(uploads_folder):
        job_path = os.path.join(uploads_folder, job_folder)
        if os.path.isdir(job_path):
            if os.path.getctime(job_path) < cutoff_time:
                shutil.rmtree(job_path)
    
    # 清理模型文件夹
    models_folder = config['MODELS_FOLDER']
    for model_file in os.listdir(models_folder):
        model_path = os.path.join(models_folder, model_file)
        if os.path.isfile(model_path):
            if os.path.getctime(model_path) < cutoff_time:
                os.remove(model_path)