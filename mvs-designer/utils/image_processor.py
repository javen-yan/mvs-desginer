"""
图像处理工具模块
用于照片预处理和质量检查
"""

import cv2
import numpy as np
import os
from PIL import Image, ImageEnhance
from PIL.ExifTags import TAGS
import json

class ImageProcessor:
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    
    def preprocess_images(self, input_folder, output_folder=None):
        """预处理图片，提高重建质量"""
        if output_folder is None:
            output_folder = input_folder
        
        os.makedirs(output_folder, exist_ok=True)
        
        processed_files = []
        for filename in os.listdir(input_folder):
            if self._is_image_file(filename):
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, filename)
                
                if self._process_single_image(input_path, output_path):
                    processed_files.append(filename)
        
        return processed_files
    
    def _process_single_image(self, input_path, output_path):
        """处理单张图片"""
        try:
            # 使用PIL打开图片
            with Image.open(input_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整图片大小（如果太大）
                max_size = 4000
                if max(img.size) > max_size:
                    ratio = max_size / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 增强对比度和锐度
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)
                
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
                
                # 保存处理后的图片
                img.save(output_path, 'JPEG', quality=95)
                return True
                
        except Exception as e:
            print(f"处理图片{input_path}失败: {e}")
            return False
    
    def analyze_image_set(self, folder_path):
        """分析图片集合的质量和特征"""
        analysis = {
            'total_images': 0,
            'valid_images': 0,
            'resolution_stats': {'min': None, 'max': None, 'avg': None},
            'format_distribution': {},
            'quality_score': 0,
            'recommendations': []
        }
        
        resolutions = []
        formats = {}
        
        for filename in os.listdir(folder_path):
            if self._is_image_file(filename):
                analysis['total_images'] += 1
                image_path = os.path.join(folder_path, filename)
                
                try:
                    with Image.open(image_path) as img:
                        width, height = img.size
                        resolutions.append(width * height)
                        
                        # 统计格式
                        fmt = img.format.lower()
                        formats[fmt] = formats.get(fmt, 0) + 1
                        
                        # 检查图片质量
                        if self._check_image_quality(img):
                            analysis['valid_images'] += 1
                            
                except Exception:
                    continue
        
        # 计算统计信息
        if resolutions:
            analysis['resolution_stats'] = {
                'min': min(resolutions),
                'max': max(resolutions),
                'avg': sum(resolutions) // len(resolutions)
            }
        
        analysis['format_distribution'] = formats
        analysis['quality_score'] = self._calculate_quality_score(analysis)
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _is_image_file(self, filename):
        """检查是否为支持的图片文件"""
        return any(filename.lower().endswith(ext) for ext in self.supported_formats)
    
    def _check_image_quality(self, img):
        """检查单张图片质量"""
        width, height = img.size
        
        # 检查分辨率
        if width < 800 or height < 600:
            return False
        
        # 检查宽高比
        aspect_ratio = width / height
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            return False
        
        return True
    
    def _calculate_quality_score(self, analysis):
        """计算图片集合质量分数（0-100）"""
        if analysis['total_images'] == 0:
            return 0
        
        score = 0
        
        # 图片数量得分（30%）
        num_score = min(30, analysis['valid_images'] * 3)
        score += num_score
        
        # 分辨率得分（40%）
        if analysis['resolution_stats']['avg']:
            avg_res = analysis['resolution_stats']['avg']
            if avg_res >= 2000000:  # 2MP+
                score += 40
            elif avg_res >= 1000000:  # 1MP+
                score += 30
            elif avg_res >= 500000:   # 0.5MP+
                score += 20
            else:
                score += 10
        
        # 有效率得分（30%）
        valid_ratio = analysis['valid_images'] / analysis['total_images']
        score += valid_ratio * 30
        
        return min(100, int(score))
    
    def _generate_recommendations(self, analysis):
        """生成改进建议"""
        recommendations = []
        
        if analysis['valid_images'] < 10:
            recommendations.append('建议增加照片数量至10张以上，以提高重建质量')
        
        if analysis['quality_score'] < 60:
            recommendations.append('图片质量偏低，建议使用更高分辨率的相机拍摄')
        
        if analysis['resolution_stats']['avg'] and analysis['resolution_stats']['avg'] < 1000000:
            recommendations.append('图片分辨率较低，建议使用至少1MP的照片')
        
        return recommendations
    
    def extract_camera_info(self, image_path):
        """提取相机信息"""
        try:
            with Image.open(image_path) as img:
                exifdata = img.getexif()
                
                camera_info = {}
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exifdata.get(tag_id)
                    
                    if tag in ['Make', 'Model', 'FocalLength', 'FNumber', 'ExposureTime', 'ISO']:
                        camera_info[tag] = str(data)
                
                return camera_info
        except Exception:
            return {}