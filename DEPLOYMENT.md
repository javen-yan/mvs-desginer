# MVS Designer v2.0 部署指南

## 🚀 部署选项

### 1. Docker部署 (推荐)

#### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (如果使用GPU)

#### 快速部署
```bash
# 1. 克隆项目
git clone <repository_url>
cd mvs-designer

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 初始化数据库
docker-compose exec mvs-designer python scripts/init_db.py

# 6. 访问服务
open http://localhost
```

#### 生产环境配置
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  mvs-designer:
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME}
```

### 2. 手动部署

#### 系统要求
- Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Python 3.8+
- PostgreSQL 12+
- Nginx (可选)
- CUDA 11.8+ (如果使用GPU)

#### 安装步骤

1. **安装系统依赖**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib libpq-dev \
    nginx git curl wget

# CentOS/RHEL
sudo yum install -y python3 python3-pip \
    postgresql postgresql-server postgresql-devel \
    nginx git curl wget
```

2. **设置PostgreSQL**
```bash
# 启动PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE mvs_designer;
CREATE USER mvs_user WITH PASSWORD 'mvs_password';
GRANT ALL PRIVILEGES ON DATABASE mvs_designer TO mvs_user;
ALTER USER mvs_user CREATEDB;
\q
EOF
```

3. **部署应用**
```bash
# 创建应用用户
sudo useradd -m -s /bin/bash mvs-designer
sudo su - mvs-designer

# 克隆代码
git clone <repository_url> /home/mvs-designer/app
cd /home/mvs-designer/app

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env 文件

# 初始化数据库
python scripts/setup.py
```

4. **配置系统服务**
```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/mvs-designer.service << EOF
[Unit]
Description=MVS Designer 3D Reconstruction Service
After=network.target postgresql.service

[Service]
Type=simple
User=mvs-designer
WorkingDirectory=/home/mvs-designer/app
Environment=PATH=/home/mvs-designer/app/venv/bin
ExecStart=/home/mvs-designer/app/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start mvs-designer
sudo systemctl enable mvs-designer
```

5. **配置Nginx反向代理**
```nginx
# /etc/nginx/sites-available/mvs-designer
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 500M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /static/ {
        alias /home/mvs-designer/app/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/mvs-designer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 配置优化

### 数据库优化
```sql
-- PostgreSQL优化配置
-- /etc/postgresql/13/main/postgresql.conf

shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 应用性能优化
```python
# config.py 生产环境配置
class ProductionConfig(Config):
    # 数据库连接池
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30
    }
    
    # 文件上传限制
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB
```

## 🔐 安全配置

### SSL/TLS配置
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # 其他配置...
}
```

### 防火墙配置
```bash
# Ubuntu UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 📊 监控和日志

### 应用监控
```bash
# 系统资源监控
htop
iotop
nvidia-smi  # GPU监控

# 应用状态
sudo systemctl status mvs-designer
sudo journalctl -u mvs-designer -f

# 数据库监控
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

### 日志轮转
```bash
# /etc/logrotate.d/mvs-designer
/home/mvs-designer/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 mvs-designer mvs-designer
    postrotate
        sudo systemctl reload mvs-designer
    endscript
}
```

## 🔄 备份和恢复

### 数据库备份
```bash
# 创建备份脚本
cat > /home/mvs-designer/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/mvs-designer/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -h localhost -U mvs_user mvs_designer | gzip > $BACKUP_DIR/mvs_designer_$DATE.sql.gz

# 保留最近30天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x /home/mvs-designer/backup_db.sh

# 添加到crontab
echo "0 2 * * * /home/mvs-designer/backup_db.sh" | crontab -
```

### 文件备份
```bash
# S3同步备份
aws s3 sync /home/mvs-designer/app/static/ s3://your-backup-bucket/static/
```

## 🚨 故障排除

### 常见问题解决

1. **服务无法启动**
```bash
# 检查日志
sudo journalctl -u mvs-designer -n 50

# 检查端口占用
sudo netstat -tlnp | grep :5000

# 检查文件权限
ls -la /home/mvs-designer/app/
```

2. **数据库连接问题**
```bash
# 测试数据库连接
psql -h localhost -U mvs_user -d mvs_designer -c "SELECT version();"

# 检查PostgreSQL状态
sudo systemctl status postgresql

# 查看PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

3. **GPU相关问题**
```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查CUDA
nvcc --version

# 检查Docker GPU支持
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

## 📈 性能调优

### 数据库调优
```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_jobs_user_status ON reconstruction_jobs(user_id, status);
CREATE INDEX CONCURRENTLY idx_jobs_created_at ON reconstruction_jobs(created_at DESC);
CREATE INDEX CONCURRENTLY idx_images_job_id ON job_images(job_id);

-- 分析表统计信息
ANALYZE;
```

### 应用调优
```python
# 使用连接池
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 20,
    'max_overflow': 30,
    'pool_pre_ping': True,
    'pool_recycle': 3600
}
```

## 🔄 更新和维护

### 应用更新
```bash
# 备份当前版本
sudo systemctl stop mvs-designer
cp -r /home/mvs-designer/app /home/mvs-designer/app.backup

# 更新代码
cd /home/mvs-designer/app
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 数据库迁移
flask db upgrade

# 重启服务
sudo systemctl start mvs-designer
```

### 定期维护
```bash
# 清理旧文件 (每周执行)
python3 -c "
from app import create_app
from app.utils import cleanup_old_jobs
app = create_app()
with app.app_context():
    result = cleanup_old_jobs(app.config, days=30)
    print(f'清理完成: {result}')
"

# 数据库维护 (每月执行)
sudo -u postgres psql mvs_designer -c "VACUUM ANALYZE;"
```

## 📞 技术支持

### 日志收集
```bash
# 收集系统信息
echo "=== 系统信息 ===" > debug_info.txt
uname -a >> debug_info.txt
python3 --version >> debug_info.txt
docker --version >> debug_info.txt

echo "=== 服务状态 ===" >> debug_info.txt
sudo systemctl status mvs-designer >> debug_info.txt
sudo systemctl status postgresql >> debug_info.txt

echo "=== 应用日志 ===" >> debug_info.txt
tail -n 100 /home/mvs-designer/app/logs/app.log >> debug_info.txt

echo "=== 数据库状态 ===" >> debug_info.txt
sudo -u postgres psql mvs_designer -c "SELECT COUNT(*) FROM users;" >> debug_info.txt
sudo -u postgres psql mvs_designer -c "SELECT COUNT(*) FROM reconstruction_jobs;" >> debug_info.txt
```

如需技术支持，请提供上述调试信息。