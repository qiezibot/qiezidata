"""绕过ModelScope pipeline，直接加载PyTorch模型推理皮肤精修"""
import os, sys, json, uuid
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

# 禁用ModelScope锁
os.environ['MODELSCOPE_LOCK'] = 'false'

import torch
import cv2
import numpy as np

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_DIR = r"C:\Users\lfy20\.cache\modelscope\hub\models\damo\cv_unet_skin-retouching"

img_path = r'C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\ebc873ea-5136-42ce-9155-e62e21d2d988.png'

print("尝试直接加载PyTorch模型...")

# 1. 加载配置文件
with open(os.path.join(MODEL_DIR, 'configuration.json')) as f:
    config = json.load(f)
print(f"配置: {json.dumps(config, indent=2)[:300]}")

# 2. 用mmcv/原生torch加载
# 先看看模型文件结构
ckpt = torch.load(os.path.join(MODEL_DIR, 'pytorch_model.pt'), map_location='cpu', weights_only=True)
if isinstance(ckpt, dict):
    print(f"检查点keys: {list(ckpt.keys())[:10]}")
    for k in list(ckpt.keys())[:5]:
        v = ckpt[k]
        if hasattr(v, 'shape'):
            print(f"  {k}: shape={v.shape}")
        else:
            print(f"  {k}: type={type(v).__name__}")

# 3. 试试用modelscope但手动跳过lock
print("\n尝试用modelscope pipeline (强制)...")
try:
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks
    
    # 直接指定本地路径
    pipe = pipeline(Tasks.skin_retouching, model=MODEL_DIR)
    print("pipeline加载成功 ✅")
    
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    scale = 2000 / max(w, h)
    if scale < 1:
        img = cv2.resize(img, (int(w*scale), int(h*scale)))
    
    result = pipe(img)
    print(f"结果类型: {type(result).__name__}")
    
    if isinstance(result, dict):
        for k, v in result.items():
            if hasattr(v, 'shape'):
                print(f"  {k}: shape={v.shape}")
                uid = uuid.uuid4().hex[:8]
                out = os.path.join(OUTPUT_DIR, f"skin_ai_{uid}.jpg")
                cv2.imwrite(out, v, [cv2.IMWRITE_JPEG_QUALITY, 95])
                print(f"  已保存: {out}")
    elif hasattr(result, 'shape'):
        uid = uuid.uuid4().hex[:8]
        out = os.path.join(OUTPUT_DIR, f"skin_ai_{uid}.jpg")
        cv2.imwrite(out, result, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"已保存: {out}")
    
except Exception as e:
    print(f"pipeline失败: {e}")
    print("\n模型文件已存在，可以直接用ComfyUI工作流试试")
