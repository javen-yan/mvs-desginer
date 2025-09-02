# MVS Designer v2.0 - 多维度照片3D建模服务

## 🚀 新功能概览

MVS Designer v2.0 是一个功能全面的3D建模服务，基于Meshroom实现多维度照片的3D重建，现已集成用户认证、PostgreSQL数据库、S3对象存储和3D模型在线预览等企业级功能。

### ✨ 主要新特性

- **🔐 用户认证系统**: JWT令牌认证，支持用户注册、登录、权限管理
- **📊 PostgreSQL数据库**: 完整的数据持久化，任务状态跟踪
- **☁️ S3对象存储**: 支持AWS S3存储图片和3D模型文件
- **👁️ 3D模型预览**: 基于Three.js的在线3D模型查看器
- **👤 用户任务管理**: 用户只能访问自己创建的任务和资源
- **📈 统计面板**: 用户任务统计和进度监控
- **🐍 Pythonic代码**: 遵循Python最佳实践和类型提示

## 🏗️ 架构设计

```
MVS Designer v2.0
├── 🔐 认证层 (JWT)
├── 🌐 API层 (Flask + RESTful)
├── 💾 数据层 (PostgreSQL)
├── 📁 存储层 (本地 + S3)
├── 🔄 处理层 (Meshroom)
└── 🎨 前端层 (现代Web界面)
```

## 🗄️ 数据库模型

### User (用户表)
- 用户认证信息
- 密码哈希存储
- 用户状态管理

### ReconstructionJob (重建任务表)
- 任务状态跟踪
- 用户关联
- 文件路径管理
- S3存储信息

### JobImage (任务图片表)
- 图片元数据
- 本地和S3路径
- 图片质量信息

### UserSession (用户会话表)
- 会话管理
- 安全审计

## 🔌 API端点

### 认证相关
```
POST /api/auth/register   - 用户注册
POST /api/auth/login      - 用户登录  
POST /api/auth/logout     - 用户退出
GET  /api/auth/profile    - 获取用户信息
PUT  /api/auth/profile    - 更新用户信息
```

### 任务管理
```
POST /api/upload          - 上传照片并创建任务
POST /api/reconstruct     - 开始3D重建
GET  /api/status/<job_id> - 查看任务状态
GET  /api/jobs            - 列出用户任务 (支持分页和过滤)
GET  /api/jobs/<job_id>   - 获取任务详情
PUT  /api/jobs/<job_id>   - 更新任务信息
DELETE /api/jobs/<job_id> - 删除任务
```

### 文件和预览
```
GET  /api/download/<job_id>     - 下载3D模型
GET  /api/preview/<job_id>      - 获取预览信息
GET  /api/image/<job_id>/<name> - 获取图片文件
```

### 统计信息
```
GET  /api/stats           - 用户统计信息
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository_url>
cd mvs-designer

# 安装Python依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env
# 编辑 .env 文件配置数据库和S3
```

### 2. 数据库设置

#### 使用Docker (推荐)
```bash
# 启动PostgreSQL和Redis
docker-compose up -d postgres redis

# 等待数据库启动
sleep 10

# 初始化数据库
python scripts/init_db.py
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
python scripts/init_db.py
```

### 3. 启动服务

#### 开发模式
```bash
python app.py
```

#### Docker模式
```bash
docker-compose up -d
```

### 4. 访问服务

- Web界面: http://localhost:5000
- API文档: http://localhost:5000/ (Accept: application/json)

## 🔧 配置说明

### 环境变量配置

```bash
# Flask配置
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# 数据库配置
DATABASE_URL=postgresql://mvs_user:mvs_password@localhost:5432/mvs_designer

# S3配置 (可选)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Meshroom配置
MESHROOM_PATH=/opt/Meshroom/meshroom_batch
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
python test_api_v2.py --url http://localhost:5000 --verbose
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

## 🔒 安全特性

- **密码哈希**: 使用bcrypt安全哈希
- **JWT令牌**: 访问令牌和刷新令牌
- **权限控制**: 用户只能访问自己的资源
- **文件验证**: 严格的文件类型和大小检查
- **SQL注入防护**: 使用SQLAlchemy ORM
- **CORS配置**: 跨域请求安全控制

## 📊 监控和维护

### 数据库维护
```bash
# 数据库迁移
flask db upgrade

# 清理旧文件
python -c "from app.utils import cleanup_old_jobs; cleanup_old_jobs(app.config, days=30)"
```

### 日志监控
- 应用日志: `/app/logs/`
- 数据库日志: PostgreSQL logs
- S3访问日志: CloudTrail (如果启用)

## 🚀 部署

### Docker部署 (推荐)
```bash
# 构建和启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mvs-designer
```

### 生产环境配置

1. **环境变量设置**
   - 设置强密码和密钥
   - 配置生产数据库
   - 配置S3存储

2. **安全配置**
   - 使用HTTPS
   - 配置防火墙
   - 设置备份策略

3. **性能优化**
   - 使用Nginx反向代理
   - 配置Redis缓存
   - 启用数据库连接池

## 🔧 开发指南

### 代码规范
- 遵循PEP 8编码规范
- 使用类型提示
- 完整的文档字符串
- 异常处理和日志记录

### 添加新功能
1. 创建数据库模型 (`models.py`)
2. 实现业务逻辑 (`services/`)
3. 添加API路由 (`routes.py`)
4. 更新前端界面 (`templates/`)
5. 编写测试用例

### 数据库迁移
```bash
# 创建迁移
flask db migrate -m "描述更改"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

## 🆘 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务状态
   - 验证连接字符串
   - 检查防火墙设置

2. **S3上传失败**
   - 验证AWS凭证
   - 检查存储桶权限
   - 确认网络连接

3. **Meshroom重建失败**
   - 检查Meshroom安装
   - 验证GPU驱动
   - 查看错误日志

### 日志查看
```bash
# 应用日志
tail -f logs/app.log

# Docker日志
docker-compose logs -f mvs-designer

# 数据库日志
docker-compose logs postgres
```

## 📝 更新日志

### v2.0.0 (当前版本)
- ✅ 集成PostgreSQL数据库
- ✅ 实现用户认证系统
- ✅ 添加S3对象存储支持
- ✅ 3D模型在线预览功能
- ✅ 用户任务权限管理
- ✅ 代码重构符合Pythonic标准
- ✅ 现代化Web界面
- ✅ 完整的API文档和测试

### v1.0.0
- 基础3D重建功能
- 简单文件上传
- Meshroom集成

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 📞 支持

如有问题或建议，请创建Issue或联系开发团队。