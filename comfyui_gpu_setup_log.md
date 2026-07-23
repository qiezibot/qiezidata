# ComfyUI GPU + 精修工作流设置报告

**日期**: 2026-05-18
**目标**: 在 Windows 上配置 ComfyUI，专攻人像婚纱精修，利用 RTX 3080 Ti

---

## ✅ Step 1: 停止旧进程
- 杀掉 pid 20268 (旧的 CPU 模式 ComfyUI)
- 清理所有残留 Python 进程
- 状态: ✅ 完成

## ✅ Step 2: 配置 GPU 环境
- Python: 3.11.9 (系统安装于 C:\Program Files\Python311)
- PyTorch: 2.7.1+cu118 (CUDA 版已安装，无需重装)
- GPU: **NVIDIA GeForce RTX 3080 Ti Laptop GPU** (16GB VRAM)
- CUDA 可用: ✅
- 启动模式: **NORMAL_VRAM** (cudaMallocAsync)
- 状态: ✅ 完成

## ✅ Step 3: 安装 AI 修图模型

### 已存在的模型
| 模型 | 路径 | 状态 |
|------|------|------|
| GFPGANv1.4.pth | models/facerestore/ | ✅ 已存在 |
| codeformer.pth | models/facerestore/ | ✅ 已存在 |
| RealESRGAN_x4plus.pth | models/upscale_models/ | ✅ 已存在 |

### 新增: facerestore_cf 自定义节点
- 来源: https://github.com/mav-rik/facerestore_cf
- 安装位置: C:\ComfyUI\custom_nodes\facerestore_cf\
- 注册节点: `FaceRestoreCFWithModel`, `CropFace`, `FaceRestoreModelLoader`
- 修复: 移除了冲突的 bundled basicsr(使用全局版); 修复了 GFPGAN 模型中 `w=codeformer_fidelity` 参数错误

### ComfyUI-Manager (V3.40)
- 状态: ✅ 正常加载
- 修复: 设置 `GIT_PYTHON_REFRESH=quiet` 环境变量解决 git 缺失警告

### 其他已加载的自定义节点
| 节点 | 版本 | 状态 |
|------|------|------|
| ComfyUI-Impact-Pack | V8.28.3 | ✅ |
| ComfyUI-Manager | V3.40 | ✅ |
| ComfyUI-KJNodes | - | ✅ |
| ComfyUI-FaceAnalysis | - | ✅ |
| facerestore_cf | - | ✅ |

## ✅ Step 4: 创建工作流

### 工作流文件
1. **`workflows/wedding_pro.json`** - GFPGAN + RealESRGAN 精修流程
   - 载入图片 → 人脸修复(GFPGAN) → 4x超分 → 下采样(0.25x限幅) → 保存
2. **`workflows/wedding_pro_codeformer.json`** - CodeFormer + RealESRGAN 精修流程
   - 载入图片 → 人脸修复(CodeFormer, fidelity=0.6) → 4x超分 → 下采样限幅 → 保存

### 启动脚本
3. **`gpu_start.bat`** - 双击启动 GPU 模式 ComfyUI
   - 设置 GIT_PYTHON_REFRESH 和 PYTHONPATH 环境变量
   - `python main.py --listen 127.0.0.1 --port 8188`

## ✅ Step 5: GPU 模式启动
- 命令: `python main.py --listen 127.0.0.1 --port 8188` (无 --cpu 参数)
- GPU 确认日志:
  ```
  Device: cuda:0 NVIDIA GeForce RTX 3080 Ti Laptop GPU : cudaMallocAsync
  Total VRAM 16384 MB, total RAM 32435 MB
  Set vram state to: NORMAL_VRAM
  ```
- 端口: 8188
- 状态: ✅ 运行中

## ✅ Step 6: 测试结果

### 测试 1: GFPGAN + RealESRGAN 4x
- 输入: wedding_input.png (4284x5712, ~3.7MB)
- 输出: wedding_pro__00002_.png (17136x22848, 354MB)
- 处理时间: ~254 秒 (含首次模型加载)
- 状态: ✅ 成功

### 测试 2: CodeFormer (人脸修复, 无超分)
- 输入: wedding_input.png (4284x5712)
- 输出: wedding_codeformer_test__00001_.png (4284x5712)
- 处理时间: ~14 秒
- CodeFormer 模型加载: ✅ 成功
- 状态: ✅ 成功

### 预览图
- 已生成: C:\temp\tts\wedding_ai_preview.jpg (1280x1706, ~204KB)
- 从 4x 超分输出裁剪缩放

## 📊 性能总结

| 操作 | 时间 | 显存占用 |
|------|------|---------|
| FaceRestore (GFPGAN) | ~60s | ~2GB |
| CodeFormer 加载 + 修复 | ~14s | ~3GB |
| RealESRGAN 4x 超分 | ~190s | ~6GB |
| 总计 (GFPGAN + 4x) | ~254s | ~8GB RAM, GPU 显存适中 |

## ⚠️ 遇到的问题及修复
1. **basicsr 注册冲突**: 全局安装的 basicsr 与 bundled basicsr 的 CodeFormer 注册冲突 → 移除 bundled basicsr
2. **GFPGAN 调用参数错误**: 节点代码始终发送 `w=codeformer_fidelity` 参数 → 修复为检测模型类型后选择正确调用方式
3. **ComfyUI-Manager git 缺失**: git 可执行文件未找到 → 设置 `GIT_PYTHON_REFRESH=quiet`
4. **4x 超分输出过大**: 17136x22848 像素 → 工作流添加 ImageScaleBy 0.25x 下采样限幅

## 📎 使用说明
1. 双击 `C:\ComfyUI\gpu_start.bat` 启动
2. 浏览器访问 http://127.0.0.1:8188
3. 加载 workflows/wedding_pro.json 或 wedding_pro_codeformer.json
4. 选择输入图片并运行
