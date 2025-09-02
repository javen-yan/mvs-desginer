#!/usr/bin/env python3
"""
Meshroom安装和配置辅助脚本
"""

import os
import sys
import subprocess
import platform
import requests
import zipfile
import tarfile
from pathlib import Path

class MeshroomInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.base_url = "https://github.com/alicevision/meshroom/releases"
        self.install_dir = "/opt/Meshroom" if self.system != "windows" else "C:\\Program Files\\Meshroom"
    
    def check_system_requirements(self):
        """检查系统要求"""
        requirements = {
            'python_version': sys.version_info >= (3, 7),
            'gpu_available': self._check_gpu(),
            'memory': self._check_memory(),
            'disk_space': self._check_disk_space()
        }
        
        print("系统要求检查:")
        for req, status in requirements.items():
            status_text = "✓" if status else "✗"
            print(f"  {status_text} {req}: {status}")
        
        return all(requirements.values())
    
    def _check_gpu(self):
        """检查GPU是否可用"""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_memory(self):
        """检查内存是否足够（建议8GB+）"""
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            return memory_gb >= 8
        except ImportError:
            return True  # 无法检测时假设足够
    
    def _check_disk_space(self):
        """检查磁盘空间（建议20GB+）"""
        try:
            import psutil
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            return free_gb >= 20
        except ImportError:
            return True
    
    def get_latest_release_info(self):
        """获取最新版本信息"""
        try:
            api_url = "https://api.github.com/repos/alicevision/meshroom/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            return {
                'version': release_data['tag_name'],
                'download_url': self._find_download_url(release_data['assets']),
                'release_notes': release_data['body']
            }
        except Exception as e:
            print(f"获取版本信息失败: {e}")
            return None
    
    def _find_download_url(self, assets):
        """根据系统平台找到对应的下载链接"""
        system_mapping = {
            'linux': 'linux',
            'windows': 'windows',
            'darwin': 'mac'
        }
        
        system_key = system_mapping.get(self.system, 'linux')
        
        for asset in assets:
            name = asset['name'].lower()
            if system_key in name and ('zip' in name or 'tar' in name):
                return asset['browser_download_url']
        
        return None
    
    def install_meshroom(self, download_url=None):
        """安装Meshroom"""
        if not download_url:
            release_info = self.get_latest_release_info()
            if not release_info:
                print("无法获取Meshroom下载链接")
                return False
            download_url = release_info['download_url']
        
        if not download_url:
            print("未找到适合当前系统的Meshroom版本")
            return False
        
        try:
            print(f"开始下载Meshroom: {download_url}")
            
            # 下载文件
            filename = download_url.split('/')[-1]
            download_path = f"/tmp/{filename}"
            
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("下载完成，开始解压...")
            
            # 解压文件
            os.makedirs(self.install_dir, exist_ok=True)
            
            if filename.endswith('.zip'):
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(self.install_dir)
            elif filename.endswith('.tar.gz'):
                with tarfile.open(download_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(self.install_dir)
            
            # 设置执行权限
            if self.system != 'windows':
                meshroom_executable = os.path.join(self.install_dir, 'meshroom_batch')
                if os.path.exists(meshroom_executable):
                    os.chmod(meshroom_executable, 0o755)
            
            # 清理下载文件
            os.remove(download_path)
            
            print(f"Meshroom安装完成: {self.install_dir}")
            return True
            
        except Exception as e:
            print(f"安装失败: {e}")
            return False
    
    def setup_environment(self):
        """设置环境变量"""
        if self.system != 'windows':
            bashrc_path = os.path.expanduser('~/.bashrc')
            export_line = f'export PATH="{self.install_dir}:$PATH"'
            
            try:
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                
                if export_line not in content:
                    with open(bashrc_path, 'a') as f:
                        f.write(f'\n# Meshroom path\n{export_line}\n')
                    
                    print("已添加Meshroom到PATH环境变量")
                    print("请运行 'source ~/.bashrc' 或重新打开终端")
                
            except Exception as e:
                print(f"设置环境变量失败: {e}")
    
    def verify_installation(self):
        """验证安装是否成功"""
        try:
            # 查找meshroom_batch可执行文件
            possible_paths = [
                os.path.join(self.install_dir, 'meshroom_batch'),
                os.path.join(self.install_dir, 'meshroom_batch.exe'),
                'meshroom_batch'
            ]
            
            for path in possible_paths:
                if os.path.exists(path) or subprocess.run(['which', path], capture_output=True).returncode == 0:
                    # 测试运行
                    result = subprocess.run([path, '--help'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"✓ Meshroom安装验证成功: {path}")
                        return True
            
            print("✗ Meshroom安装验证失败")
            return False
            
        except Exception as e:
            print(f"验证过程出错: {e}")
            return False

def main():
    """主安装流程"""
    installer = MeshroomInstaller()
    
    print("MVS Designer - Meshroom安装工具")
    print("=" * 40)
    
    # 检查系统要求
    if not installer.check_system_requirements():
        print("系统要求检查未通过，请解决相关问题后重试")
        return
    
    # 检查是否已安装
    if installer.verify_installation():
        print("Meshroom已经安装并可用")
        return
    
    # 获取最新版本信息
    release_info = installer.get_latest_release_info()
    if release_info:
        print(f"最新版本: {release_info['version']}")
        
        # 询问是否安装
        response = input("是否下载并安装Meshroom? (y/N): ")
        if response.lower() == 'y':
            if installer.install_meshroom(release_info['download_url']):
                installer.setup_environment()
                installer.verify_installation()
            else:
                print("安装失败")
    else:
        print("无法获取Meshroom版本信息，请手动安装")

if __name__ == "__main__":
    main()