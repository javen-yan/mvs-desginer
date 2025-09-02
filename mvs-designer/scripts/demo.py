#!/usr/bin/env python3
"""
MVS Designer 演示脚本
创建示例照片集用于测试
"""

import os
import shutil
import requests
from PIL import Image, ImageDraw, ImageFont
import math

def create_demo_images(output_dir='demo_images', num_images=12):
    """创建演示用的多角度照片"""
    print(f"创建演示照片集: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建一个简单的3D物体图像（立方体）
    size = 800
    center = size // 2
    
    for i in range(num_images):
        # 计算角度
        angle = (i * 360 / num_images) * math.pi / 180
        
        # 创建图像
        img = Image.new('RGB', (size, size), 'white')
        draw = ImageDraw.Draw(img)
        
        # 绘制立方体的不同视角
        cube_size = 200
        x_offset = int(50 * math.cos(angle))
        y_offset = int(30 * math.sin(angle))
        
        # 立方体顶点
        points = [
            (center - cube_size//2 + x_offset, center - cube_size//2 + y_offset),
            (center + cube_size//2 + x_offset, center - cube_size//2 + y_offset),
            (center + cube_size//2 + x_offset, center + cube_size//2 + y_offset),
            (center - cube_size//2 + x_offset, center + cube_size//2 + y_offset)
        ]
        
        # 绘制立方体
        draw.polygon(points, fill='lightblue', outline='darkblue', width=3)
        
        # 添加纹理细节
        for j in range(5):
            for k in range(5):
                x = points[0][0] + j * cube_size // 5
                y = points[0][1] + k * cube_size // 5
                draw.ellipse([x-5, y-5, x+5, y+5], fill='red')
        
        # 添加角度标记
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), f"角度: {i*30}°", fill='black', font=font)
        
        # 保存图片
        filename = f'demo_photo_{i+1:02d}.jpg'
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, 'JPEG', quality=95)
    
    print(f"✓ 已创建 {num_images} 张演示照片")
    return output_dir

def run_demo_workflow(images_dir):
    """运行完整的演示工作流程"""
    print("\n" + "="*50)
    print("MVS Designer 演示工作流程")
    print("="*50)
    
    base_url = 'http://localhost:5000'
    
    try:
        # 1. 检查服务状态
        print("1. 检查服务状态...")
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✓ 服务运行正常")
        else:
            print("✗ 服务未运行，请先启动服务")
            return
        
        # 2. 上传照片
        print("\n2. 上传演示照片...")
        files = []
        image_files = [f for f in os.listdir(images_dir) if f.endswith('.jpg')]
        
        for img_file in image_files[:10]:  # 限制10张照片
            filepath = os.path.join(images_dir, img_file)
            files.append(('images', open(filepath, 'rb')))
        
        response = requests.post(f'{base_url}/api/upload', files=files)
        
        # 关闭文件
        for _, file_obj in files:
            file_obj.close()
        
        if response.status_code == 200:
            result = response.json()
            job_id = result['job_id']
            print(f"✓ 照片上传成功，任务ID: {job_id}")
        else:
            print(f"✗ 上传失败: {response.text}")
            return
        
        # 3. 开始重建
        print("\n3. 开始3D重建...")
        response = requests.post(f'{base_url}/api/reconstruct', 
                               json={'job_id': job_id, 'quality': 'low'})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 重建任务已启动")
            print(f"  预计耗时: {result['estimated_time']}")
        else:
            print(f"✗ 重建启动失败: {response.text}")
            return
        
        # 4. 监控进度
        print("\n4. 监控重建进度...")
        print("访问 http://localhost:5000 查看实时进度")
        print(f"或使用API: curl {base_url}/api/status/{job_id}")
        
        print("\n" + "="*50)
        print("✅ 演示工作流程启动成功！")
        print("请在Web界面中查看重建进度")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务，请确保服务正在运行")
        print("运行: python app.py")
    except Exception as e:
        print(f"✗ 演示过程出错: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='MVS Designer 演示工具')
    parser.add_argument('--create-images', action='store_true', help='创建演示照片')
    parser.add_argument('--run-demo', action='store_true', help='运行演示工作流程')
    parser.add_argument('--images-dir', default='demo_images', help='照片目录')
    
    args = parser.parse_args()
    
    if args.create_images:
        create_demo_images(args.images_dir)
    
    if args.run_demo:
        if not os.path.exists(args.images_dir):
            print(f"照片目录不存在: {args.images_dir}")
            print("先运行: python scripts/demo.py --create-images")
            return
        
        run_demo_workflow(args.images_dir)
    
    if not args.create_images and not args.run_demo:
        print("使用方法:")
        print("  创建演示照片: python scripts/demo.py --create-images")
        print("  运行演示流程: python scripts/demo.py --run-demo")
        print("  完整演示:     python scripts/demo.py --create-images --run-demo")

if __name__ == "__main__":
    main()