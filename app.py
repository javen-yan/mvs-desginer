#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from app import create_app
from app.logger import setup_logging
from app.config import Config

# 设置日志系统
config = Config()
logger = setup_logging(config.LOG)

def run_server():
    app = create_app()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )

def run_migrations():
    """运行数据库迁移"""
    try:
        import subprocess
        
        logger.info("开始运行数据库迁移")
        
        # 确保在项目根目录
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        print("正在运行数据库迁移...")
        logger.info(f"工作目录: {project_root}")
        
        # 设置环境变量
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.factory:create_app'
        
        # 运行 Alembic 升级命令
        result = subprocess.run([
            sys.executable, '-m', 'flask', 'db', 'upgrade'
        ], capture_output=True, text=True, cwd=project_root, env=env)
        
        if result.returncode == 0:
            print("✅ 数据库迁移完成")
            logger.info("数据库迁移成功完成")
            if result.stdout:
                print(result.stdout)
                logger.debug(f"迁移输出: {result.stdout}")
        else:
            print("❌ 数据库迁移失败")
            logger.error("数据库迁移失败")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
                logger.error(f"迁移错误: {result.stderr}")
            if result.stdout:
                print(f"输出信息: {result.stdout}")
                logger.debug(f"迁移输出: {result.stdout}")
            sys.exit(1)
            
    except Exception as e:
        error_msg = f"运行迁移时发生错误: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        sys.exit(1)

def run_init_db():
    """运行初始化数据库"""
    try:
        from app import create_app
        from app.models import db, User
        app = create_app()
        with app.app_context():
            db.create_all()
            logger.info("数据库初始化完成")
            # Create sample admin user
            admin_user = User(
                username='admin',
                email='admin@mvs-designer.com',
                password='admin123456'
            )
            db.session.add(admin_user)
            db.session.commit()
            logger.info("创建管理员用户完成")

    except Exception as e:
        error_msg = f"运行初始化数据库时发生错误: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        sys.exit(1)


def show_help():
    """显示帮助信息"""
    help_text = """
MVS Designer - 多维度照片3D建模服务

用法:
    python app.py [选项]

选项:
    --server     启动 Web 服务器
    --migrate    运行数据库迁移
    --help       显示此帮助信息

示例:
    python app.py --server    # 启动服务器
    python app.py --migrate   # 运行数据库迁移
    python app.py --init-db   # 初始化数据库
    python app.py --help      # 显示帮助

环境变量:
    确保已正确配置 .env 文件中的数据库连接信息
    """
    print(help_text)


if __name__ == '__main__':
    """
    MVS Designer 主入口点
    
    支持的命令:
    --server  启动 Web 服务器
    --migrate 执行数据库迁移
    --init-db 初始化数据库
    --help    显示帮助信息
    """
    try:
        logger.info(f"启动 MVS Designer，参数: {sys.argv}")
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            logger.info(f"执行命令: {command}")
            
            if command == '--server':
                print("🚀 启动 MVS Designer 服务器...")
                logger.info("启动 Web 服务器")
                run_server()
            elif command == '--migrate':
                logger.info("执行数据库迁移")
                run_migrations()
            elif command == '--init-db':
                logger.info("初始化数据库")
                run_init_db()
            elif command == '--help':
                logger.info("显示帮助信息")
                show_help()
            else:
                error_msg = f"未知命令: {command}"
                print(f"❌ {error_msg}")
                print("使用 --help 查看可用命令")
                logger.error(error_msg)
                sys.exit(1)
        else:
            print("❌ 请指定一个命令")
            logger.warning("未指定命令参数")
            show_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
        logger.info("程序被用户中断 (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        error_msg = f"程序执行出错: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        sys.exit(1)