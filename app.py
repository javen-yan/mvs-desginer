#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MVS Designer - 多维度照片3D建模服务
基于Python和Meshroom实现的3D重建服务
"""

from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # 开发环境配置
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("=" * 50)
    print("MVS Designer - 多维度照片3D建模服务")
    print("=" * 50)
    print(f"服务地址: http://{host}:{port}")
    print(f"调试模式: {debug_mode}")
    print("API端点:")
    print("  GET  /                    - 服务信息")
    print("  POST /api/upload          - 上传照片")
    print("  POST /api/reconstruct     - 开始3D重建")
    print("  GET  /api/status/<job_id> - 查看任务状态")
    print("  GET  /api/download/<job_id> - 下载3D模型")
    print("  GET  /api/jobs            - 列出所有任务")
    print("=" * 50)
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )