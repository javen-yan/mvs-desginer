#!/bin/bash

# MVS Designer 安装脚本

set -e

echo "=================================="
echo "MVS Designer 安装脚本"
echo "=================================="

# 检查操作系统
OS=$(uname -s)
echo "操作系统: $OS"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: Python 3 未安装"
    exit 1
fi

python_version=$(python3 --version | cut -d' ' -f2)
echo "Python版本: $python_version"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "安装pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# 创建虚拟环境（推荐）
if [[ "$1" == "--venv" ]]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "虚拟环境已激活"
fi

# 安装Python依赖
echo "安装Python依赖..."
pip3 install -r requirements.txt

# 检查GPU和CUDA
if command -v nvidia-smi &> /dev/null; then
    echo "检测到NVIDIA GPU:"
    nvidia-smi --query-gpu=name --format=csv,noheader
    
    if command -v nvcc &> /dev/null; then
        cuda_version=$(nvcc --version | grep "release" | sed 's/.*release //' | sed 's/,.*//')
        echo "CUDA版本: $cuda_version"
    else
        echo "警告: CUDA未安装，GPU加速可能不可用"
    fi
else
    echo "未检测到NVIDIA GPU，将使用CPU模式"
fi

# 安装系统依赖（Ubuntu/Debian）
if command -v apt-get &> /dev/null; then
    echo "安装系统依赖..."
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        curl \
        unzip \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev
fi

# 安装Meshroom
echo "安装Meshroom..."
python3 utils/meshroom_installer.py

# 创建目录结构
echo "创建目录结构..."
mkdir -p static/{uploads,models,temp} logs

# 设置权限
chmod +x scripts/*.sh
chmod +x app.py
chmod +x test_api.py

echo "=================================="
echo "✅ 安装完成！"
echo ""
echo "启动服务:"
echo "  ./scripts/start.sh"
echo ""
echo "运行测试:"
echo "  python test_api.py --images /path/to/test/images"
echo ""
echo "访问服务:"
echo "  http://localhost:5000"
echo "=================================="