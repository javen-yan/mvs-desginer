#!/bin/bash
# MVS Designer v2.0 启动脚本

set -e

echo "=================================="
echo "MVS Designer v2.0 启动脚本"
echo "=================================="

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python版本: $python_version"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "错误: 需要Python 3.8或更高版本"
    exit 1
fi

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 检查环境配置文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "创建.env配置文件..."
        cp .env.example .env
        echo "⚠️  请编辑.env文件配置您的数据库和S3设置"
    else
        echo "⚠️  未找到.env.example文件"
    fi
fi

# 检查PostgreSQL连接
echo "检查数据库连接..."
if python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

try:
    import psycopg2
    conn_str = os.environ.get('DATABASE_URL', 'postgresql://mvs_user:mvs_password@localhost:5432/mvs_designer')
    conn = psycopg2.connect(conn_str)
    conn.close()
    print('✓ 数据库连接成功')
except Exception as e:
    print(f'⚠️  数据库连接失败: {e}')
    print('请确保PostgreSQL正在运行并且配置正确')
"; then
    echo "数据库连接正常"
else
    echo "数据库连接有问题，但服务仍可启动"
fi

# 初始化数据库
echo "初始化数据库..."
python scripts/init_db.py

echo "=================================="
echo "启动MVS Designer服务..."
echo "=================================="

# 启动应用
python app.py