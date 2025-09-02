#!/bin/bash

# MVS Designer 启动脚本

set -e

echo "=================================="
echo "MVS Designer 启动脚本"
echo "=================================="

# 检查Python版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python版本: $python_version"

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "虚拟环境: $VIRTUAL_ENV"
else
    echo "警告: 建议在虚拟环境中运行"
fi

# 检查依赖
echo "检查Python依赖..."
if ! pip check > /dev/null 2>&1; then
    echo "警告: 依赖检查失败，尝试安装..."
    pip install -r requirements.txt
fi

# 检查Meshroom
echo "检查Meshroom安装..."
if ! command -v meshroom_batch &> /dev/null; then
    echo "Meshroom未找到，尝试自动安装..."
    python utils/meshroom_installer.py
fi

# 创建必要目录
echo "创建目录结构..."
mkdir -p static/{uploads,models,temp} logs

# 检查GPU
if command -v nvidia-smi &> /dev/null; then
    echo "GPU状态:"
    nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits
    export USE_GPU=true
else
    echo "未检测到NVIDIA GPU，将使用CPU模式"
    export USE_GPU=false
fi

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=${FLASK_ENV:-development}

echo "=================================="
echo "启动MVS Designer服务..."
echo "访问地址: http://localhost:5000"
echo "=================================="

# 启动应用
python3 app.py