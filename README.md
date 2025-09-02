# MVS Designer v2.0 - 多维度照片3D建模服务

## 🚀 项目概览

MVS Designer v2.0 是一个功能全面的3D建模服务，基于Meshroom/AliceVision实现多维度照片的3D重建。项目采用现代化的Python架构，集成了用户认证、PostgreSQL数据库、S3对象存储和3D模型在线预览等企业级功能。

### ✨ 核心特性

- **🔐 用户认证系统**: JWT令牌认证，支持用户注册、登录、权限管理
- **📊 PostgreSQL数据库**: 完整的数据持久化，任务状态跟踪
- **☁️ S3对象存储**: 支持AWS S3存储图片和3D模型文件
- **👁️ 3D模型预览**: 基于Three.js的在线3D模型查看器
- **👤 用户任务管理**: 用户只能访问自己创建的任务和资源
- **📈 统计面板**: 用户任务统计和进度监控
- **🐍 现代化架构**: 遵循Python最佳实践，模块化设计
- **🔄 异步处理**: 基于线程的异步任务处理系统

## 🏗️ 项目架构

### 技术栈
- **后端框架**: Flask 2.3.3 + SQLAlchemy 2.0
- **数据库**: PostgreSQL + Flask-Migrate
- **认证**: JWT + Flask-JWT-Extended
- **存储**: 本地文件系统 + AWS S3
- **3D处理**: Meshroom/AliceVision
- **前端**: HTML5 + CSS3 + JavaScript (Three.js)

### 架构层次
```
MVS Designer v2.0
├── 🔐 认证层 (JWT + 用户管理)
├── 🌐 API层 (Flask Blueprints + RESTful)
├── 💾 数据层 (PostgreSQL + SQLAlchemy ORM)
├── 📁 存储层 (本地文件 + S3对象存储)
├── 🔄 处理层 (Meshroom + 异步任务)
└── 🎨 前端层 (现代Web界面 + 3D预览)
```

## 📁 项目结构

```
mvs-designer/
├── app/                          # 主应用模块
│   ├── __init__.py              # 应用工厂
│   ├── factory.py               # 应用创建工厂
│   ├── models.py                # 数据库模型
│   ├── auth.py                  # 认证服务
│   ├── extensions.py            # Flask扩展
│   ├── logger.py                # 日志配置
│   ├── utils.py                 # 工具函数
│   ├── blueprints/              # 蓝图模块
│   │   ├── api.py              # API路由
│   │   ├── auth.py             # 认证路由
│   │   └── main.py             # 主页面路由
│   ├── services/                # 业务服务
│   │   ├── job_service.py      # 任务管理服务
│   │   ├── meshroom_service.py # Meshroom集成服务
│   │   ├── s3_service.py       # S3存储服务
│   │   └── manager.py          # 任务管理器
│   ├── middleware/              # 中间件
│   │   ├── auth.py             # 认证中间件
│   │   └── validation.py       # 验证中间件
│   └── config/                  # 配置模块
├── static/                      # 静态文件
│   ├── uploads/                # 用户上传文件
│   ├── models/                 # 生成的3D模型
│   └── temp/                   # 临时文件
├── templates/                   # HTML模板
├── migrations/                  # 数据库迁移
├── docker/                      # Docker配置
├── scripts/                     # 脚本工具
├── app.py                       # 应用入口
├── requirements.txt             # Python依赖
└── .env.example                 # 环境变量模板
```

## 🗄️ 数据库模型

### User (用户表)
- 用户认证信息 (username, email, password_hash)
- 用户状态管理 (is_active, created_at, updated_at)
- 与任务的一对多关系

### ReconstructionJob (重建任务表)
- 任务基本信息 (title, description, status)
- 用户关联 (user_id)
- 处理参数 (quality, preset)
- 文件路径管理 (input_path, output_path)
- S3存储信息 (s3_bucket, s3_key)
- 时间戳 (created_at, updated_at, completed_at)

### JobImage (任务图片表)
- 图片元数据 (filename, file_size, mime_type)
- 本地和S3路径 (local_path, s3_key)
- 图片质量信息 (width, height, exif_data)
- 与任务的多对一关系

### UserSession (用户会话表)
- 会话管理 (session_token, expires_at)
- 安全审计 (ip_address, user_agent)
- 与用户的关联

## 🔌 API接口

### 认证相关 (`/api/auth/`)
```
POST /api/auth/register   - 用户注册
POST /api/auth/login      - 用户登录  
POST /api/auth/logout     - 用户退出
GET  /api/auth/profile    - 获取用户信息
PUT  /api/auth/profile    - 更新用户信息
```

### 任务管理 (`/api/`)
```
POST /api/upload          - 上传照片并创建任务
POST /api/reconstruct     - 开始3D重建
GET  /api/status/<job_id> - 查看任务状态
GET  /api/jobs            - 列出用户任务 (支持分页和过滤)
GET  /api/jobs/<job_id>   - 获取任务详情
PUT  /api/jobs/<job_id>   - 更新任务信息
DELETE /api/jobs/<job_id> - 删除任务
```

### 文件和预览 (`/api/`)
```
GET  /api/download/<job_id>     - 下载3D模型
GET  /api/preview/<job_id>      - 获取预览信息
GET  /api/image/<job_id>/<name> - 获取图片文件
```

### 统计信息 (`/api/`)
```
GET  /api/stats           - 用户统计信息
```

### 主页面 (`/`)
```
GET  /                    - Web界面首页
GET  /health              - 健康检查
```

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.7+ (推荐 3.9+)
- **数据库**: PostgreSQL 12+
- **内存**: 8GB+ RAM
- **存储**: 20GB+ 可用空间
- **GPU**: NVIDIA GPU (可选，但强烈推荐用于加速)

### 2. 安装步骤

```bash
# 克隆项目
git clone <repository_url>
cd mvs-designer

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env
# 编辑 .env 文件配置数据库和S3
```

### 3. 数据库设置

#### 使用Docker (推荐)
```bash
# 启动PostgreSQL
docker-compose up -d postgres

# 等待数据库启动
sleep 10

# 初始化数据库
python app.py --init-db
```

#### 手动安装PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib libpq-dev

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE mvs_designer;
CREATE USER mvs_user WITH PASSWORD 'mvs_password';
GRANT ALL PRIVILEGES ON DATABASE mvs_designer TO mvs_user;
\q

# 初始化数据库
python app.py --init-db
```

### 4. 启动服务

#### 开发模式
```bash
# 启动Web服务器
python app.py --server

# 或直接运行 (默认启动服务器)
python app.py
```

#### Docker模式
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 5. 访问服务

- **Web界面**: http://localhost:5000
- **API接口**: http://localhost:5000/api/
- **健康检查**: http://localhost:5000/health

## 🔧 配置说明

### 环境变量配置 (`.env` 文件)

```bash
# Flask应用配置
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://mvs_user:mvs_password@localhost:5432/mvs_designer

# S3存储配置 (可选)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
USE_S3_STORAGE=false

# Meshroom配置
MESHROOM_PATH=/opt/Meshroom/meshroom_batch
MESHROOM_CACHE_PATH=/tmp/meshroom_cache

# 服务器配置
HOST=0.0.0.0
PORT=5000
MAX_CONTENT_LENGTH=104857600  # 100MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### S3存储配置

1. 创建S3存储桶
2. 配置IAM用户权限
3. 设置环境变量
4. 重启应用

存储结构:
```
s3://your-bucket/
├── jobs/
│   └── <job_id>/
│       ├── images/
│       │   ├── image1.jpg
│       │   └── image2.jpg
│       └── models/
│           └── model.obj
```

## 🧪 测试

### 运行API测试
```bash
# 运行完整的API测试套件
python test_api_v2.py --url http://localhost:5000 --verbose

# 运行特定测试
python test_api_v2.py --url http://localhost:5000 --test auth
python test_api_v2.py --url http://localhost:5000 --test upload
```

### 手动测试流程

1. **用户注册**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123456"}'
```

2. **用户登录**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123456"}'
```

3. **上传图片**
```bash
curl -X POST http://localhost:5000/api/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=测试任务" \
  -F "description=API测试" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.jpg"
```

4. **开始3D重建**
```bash
curl -X POST http://localhost:5000/api/reconstruct \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"YOUR_JOB_ID","quality":"medium"}'
```

5. **查询任务状态**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/status/YOUR_JOB_ID
```

## 🔒 安全特性

- **密码安全**: 使用bcrypt进行密码哈希存储
- **JWT认证**: 基于JWT的访问令牌和会话管理
- **权限控制**: 用户只能访问自己创建的任务和资源
- **文件验证**: 严格的文件类型、大小和内容检查
- **SQL注入防护**: 使用SQLAlchemy ORM防止SQL注入
- **CORS配置**: 跨域请求安全控制
- **输入验证**: 使用Pydantic进行数据验证
- **路径安全**: 防止路径遍历攻击
- **会话管理**: 安全的用户会话和令牌管理

## 📊 监控和维护

### 数据库维护
```bash
# 运行数据库迁移
python app.py --migrate

# 初始化数据库
python app.py --init-db

# 清理旧文件 (通过API或管理脚本)
curl -X DELETE http://localhost:5000/api/cleanup/old-jobs
```

### 日志监控
- **应用日志**: `logs/app.log`
- **错误日志**: `logs/error.log`
- **访问日志**: `logs/access.log`
- **数据库日志**: PostgreSQL logs
- **S3访问日志**: CloudTrail (如果启用)

### 性能监控
- **任务处理时间**: 通过API统计接口查看
- **资源使用**: CPU、内存、GPU使用情况
- **存储使用**: 磁盘空间和S3存储使用量
- **并发任务**: 当前运行的任务数量

## 🚀 部署

### Docker部署 (推荐)
```bash
# 构建和启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mvs-designer

# 停止服务
docker-compose down
```

### 生产环境配置

1. **环境变量设置**
   - 设置强密码和密钥
   - 配置生产数据库连接
   - 配置S3存储凭证
   - 设置日志级别为INFO或WARNING

2. **安全配置**
   - 使用HTTPS (配置SSL证书)
   - 配置防火墙规则
   - 设置定期备份策略
   - 启用访问日志记录

3. **性能优化**
   - 使用Nginx反向代理
   - 配置Gunicorn WSGI服务器
   - 启用数据库连接池
   - 配置Redis缓存 (可选)
   - 使用CDN加速静态文件

## 🔧 开发指南

### 代码规范
- 遵循PEP 8编码规范
- 使用类型提示 (Type Hints)
- 完整的文档字符串 (Docstrings)
- 异常处理和日志记录
- 使用Black代码格式化工具

### 项目结构说明
- **`app/blueprints/`**: API路由和视图函数
- **`app/services/`**: 业务逻辑和服务层
- **`app/models.py`**: 数据库模型定义
- **`app/middleware/`**: 中间件和装饰器
- **`app/config/`**: 配置管理
- **`static/`**: 静态文件和用户上传
- **`templates/`**: HTML模板文件

### 添加新功能
1. 创建数据库模型 (`app/models.py`)
2. 实现业务逻辑 (`app/services/`)
3. 添加API路由 (`app/blueprints/`)
4. 更新前端界面 (`templates/`)
5. 编写测试用例
6. 更新文档

### 数据库迁移
```bash
# 创建迁移文件
flask db migrate -m "描述更改"

# 应用迁移
python app.py --migrate

# 回滚迁移 (如果需要)
flask db downgrade
```

## 🆘 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查PostgreSQL服务状态
   docker-compose ps postgres
   
   # 验证连接字符串
   echo $DATABASE_URL
   
   # 测试数据库连接
   python -c "from app import create_app; app = create_app(); print('DB OK')"
   ```

2. **S3上传失败**
   ```bash
   # 验证AWS凭证
   aws s3 ls
   
   # 检查存储桶权限
   aws s3 ls s3://your-bucket-name
   
   # 确认网络连接
   ping s3.amazonaws.com
   ```

3. **Meshroom重建失败**
   ```bash
   # 检查Meshroom安装
   which meshroom_batch
   
   # 验证GPU驱动
   nvidia-smi
   
   # 查看错误日志
   tail -f logs/app.log
   ```

4. **应用启动失败**
   ```bash
   # 检查Python依赖
   pip list
   
   # 检查环境变量
   cat .env
   
   # 查看详细错误
   python app.py --server
   ```

### 日志查看
```bash
# 应用日志
tail -f logs/app.log

# 错误日志
tail -f logs/error.log

# Docker日志
docker-compose logs -f mvs-designer

# 数据库日志
docker-compose logs postgres
```

## 📝 更新日志

### v2.0.0 (当前版本)
- ✅ **数据库集成**: PostgreSQL + SQLAlchemy ORM
- ✅ **用户认证**: JWT令牌认证系统
- ✅ **权限管理**: 用户只能访问自己的任务
- ✅ **S3存储**: AWS S3对象存储支持
- ✅ **3D预览**: 基于Three.js的在线模型查看器
- ✅ **现代化架构**: Flask Blueprints + 服务层设计
- ✅ **API完善**: RESTful API + 完整文档
- ✅ **安全增强**: 密码哈希、输入验证、路径安全
- ✅ **日志系统**: 结构化日志记录
- ✅ **Docker支持**: 容器化部署配置

### v1.0.0
- 基础3D重建功能
- 简单文件上传
- Meshroom集成
- 基础Web界面

## 🤝 贡献指南

1. **Fork项目** - 在GitHub上fork本项目
2. **创建分支** - 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. **提交更改** - 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. **推送分支** - 推送到分支 (`git push origin feature/AmazingFeature`)
5. **创建PR** - 创建Pull Request

### 开发环境设置
```bash
# 克隆你的fork
git clone https://github.com/your-username/mvs-designer.git
cd mvs-designer

# 添加上游仓库
git remote add upstream https://github.com/original-owner/mvs-designer.git

# 创建开发分支
git checkout -b development
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 支持

- **问题反馈**: [GitHub Issues](https://github.com/your-repo/mvs-designer/issues)
- **功能建议**: [GitHub Discussions](https://github.com/your-repo/mvs-designer/discussions)
- **技术文档**: 查看 `docs/` 目录下的详细文档

## 🙏 致谢

- [AliceVision](https://alicevision.org/) - 开源摄影测量框架
- [Meshroom](https://alicevision.org/#meshroom) - 3D重建软件
- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [Three.js](https://threejs.org/) - 3D JavaScript库

---

**MVS Designer v2.0** - 让3D建模变得简单而强大 🚀
