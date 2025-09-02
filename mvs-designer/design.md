# MVS Designer - 多维度照片3D建模服务设计文档

## 项目概述

MVS Designer 是一个基于 Python 和 Meshroom 实现的多维度照片3D建模服务。用户可以通过上传上下前后左右等多个角度的照片，使用 Meshroom 的摄影测量技术生成高质量的3D模型。

### 核心功能
- 多角度照片上传和验证
- 基于Meshroom的自动化3D重建
- 实时任务状态监控
- 3D模型下载和管理
- Web界面和RESTful API

## 技术架构

### 技术栈选择

**后端技术:**
- **Python 3.7+**: 主要开发语言
- **Flask**: Web框架，轻量级且易于扩展
- **Meshroom/AliceVision**: 开源摄影测量软件，用于3D重建
- **OpenCV & Pillow**: 图像处理和验证
- **Threading**: 异步任务处理

**前端技术:**
- **HTML5/CSS3/JavaScript**: 现代Web界面
- **原生JavaScript**: 避免额外依赖，提高性能

**部署技术:**
- **Docker**: 容器化部署，包含GPU支持
- **NVIDIA CUDA**: GPU加速处理

### 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Flask API     │    │   Meshroom      │
│                 │    │                 │    │   Engine        │
│ - Upload UI     │────│ - File Upload   │────│ - 3D Recon     │
│ - Progress      │    │ - Job Manager   │    │ - Pipeline      │
│ - Download      │    │ - Status API    │    │ - Export        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   Job Status    │    │   3D Models     │
│                 │    │   Management    │    │   Storage       │
│ - Uploads/      │    │                 │    │                 │
│ - Temp/         │    │ - Progress      │    │ - .obj files    │
│ - Models/       │    │ - Metadata      │    │ - Textures      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 详细设计

### 1. 文件结构

```
mvs-designer/
├── app/                    # 主应用模块
│   ├── __init__.py        # Flask应用工厂
│   ├── routes.py          # API路由定义
│   ├── meshroom_service.py # Meshroom集成服务
│   └── utils.py           # 工具函数
├── config/                # 配置文件
│   └── settings.py        # 应用配置
├── utils/                 # 工具模块
│   ├── image_processor.py # 图像处理工具
│   └── meshroom_installer.py # Meshroom安装工具
├── static/                # 静态文件
│   ├── uploads/           # 上传的照片
│   ├── models/            # 生成的3D模型
│   └── temp/              # 临时处理文件
├── templates/             # HTML模板
│   └── index.html         # 主界面
├── docker/                # Docker配置
│   └── Dockerfile         # 容器配置
├── docs/                  # 文档目录
├── app.py                 # 应用入口
├── requirements.txt       # Python依赖
├── test_api.py           # API测试脚本
└── design.md             # 设计文档
```

### 2. API接口设计

#### 2.1 服务信息
```
GET /
返回服务基本信息和可用端点
```

#### 2.2 照片上传
```
POST /api/upload
Content-Type: multipart/form-data
Body: images (multiple files)

Response:
{
  "job_id": "uuid",
  "uploaded_files": ["file1.jpg", "file2.jpg"],
  "message": "成功上传N张照片"
}
```

#### 2.3 开始3D重建
```
POST /api/reconstruct
Content-Type: application/json
Body: {
  "job_id": "uuid",
  "quality": "medium",  // low, medium, high
  "preset": "default"   // default, fast, detailed
}

Response:
{
  "job_id": "uuid",
  "status": "started",
  "estimated_time": "10-30分钟"
}
```

#### 2.4 查询任务状态
```
GET /api/status/<job_id>

Response:
{
  "status": "running",      // initializing, running, completed, failed
  "progress": 45,           // 0-100
  "message": "正在进行3D重建...",
  "start_time": "2024-01-01T10:00:00",
  "estimated_time": "15分钟"
}
```

#### 2.5 下载3D模型
```
GET /api/download/<job_id>
返回3D模型文件 (.obj格式)
```

#### 2.6 任务列表
```
GET /api/jobs
返回所有任务的状态列表
```

### 3. Meshroom集成方案

#### 3.1 Meshroom工作流程
1. **特征提取 (Feature Extraction)**: 从每张照片中提取SIFT特征点
2. **特征匹配 (Feature Matching)**: 在不同照片间匹配相同的特征点
3. **结构恢复 (Structure from Motion)**: 计算相机位置和稀疏点云
4. **深度图生成 (Depth Map Generation)**: 为每张照片生成深度图
5. **网格重建 (Meshing)**: 从深度图生成3D网格
6. **纹理映射 (Texturing)**: 将照片纹理映射到3D模型

#### 3.2 命令行集成
```python
# 基本Meshroom命令
meshroom_batch --input /path/to/images --output /path/to/output

# 带参数的命令
meshroom_batch \
  --input /path/to/images \
  --output /path/to/output \
  --cache /path/to/cache \
  --preset detailed \
  --verbose info
```

#### 3.3 质量预设配置

| 质量级别 | Meshroom预设 | 处理时间 | 适用场景 |
|---------|-------------|---------|---------|
| Low     | draft       | 快速     | 预览测试 |
| Medium  | default     | 中等     | 日常使用 |
| High    | detailed    | 较长     | 专业用途 |

### 4. 图像处理流程

#### 4.1 照片验证标准
- **数量要求**: 最少3张，建议10-50张
- **分辨率要求**: 最低800x600，建议2MP以上
- **格式支持**: JPEG, PNG, TIFF, BMP
- **质量检查**: 检测模糊、过曝、损坏等问题

#### 4.2 预处理步骤
1. **格式标准化**: 转换为RGB模式
2. **尺寸优化**: 大图片适当缩放
3. **质量增强**: 调整对比度和锐度
4. **EXIF提取**: 获取相机参数信息

### 5. 任务管理系统

#### 5.1 任务状态流转
```
initializing → running → completed
     ↓              ↓
   failed        failed
```

#### 5.2 状态存储
- 内存存储任务状态（生产环境可扩展为Redis）
- 文件系统存储任务数据和结果
- JSON格式的元数据文件

### 6. 文件管理策略

#### 6.1 目录结构
```
static/
├── uploads/           # 用户上传的照片
│   └── <job_id>/     # 按任务ID分组
├── temp/             # Meshroom临时文件
│   └── <job_id>/     # 处理过程文件
└── models/           # 生成的3D模型
    └── <job_id>/     # 模型文件和元数据
```

#### 6.2 清理策略
- 自动清理7天前的旧任务文件
- 支持手动清理指定任务
- 保留模型文件供下载

## 部署方案

### 1. 本地开发部署

#### 环境要求
- Python 3.7+
- NVIDIA GPU (推荐)
- CUDA 11.0+ (GPU加速)
- 8GB+ RAM
- 20GB+ 磁盘空间

#### 安装步骤
```bash
# 1. 克隆项目
git clone <repository>
cd mvs-designer

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 安装Meshroom
python utils/meshroom_installer.py

# 4. 启动服务
python app.py
```

### 2. Docker部署

```bash
# 构建镜像
docker build -t mvs-designer -f docker/Dockerfile .

# 运行容器（GPU支持）
docker run --gpus all -p 5000:5000 -v $(pwd)/data:/app/static mvs-designer
```

### 3. 生产环境部署

#### 推荐配置
- **服务器**: NVIDIA GPU服务器
- **操作系统**: Ubuntu 20.04 LTS
- **Web服务器**: Nginx + Gunicorn
- **容器编排**: Docker Compose 或 Kubernetes
- **存储**: 高性能SSD存储
- **监控**: 日志记录和性能监控

## 性能优化

### 1. 处理性能
- **GPU加速**: 利用CUDA加速Meshroom处理
- **并行处理**: 支持多任务并行执行
- **内存管理**: 合理控制内存使用
- **缓存策略**: 复用中间处理结果

### 2. 用户体验
- **异步处理**: 后台处理，不阻塞用户界面
- **实时反馈**: 进度条和状态更新
- **错误处理**: 友好的错误提示和恢复机制
- **文件预览**: 上传照片的缩略图预览

## 安全考虑

### 1. 文件安全
- **文件类型验证**: 严格限制上传文件类型
- **文件大小限制**: 防止恶意大文件上传
- **路径安全**: 防止路径遍历攻击
- **病毒扫描**: 可选的文件安全检查

### 2. 资源保护
- **请求限制**: 防止API滥用
- **任务队列**: 限制并发处理数量
- **超时机制**: 防止长时间占用资源
- **资源清理**: 定期清理临时文件

## 扩展方案

### 1. 功能扩展
- **多种输出格式**: 支持PLY, STL, FBX等格式
- **模型后处理**: 网格简化、纹理优化
- **批量处理**: 支持多个项目并行处理
- **云存储集成**: 支持AWS S3, 阿里云OSS等

### 2. 集成扩展
- **数据库支持**: PostgreSQL/MongoDB存储任务数据
- **消息队列**: Redis/RabbitMQ处理异步任务
- **微服务架构**: 拆分为多个独立服务
- **API网关**: 统一接口管理和认证

## 测试方案

### 1. 单元测试
- 图像处理模块测试
- Meshroom服务集成测试
- API接口功能测试

### 2. 集成测试
- 完整工作流程测试
- 错误处理和恢复测试
- 性能压力测试

### 3. 用户验收测试
- 不同质量照片的重建效果
- 各种拍摄场景的适应性
- 用户界面易用性测试

## 使用指南

### 1. 照片拍摄建议

#### 最佳实践
- **拍摄角度**: 围绕物体360度拍摄，包括俯视和仰视角度
- **照片数量**: 建议15-50张，复杂物体可增加到100张
- **重叠度**: 相邻照片重叠60-80%
- **光照条件**: 均匀柔和的光线，避免强烈阴影
- **背景选择**: 简洁的背景，避免反光表面

#### 拍摄参数
- **分辨率**: 建议2MP以上 (1920x1080+)
- **焦距**: 固定焦距，避免变焦
- **曝光**: 手动模式，保持一致的曝光参数
- **对焦**: 确保主体清晰对焦

### 2. API使用示例

#### Python客户端示例
```python
import requests
import time

# 1. 上传照片
files = [('images', open(f'photo_{i}.jpg', 'rb')) for i in range(1, 11)]
response = requests.post('http://localhost:5000/api/upload', files=files)
job_id = response.json()['job_id']

# 2. 开始重建
requests.post('http://localhost:5000/api/reconstruct', 
              json={'job_id': job_id, 'quality': 'medium'})

# 3. 监控进度
while True:
    status = requests.get(f'http://localhost:5000/api/status/{job_id}').json()
    print(f"进度: {status['progress']}% - {status['message']}")
    
    if status['status'] == 'completed':
        break
    elif status['status'] == 'failed':
        print(f"重建失败: {status['message']}")
        break
    
    time.sleep(30)

# 4. 下载模型
response = requests.get(f'http://localhost:5000/api/download/{job_id}')
with open('model.obj', 'wb') as f:
    f.write(response.content)
```

### 3. 质量优化建议

#### 照片质量优化
- 使用三脚架保持稳定
- 避免运动模糊
- 确保充足的光线
- 避免过度曝光或欠曝光

#### 重建参数调优
- **快速预览**: 使用low质量，快速查看效果
- **日常使用**: 使用medium质量，平衡效果和速度
- **专业用途**: 使用high质量，获得最佳效果

## 故障排除

### 1. 常见问题

#### Meshroom安装问题
- **GPU驱动**: 确保安装最新的NVIDIA驱动
- **CUDA版本**: 检查CUDA版本兼容性
- **权限问题**: 确保有执行权限

#### 重建质量问题
- **照片不足**: 增加照片数量
- **重叠度不够**: 提高相邻照片重叠度
- **光照不均**: 改善拍摄光照条件
- **背景复杂**: 简化拍摄背景

#### 性能问题
- **内存不足**: 减少并发任务数量
- **磁盘空间**: 清理旧的任务文件
- **GPU占用**: 监控GPU使用情况

### 2. 错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|---------|
| 400 | 请求参数错误 | 检查API参数格式 |
| 404 | 任务不存在 | 确认job_id正确 |
| 413 | 文件过大 | 减少文件大小或数量 |
| 500 | 服务器内部错误 | 检查日志，重启服务 |

## 监控和日志

### 1. 日志记录
- **访问日志**: 记录所有API请求
- **错误日志**: 记录异常和错误信息
- **性能日志**: 记录处理时间和资源使用

### 2. 监控指标
- **任务成功率**: 重建任务的成功比例
- **平均处理时间**: 不同质量级别的处理时间
- **资源使用**: CPU, GPU, 内存使用情况
- **存储使用**: 磁盘空间使用情况

## 版本历史

### v1.0.0 (当前版本)
- ✅ 基本的多角度照片上传功能
- ✅ Meshroom集成和3D重建
- ✅ Web界面和RESTful API
- ✅ 任务状态监控
- ✅ 3D模型下载
- ✅ Docker部署支持

### 未来版本规划

#### v1.1.0
- [ ] 数据库集成（PostgreSQL）
- [ ] 用户认证和权限管理
- [ ] 批量处理支持
- [ ] 模型预览功能

#### v1.2.0
- [ ] 云存储集成
- [ ] 微服务架构重构
- [ ] 高级图像预处理
- [ ] 多种输出格式支持

#### v2.0.0
- [ ] 机器学习优化
- [ ] 实时3D预览
- [ ] 移动端支持
- [ ] 企业级功能

## 贡献指南

### 开发环境设置
1. Fork项目仓库
2. 创建虚拟环境
3. 安装开发依赖
4. 运行测试确保环境正常

### 代码规范
- 遵循PEP 8代码风格
- 添加适当的注释和文档
- 编写单元测试
- 提交前运行代码检查

### 提交流程
1. 创建feature分支
2. 实现功能并测试
3. 提交Pull Request
4. 代码审查和合并

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

- 项目仓库: [GitHub链接]
- 问题反馈: [Issues链接]
- 技术讨论: [Discussions链接]

---

*最后更新: 2024年1月*