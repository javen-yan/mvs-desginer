#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MVS Designer - 多维度照片3D建模服务
基于Python和Meshroom实现的3D重建服务，支持用户认证、PostgreSQL数据库和S3存储
"""
import os
import logging
from dotenv import load_dotenv

from app import create_app

# 加载环境变量
load_dotenv()

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 环境配置
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    env = os.environ.get('FLASK_ENV', 'development')
    
    # 配置日志
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(name)s %(levelname)s: %(message)s'
    )
    
    print("=" * 60)
    print("MVS Designer - 多维度照片3D建模服务 v2.0")
    print("=" * 60)
    print(f"环境模式: {env}")
    print(f"服务地址: http://{host}:{port}")
    print(f"调试模式: {debug_mode}")
    print(f"数据库: {'已配置' if os.environ.get('DATABASE_URL') else '未配置'}")
    print(f"S3存储: {'已配置' if os.environ.get('S3_BUCKET_NAME') else '未配置'}")
    print("")
    print("新功能:")
    print("  ✓ 用户认证与授权")
    print("  ✓ PostgreSQL数据库集成")
    print("  ✓ S3对象存储支持")
    print("  ✓ 3D模型在线预览")
    print("  ✓ 用户任务管理")
    print("")
    print("API端点:")
    print("认证相关:")
    print("  POST /api/auth/register   - 用户注册")
    print("  POST /api/auth/login      - 用户登录")
    print("  POST /api/auth/logout     - 用户退出")
    print("  GET  /api/auth/profile    - 用户信息")
    print("")
    print("任务相关:")
    print("  GET  /                    - 服务信息")
    print("  POST /api/upload          - 上传照片")
    print("  POST /api/reconstruct     - 开始3D重建")
    print("  GET  /api/status/<job_id> - 查看任务状态")
    print("  GET  /api/download/<job_id> - 下载3D模型")
    print("  GET  /api/preview/<job_id> - 预览3D模型")
    print("  GET  /api/jobs            - 列出用户任务")
    print("  GET  /api/jobs/<job_id>   - 获取任务详情")
    print("  PUT  /api/jobs/<job_id>   - 更新任务信息")
    print("  DELETE /api/jobs/<job_id> - 删除任务")
    print("  GET  /api/stats           - 用户统计信息")
    print("=" * 60)
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )