# MVS Designer

🎯 **多维度照片3D建模服务**

基于Python和Meshroom实现的自动化3D重建服务，支持通过上传多角度照片生成高质量3D模型。

## ✨ 主要特性

- 📷 **多角度照片上传** - 支持上下前后左右等多视角照片
- 🔄 **自动化3D重建** - 基于Meshroom/AliceVision的专业摄影测量技术
- 📊 **实时进度监控** - 任务状态实时更新和进度跟踪
- 🌐 **Web界面** - 直观易用的Web操作界面
- 🔌 **RESTful API** - 完整的API接口，支持集成开发
- 🐳 **Docker支持** - 容器化部署，包含GPU加速
- ⚡ **多质量选项** - 快速/标准/高质量三种重建模式

## 🚀 快速开始

### 环境要求

- Python 3.7+
- NVIDIA GPU (推荐，用于加速)
- 8GB+ RAM
- 20GB+ 磁盘空间

### 安装步骤

1. **克隆项目**
```bash
git clone <repository>
cd mvs-designer
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装Meshroom**
```bash
python utils/meshroom_installer.py
```

4. **启动服务**
```bash
python app.py
```

5. **访问服务**
打开浏览器访问 `http://localhost:5000`

### Docker部署

```bash
# 构建镜像
docker build -t mvs-designer -f docker/Dockerfile .

# 运行服务（GPU支持）
docker run --gpus all -p 5000:5000 -v $(pwd)/data:/app/static mvs-designer
```

## 📖 使用指南

### 1. 照片拍摄建议

- **数量**: 建议15-50张照片
- **角度**: 360度环绕拍摄，包括俯视仰视
- **重叠**: 相邻照片重叠60-80%
- **质量**: 2MP以上分辨率，避免模糊
- **光照**: 均匀光线，避免强烈阴影

### 2. API使用

#### 上传照片
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg" \
  -F "images=@photo3.jpg"
```

#### 开始重建
```bash
curl -X POST http://localhost:5000/api/reconstruct \
  -H "Content-Type: application/json" \
  -d '{"job_id": "your-job-id", "quality": "medium"}'
```

#### 查询状态
```bash
curl http://localhost:5000/api/status/your-job-id
```

#### 下载模型
```bash
curl -O http://localhost:5000/api/download/your-job-id
```

### 3. 测试工具

```bash
# 运行API测试
python test_api.py --images ./test_images --quality medium
```

## 🏗️ 项目结构

```
mvs-designer/
├── app/                    # 主应用模块
│   ├── __init__.py        # Flask应用工厂
│   ├── routes.py          # API路由
│   ├── meshroom_service.py # Meshroom集成
│   └── utils.py           # 工具函数
├── config/                # 配置文件
├── utils/                 # 工具模块
├── static/                # 静态文件存储
├── templates/             # HTML模板
├── docker/                # Docker配置
├── app.py                 # 应用入口
└── design.md             # 详细设计文档
```

## 🔧 配置选项

### 环境变量

```bash
# Meshroom配置
export MESHROOM_PATH="/path/to/meshroom_batch"
export USE_GPU=True
export CUDA_VISIBLE_DEVICES=0

# 服务配置
export FLASK_DEBUG=False
export PORT=5000
export HOST=0.0.0.0

# 文件配置
export MAX_CONTENT_LENGTH=500000000  # 500MB
```

### 质量预设

| 质量级别 | 处理时间 | 适用场景 |
|---------|---------|---------|
| Low     | 快速     | 预览测试 |
| Medium  | 中等     | 日常使用 |
| High    | 较长     | 专业用途 |

## 📊 性能指标

### 典型处理时间
- **20张照片 + Medium质量**: 15-30分钟
- **50张照片 + High质量**: 1-2小时
- **GPU加速**: 比CPU快3-5倍

### 系统要求
- **最低配置**: 4GB RAM, CPU处理
- **推荐配置**: 16GB RAM, NVIDIA GTX 1060+
- **高端配置**: 32GB RAM, NVIDIA RTX 3080+

## 🐛 故障排除

### 常见问题

**Q: Meshroom安装失败**
A: 检查NVIDIA驱动和CUDA版本，使用安装脚本自动配置

**Q: 重建质量不佳**
A: 增加照片数量，提高重叠度，改善拍摄光照条件

**Q: 处理速度慢**
A: 启用GPU加速，减少照片数量，使用较低质量设置

**Q: 内存不足**
A: 减少并发任务，使用较小分辨率照片

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！详见 [design.md](design.md) 中的贡献指南。

## 📞 支持

- 📚 [详细设计文档](design.md)
- 🐛 [问题反馈](issues)
- 💬 [技术讨论](discussions)

---

**MVS Designer** - 让3D建模变得简单高效！