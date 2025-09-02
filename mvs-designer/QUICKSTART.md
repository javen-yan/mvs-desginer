# MVS Designer 快速启动指南

## 🚀 5分钟快速体验

### 1. 环境准备

确保你的系统满足以下要求：
- Python 3.7+
- 8GB+ RAM
- NVIDIA GPU (可选，但强烈推荐)

### 2. 一键安装

```bash
# 下载项目
git clone <repository>
cd mvs-designer

# 自动安装（推荐使用虚拟环境）
./scripts/install.sh --venv

# 激活虚拟环境（如果使用了--venv）
source venv/bin/activate
```

### 3. 启动服务

```bash
# 启动服务
./scripts/start.sh
```

服务启动后，访问 http://localhost:5000

### 4. 准备测试照片

为了测试3D重建功能，你需要准备一组多角度照片：

#### 拍摄建议
1. **选择合适的物体**: 不透明、有纹理、中等大小的物体
2. **拍摄环境**: 光线均匀，背景简洁
3. **拍摄角度**: 围绕物体360度拍摄，包括上下视角
4. **照片数量**: 15-30张照片
5. **重叠度**: 相邻照片重叠60-80%

#### 示例拍摄序列
```
照片1-8:   水平环绕拍摄 (每45度一张)
照片9-12:  俯视角度拍摄 (4个方向)
照片13-16: 仰视角度拍摄 (4个方向)
照片17-20: 细节补充拍摄
```

### 5. 使用Web界面

1. 打开浏览器访问 http://localhost:5000
2. 拖拽或选择多张照片上传
3. 选择重建质量（建议先用"快速模式"测试）
4. 点击"开始3D重建"
5. 等待处理完成（可以看到实时进度）
6. 下载生成的3D模型

### 6. 使用API接口

```bash
# 测试服务状态
curl http://localhost:5000/

# 上传照片
curl -X POST http://localhost:5000/api/upload \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg" \
  -F "images=@photo3.jpg"

# 开始重建（使用返回的job_id）
curl -X POST http://localhost:5000/api/reconstruct \
  -H "Content-Type: application/json" \
  -d '{"job_id": "your-job-id", "quality": "medium"}'

# 查询状态
curl http://localhost:5000/api/status/your-job-id

# 下载模型
curl -O http://localhost:5000/api/download/your-job-id
```

### 7. 自动化测试

```bash
# 运行完整的API测试
python test_api.py --images /path/to/test/images --quality low
```

## 🔧 故障排除

### 常见问题

**问题1: Meshroom未找到**
```bash
# 解决方案：手动安装Meshroom
python utils/meshroom_installer.py
```

**问题2: GPU不可用**
```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查CUDA
nvcc --version

# 如果没有GPU，服务会自动使用CPU模式（较慢）
```

**问题3: 内存不足**
```bash
# 减少照片数量或分辨率
# 或者增加系统内存
```

**问题4: 端口被占用**
```bash
# 修改端口
export PORT=8080
python app.py
```

### 性能优化建议

1. **首次使用**: 建议用少量照片（5-10张）和低质量模式测试
2. **GPU加速**: 确保NVIDIA驱动和CUDA正确安装
3. **内存管理**: 避免同时运行多个重建任务
4. **存储空间**: 定期清理旧的任务文件

## 📚 下一步

- 阅读 [design.md](design.md) 了解详细的技术设计
- 查看 [README.md](README.md) 了解完整功能介绍
- 参考 [config/settings.py](config/settings.py) 了解配置选项
- 使用 [test_api.py](test_api.py) 进行功能测试

## 💡 提示

- 第一次运行Meshroom可能需要下载一些模型文件，请耐心等待
- GPU模式比CPU模式快3-5倍，强烈建议使用GPU
- 照片质量直接影响3D模型质量，请按照拍摄建议进行
- 可以先用快速模式测试，确认效果后再用高质量模式

---

**祝你使用愉快！** 🎉