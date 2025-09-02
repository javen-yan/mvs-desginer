#!/usr/bin/env python3
"""
API测试脚本 - MVS Designer v2.0
测试用户认证、任务管理、S3集成等新功能
"""
import requests
import json
import time
import os
from pathlib import Path


class MVSDesignerAPITest:
    """MVS Designer API测试类"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
        self.test_user = {
            'username': 'test_user',
            'email': 'test@example.com',
            'password': 'test123456'
        }
    
    def log(self, message: str, level: str = 'INFO'):
        """记录测试日志"""
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def test_service_info(self):
        """测试服务信息接口"""
        self.log("测试服务信息接口...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/",
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ 服务信息: {data['service']} v{data['version']}")
                self.log(f"✓ 功能列表: {', '.join(data['features'])}")
                return True
            else:
                self.log(f"✗ 服务信息获取失败: {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ 服务信息测试异常: {e}", 'ERROR')
            return False
    
    def test_user_registration(self):
        """测试用户注册"""
        self.log("测试用户注册...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=self.test_user
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log(f"✓ 用户注册成功: {data['user']['username']}")
                return True
            elif response.status_code == 400:
                error_data = response.json()
                if 'already' in error_data.get('error', '').lower():
                    self.log("✓ 用户已存在，跳过注册")
                    return True
                else:
                    self.log(f"✗ 注册失败: {error_data.get('error')}", 'ERROR')
                    return False
            else:
                self.log(f"✗ 注册失败: {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ 注册测试异常: {e}", 'ERROR')
            return False
    
    def test_user_login(self):
        """测试用户登录"""
        self.log("测试用户登录...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={
                    'username': self.test_user['username'],
                    'password': self.test_user['password']
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                self.log(f"✓ 登录成功: {data['user']['username']}")
                return True
            else:
                error_data = response.json()
                self.log(f"✗ 登录失败: {error_data.get('error')}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ 登录测试异常: {e}", 'ERROR')
            return False
    
    def test_user_profile(self):
        """测试用户信息获取"""
        self.log("测试用户信息获取...")
        
        if not self.auth_token:
            self.log("✗ 需要先登录", 'ERROR')
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/auth/profile")
            
            if response.status_code == 200:
                data = response.json()
                user = data['user']
                self.log(f"✓ 用户信息: {user['username']} ({user['email']})")
                self.log(f"✓ 任务数量: {user['job_count']}")
                return True
            else:
                error_data = response.json()
                self.log(f"✗ 获取用户信息失败: {error_data.get('error')}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ 用户信息测试异常: {e}", 'ERROR')
            return False
    
    def test_image_upload(self):
        """测试图片上传"""
        self.log("测试图片上传...")
        
        if not self.auth_token:
            self.log("✗ 需要先登录", 'ERROR')
            return False, None
        
        # 创建测试图片
        test_images = self._create_test_images()
        
        try:
            files = []
            for i, image_path in enumerate(test_images):
                files.append(('images', (f'test_image_{i+1}.jpg', open(image_path, 'rb'), 'image/jpeg')))
            
            data = {
                'title': 'API测试任务',
                'description': '这是一个API测试任务'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/upload",
                files=files,
                data=data
            )
            
            # 关闭文件
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            if response.status_code == 200:
                upload_data = response.json()
                job_id = upload_data['job_id']
                self.log(f"✓ 图片上传成功: {len(upload_data['uploaded_files'])}张")
                self.log(f"✓ 任务ID: {job_id}")
                return True, job_id
            else:
                error_data = response.json()
                self.log(f"✗ 上传失败: {error_data.get('error')}", 'ERROR')
                return False, None
                
        except Exception as e:
            self.log(f"✗ 上传测试异常: {e}", 'ERROR')
            return False, None
        finally:
            # 清理测试图片
            self._cleanup_test_images(test_images)
    
    def test_reconstruction_start(self, job_id: str):
        """测试3D重建启动"""
        self.log("测试3D重建启动...")
        
        if not self.auth_token or not job_id:
            self.log("✗ 需要认证和有效的job_id", 'ERROR')
            return False
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/reconstruct",
                json={
                    'job_id': job_id,
                    'quality': 'low',  # 使用低质量以便快速测试
                    'preset': 'fast'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ 重建任务启动成功")
                self.log(f"✓ 状态: {data['status']}")
                self.log(f"✓ 预估时间: {data['estimated_time']}")
                return True
            else:
                error_data = response.json()
                self.log(f"✗ 重建启动失败: {error_data.get('error')}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ 重建启动测试异常: {e}", 'ERROR')
            return False
    
    def test_job_status(self, job_id: str):
        """测试任务状态查询"""
        self.log("测试任务状态查询...")
        
        if not self.auth_token or not job_id:
            self.log("✗ 需要认证和有效的job_id", 'ERROR')
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/status/{job_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ 任务状态: {data['status']}")
                self.log(f"✓ 进度: {data['progress']:.1f}%")
                if data.get('title'):
                    self.log(f"✓ 任务标题: {data['title']}")
                return True, data
            else:
                error_data = response.json()
                self.log(f"✗ 状态查询失败: {error_data.get('error')}", 'ERROR')
                return False, None
                
        except Exception as e:
            self.log(f"✗ 状态查询测试异常: {e}", 'ERROR')
            return False, None
    
    def test_jobs_list(self):
        """测试任务列表获取"""
        self.log("测试任务列表获取...")
        
        if not self.auth_token:
            self.log("✗ 需要先登录", 'ERROR')
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/jobs")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ 获取到 {len(data['jobs'])} 个任务")
                self.log(f"✓ 总计: {data['total']} 个任务")
                return True
            else:
                error_data = response.json()
                self.log(f"✗ 任务列表获取失败: {error_data.get('error')}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ 任务列表测试异常: {e}", 'ERROR')
            return False
    
    def test_user_stats(self):
        """测试用户统计信息"""
        self.log("测试用户统计信息...")
        
        if not self.auth_token:
            self.log("✗ 需要先登录", 'ERROR')
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/stats")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data['jobs']
                self.log(f"✓ 用户统计:")
                self.log(f"  - 总任务: {jobs['total']}")
                self.log(f"  - 已完成: {jobs['completed']}")
                self.log(f"  - 进行中: {jobs['running']}")
                self.log(f"  - 失败: {jobs['failed']}")
                self.log(f"  - 等待中: {jobs['pending']}")
                return True
            else:
                error_data = response.json()
                self.log(f"✗ 统计信息获取失败: {error_data.get('error')}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ 统计信息测试异常: {e}", 'ERROR')
            return False
    
    def _create_test_images(self):
        """创建测试图片"""
        from PIL import Image, ImageDraw
        
        test_images = []
        temp_dir = Path('/tmp/mvs_test_images')
        temp_dir.mkdir(exist_ok=True)
        
        # 创建3张不同的测试图片
        for i in range(3):
            img = Image.new('RGB', (1024, 768), color=(i*80, 100, 200-i*50))
            draw = ImageDraw.Draw(img)
            
            # 添加一些几何图形
            draw.rectangle([100+i*50, 100, 300+i*50, 300], fill=(255-i*80, i*100, 100))
            draw.ellipse([400+i*30, 200, 600+i*30, 400], fill=(100, 255-i*80, i*100))
            
            # 添加文字
            draw.text((50, 50), f"Test Image {i+1}", fill=(255, 255, 255))
            
            image_path = temp_dir / f'test_image_{i+1}.jpg'
            img.save(image_path, 'JPEG', quality=95)
            test_images.append(str(image_path))
        
        return test_images
    
    def _cleanup_test_images(self, image_paths):
        """清理测试图片"""
        for path in image_paths:
            try:
                os.remove(path)
            except:
                pass
        
        try:
            os.rmdir('/tmp/mvs_test_images')
        except:
            pass
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始API测试...")
        self.log("=" * 50)
        
        tests_passed = 0
        total_tests = 0
        
        # 测试服务信息
        total_tests += 1
        if self.test_service_info():
            tests_passed += 1
        
        # 测试用户注册
        total_tests += 1
        if self.test_user_registration():
            tests_passed += 1
        
        # 测试用户登录
        total_tests += 1
        if self.test_user_login():
            tests_passed += 1
        
        # 测试用户信息
        total_tests += 1
        if self.test_user_profile():
            tests_passed += 1
        
        # 测试图片上传
        total_tests += 1
        upload_success, job_id = self.test_image_upload()
        if upload_success:
            tests_passed += 1
        
        # 如果上传成功，测试重建
        if upload_success and job_id:
            total_tests += 1
            if self.test_reconstruction_start(job_id):
                tests_passed += 1
            
            # 测试状态查询
            total_tests += 1
            status_success, status_data = self.test_job_status(job_id)
            if status_success:
                tests_passed += 1
        
        # 测试任务列表
        total_tests += 1
        if self.test_jobs_list():
            tests_passed += 1
        
        # 测试用户统计
        total_tests += 1
        if self.test_user_stats():
            tests_passed += 1
        
        # 测试结果
        self.log("=" * 50)
        self.log(f"测试完成: {tests_passed}/{total_tests} 通过")
        
        if tests_passed == total_tests:
            self.log("✓ 所有测试通过!", 'SUCCESS')
            return True
        else:
            self.log(f"✗ {total_tests - tests_passed} 个测试失败", 'ERROR')
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MVS Designer API测试')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='API服务地址 (默认: http://localhost:5000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # 运行测试
    tester = MVSDesignerAPITest(args.url)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)


if __name__ == '__main__':
    main()