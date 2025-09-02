# MVS Designer Dockerfile
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
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
    libxrender-dev \
    libgomp1 \
    libglu1-mesa \
    libxi6 \
    libxmu6 \
    libgconf-2-4 \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 下载并安装Meshroom
RUN mkdir -p /opt/meshroom && \
    cd /opt/meshroom && \
    wget https://github.com/alicevision/meshroom/releases/latest/download/Meshroom-2023.3.0-linux.tar.gz && \
    tar -xzf Meshroom-2023.3.0-linux.tar.gz --strip-components=1 && \
    rm Meshroom-2023.3.0-linux.tar.gz && \
    chmod +x meshroom_batch

# 设置Meshroom环境变量
ENV PATH="/opt/meshroom:${PATH}"
ENV MESHROOM_PATH="/opt/meshroom/meshroom_batch"

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p static/{uploads,models,temp} logs

# 设置权限
RUN chmod +x app.py

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# 启动命令
CMD ["python3", "app.py"]