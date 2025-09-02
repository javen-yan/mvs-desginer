#!/usr/bin/env python3
"""
MVS Designer API测试脚本
"""

import requests
import json
import time
import os
from pathlib import Path

class MVSDesignerTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_service_info(self):
        """测试服务信息接口"""
        print("测试服务信息接口...")
        try:
            response = self.session.get(f'{self.base_url}/')
            response.raise_for_status()
            
            data = response.json()
            print(f"✓ 服务名称: {data['service']}")
            print(f"✓ 版本: {data['version']}")
            print(f"✓ 描述: {data['description']}")
            return True
        except Exception as e:
            print(f"✗ 服务信息测试失败: {e}")
            return False
    
    def test_upload_images(self, image_folder):
        """测试图片上传接口"""
        print(f"\n测试图片上传接口 (文件夹: {image_folder})...")
        
        if not os.path.exists(image_folder):
            print(f"✗ 图片文件夹不存在: {image_folder}")
            return None
        
        # 收集图片文件
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            image_files.extend(Path(image_folder).glob(f'*{ext}'))
            image_files.extend(Path(image_folder).glob(f'*{ext.upper()}'))
        
        if len(image_files) < 3:
            print(f"✗ 图片数量不足: {len(image_files)} (需要至少3张)")
            return None
        
        try:
            files = []
            for image_file in image_files[:20]:  # 最多上传20张
                files.append(('images', open(image_file, 'rb')))
            
            response = self.session.post(f'{self.base_url}/api/upload', files=files)
            
            # 关闭文件
            for _, file_obj in files:
                file_obj.close()
            
            response.raise_for_status()
            data = response.json()
            
            print(f"✓ 上传成功")
            print(f"  任务ID: {data['job_id']}")
            print(f"  上传文件数: {len(data['uploaded_files'])}")
            
            return data['job_id']
            
        except Exception as e:
            print(f"✗ 图片上传失败: {e}")
            return None
    
    def test_reconstruction(self, job_id, quality='medium'):
        """测试3D重建接口"""
        print(f"\n测试3D重建接口 (任务ID: {job_id})...")
        
        try:
            payload = {
                'job_id': job_id,
                'quality': quality
            }
            
            response = self.session.post(
                f'{self.base_url}/api/reconstruct',
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"✓ 重建任务启动成功")
            print(f"  预计耗时: {data['estimated_time']}")
            print(f"  状态检查: {data['check_status']}")
            
            return True
            
        except Exception as e:
            print(f"✗ 重建启动失败: {e}")
            return False
    
    def test_status_monitoring(self, job_id, max_wait_minutes=30):
        """测试状态监控"""
        print(f"\n监控重建状态 (最长等待: {max_wait_minutes}分钟)...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = self.session.get(f'{self.base_url}/api/status/{job_id}')
                response.raise_for_status()
                
                data = response.json()
                
                if 'error' in data:
                    print(f"✗ 状态查询错误: {data['error']}")
                    return False
                
                status = data['status']
                progress = data.get('progress', 0)
                message = data.get('message', '')
                
                print(f"  状态: {status} | 进度: {progress}% | {message}")
                
                if status == 'completed':
                    print("✓ 重建完成！")
                    if data.get('model_ready'):
                        print(f"  模型文件大小: {data.get('file_size', 0)} bytes")
                        print(f"  下载链接: {data.get('download_url')}")
                    return True
                    
                elif status == 'failed':
                    print(f"✗ 重建失败: {message}")
                    return False
                
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                print(f"状态查询异常: {e}")
                time.sleep(10)
        
        print(f"✗ 等待超时 ({max_wait_minutes}分钟)")
        return False
    
    def test_download_model(self, job_id, output_path='./downloaded_model.obj'):
        """测试模型下载"""
        print(f"\n测试模型下载...")
        
        try:
            response = self.session.get(f'{self.base_url}/api/download/{job_id}')
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_path)
            print(f"✓ 模型下载成功")
            print(f"  保存路径: {output_path}")
            print(f"  文件大小: {file_size} bytes")
            
            return True
            
        except Exception as e:
            print(f"✗ 模型下载失败: {e}")
            return False
    
    def run_full_test(self, image_folder, quality='medium'):
        """运行完整测试流程"""
        print("=" * 60)
        print("MVS Designer 完整功能测试")
        print("=" * 60)
        
        # 1. 测试服务信息
        if not self.test_service_info():
            return False
        
        # 2. 测试图片上传
        job_id = self.test_upload_images(image_folder)
        if not job_id:
            return False
        
        # 3. 测试重建启动
        if not self.test_reconstruction(job_id, quality):
            return False
        
        # 4. 监控重建进度
        if not self.test_status_monitoring(job_id):
            return False
        
        # 5. 测试模型下载
        if not self.test_download_model(job_id):
            return False
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='MVS Designer API测试工具')
    parser.add_argument('--url', default='http://localhost:5000', help='服务URL')
    parser.add_argument('--images', required=True, help='测试图片文件夹路径')
    parser.add_argument('--quality', choices=['low', 'medium', 'high'], default='medium', help='重建质量')
    
    args = parser.parse_args()
    
    tester = MVSDesignerTester(args.url)
    tester.run_full_test(args.images, args.quality)

if __name__ == "__main__":
    main()