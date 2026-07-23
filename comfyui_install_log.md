# ComfyUI 安装日志
## 开始时间: 2026-05-18 13:48

## 环境检查
- Python版本: Python 3.11.9 (C:\Program Files\Python311\python.exe)
- pip版本: pip 26.1.1
- Git: 未安装，将通过zip方式下载ComfyUI
- 磁盘空间: 875GB可用
- 显卡: 大概率无独立显卡，按CPU模式准备
- CUDA可用: 否（pytorch cu118已安装但CUDA不可用，使用CPU模式）
- Git: 未安装（通过GIT_PYTHON_REFRESH=quiet环境变量绕过）

## 步骤记录

### 1. 下载ComfyUI
- 2026-05-18 13:49: 从GitHub下载ComfyUI master.zip
- 解压到 C:\ComfyUI

### 2. 安装依赖
- pip install -r requirements.txt ✅ (Python 3.11.9)
- 修复torchaudio DLL加载问题: pip install torchaudio==2.7.1 --force-reinstall --no-deps ✅

### 3. 安装插件
- **ComfyUI-Manager** ✅ (V3.40) - 插件管理器
- **ComfyUI-KJNodes** ✅ - 图像处理节点
- **ComfyUI-Impact-Pack** ✅ (V8.28.3) - 图像处理工具包
- **ComfyUI-FaceAnalysis** ✅ - 人脸分析
- **websocket_image_save.py** ✅ (自带)

### 4. 安装Python依赖
- piexif ✅
- insightface ✅ (binary only, 0.2.1)
- segment-anything ✅ (1.0)
- opencv-python-headless ✅

### 5. 下载模型
- **GFPGANv1.4.pth** ✅ (332.5 MB) - 轻量面部修复 - C:\ComfyUI\models\facerestore\
- **codeformer.pth** ✅ (359.2 MB) - 面部修复 - C:\ComfyUI\models\facerestore\
- **RealESRGAN_x4plus.pth** ✅ (63.9 MB) - 4x超分辨率放大 - C:\ComfyUI\models\upscale_models\
- 总计: ~755 MB

### 6. 创建工作流
- ✅ **wedding_retouch_basic.json** - 基础工作流: 载入→GFPGAN面部修复→RealESRGAN超分→调色→保存
- ✅ **wedding_retouch_fine.json** - 精细工作流: 载入→GFPGAN+CodeFormer混合修复→柔光调色→超分→保存

### 7. 启动测试
- 2026-05-18 13:56: ComfyUI V0.21.1 启动成功 ✅
- 所有5个自定义节点加载成功 ✅
- 设备: CPU模式
- 注意: ComfyUI-Manager网络受限（已切换本地模式，不影响核心功能）
- 快捷启动脚本: C:\ComfyUI\start_cpu.bat

## 完成状态: ✅ 成功
- ComfyUI路径: C:\ComfyUI
- 启动命令: cd C:\ComfyUI && python main.py --cpu --listen 127.0.0.1 --port 8188
- 浏览器访问: http://127.0.0.1:8188
- 总下载量: ~755 MB（远低于20GB限制）

## 后续建议
1. 如需要SD扩散功能，可下载轻量模型如 LCM-LoRA + Realistic Vision (2-3GB)
2. 人脸修复需要GFPGAN模型配合FaceRestore节点使用
3. 如果卡顿，可调小图片尺寸或使用--lowvram参数
4. 建议安装Git for Windows以启用ComfyUI-Manager完整功能
5. Torchaudio可能影响音频VAE功能，但不影响图像处理核心功能
---
