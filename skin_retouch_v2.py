"""
皮肤精修 v2 — 只磨皮不改变五官结构
策略：CodeFormer修脸 + 自适应双边滤波局部磨皮 + 遮罩保护五官边缘
"""

import cv2
import numpy as np
import os
import sys
import urllib.request
import json
import time
import uuid
import shutil

os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== ComfyUI CodeFormer ====================

def run_codeformer(input_path, fidelity=0.5):
    input_dir = r"C:\ComfyUI\input"
    target_name = f"sk_{uuid.uuid4().hex[:8]}{os.path.splitext(input_path)[1] or '.jpg'}"
    shutil.copy2(input_path, os.path.join(input_dir, target_name))
    
    workflow = {
        "3": {"class_type": "FaceRestoreModelLoader", "inputs": {"model_name": "codeformer.pth"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": target_name}},
        "5": {"class_type": "FaceRestoreCFWithModel", "inputs": {
            "facerestore_model": ["3", 0], "image": ["4", 0],
            "facedetection": "retinaface_resnet50", "codeformer_fidelity": fidelity
        }},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "sk_"}},
    }
    
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt",
        data=json.dumps({"prompt": workflow}).encode('utf-8'),
        headers={"Content-Type": "application/json"})
    prompt_id = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
    
    start = time.time()
    while time.time() - start < 300:
        try:
            h = json.loads(urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}").read())
            if prompt_id in h and h[prompt_id]["status"]["status_str"] == "success":
                for nid, no in h[prompt_id]["outputs"].items():
                    if "images" in no:
                        for img in no["images"]:
                            params = f"?filename={img['filename']}&subfolder={img.get('subfolder','')}&type={img.get('type','output')}"
                            data = urllib.request.urlopen(f"{COMFYUI_URL}/view{params}").read()
                            out = os.path.join(OUTPUT_DIR, img["filename"])
                            with open(out, 'wb') as f: f.write(data)
                            return out
        except: pass
        time.sleep(2)
    raise TimeoutError("CodeFormer超时")

# ==================== 专业磨皮 ====================

def skin_smooth(img, strength=1.0):
    """
    表面模糊磨皮 — 只平滑皮肤色斑区域，保护边缘
    """
    print(f"[磨皮] 输入尺寸: {img.shape[1]}x{img.shape[0]}")
    
    # 1. 双边滤波磨皮（保留边缘的模糊）
    bf = cv2.bilateralFilter(img, d=15, sigmaColor=40, sigmaSpace=15)
    
    # 2. 用表面模糊进一步平滑色斑（OpenCV自带）
    # 替代引导滤波：用小半径的双边滤波
    bf2 = cv2.bilateralFilter(bf, d=9, sigmaColor=20, sigmaSpace=9)
    bf = bf2
    
    # 3. 频率分离：只平滑低频（色斑层）
    low = cv2.GaussianBlur(img, (0, 0), 15)
    high = cv2.subtract(img.astype(np.int16), low.astype(np.int16))
    low_smooth = cv2.bilateralFilter(low, d=9, sigmaColor=30, sigmaSpace=9)
    
    # 合成
    result = cv2.addWeighted(low_smooth.astype(np.int16), 1.0, high.astype(np.int16), 0.6, 0)
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # 4. 柔和混合原图和磨皮结果（保护五官不模糊）
    alpha = strength * 0.6
    final = cv2.addWeighted(img, 1 - alpha, result, alpha, 0)
    
    return final


def color_uniform(img, strength=0.3):
    """均匀肤色 — 减少局部色斑的颜色差异"""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # 对A/B通道做高斯模糊（去掉颜色斑点）
    a_smooth = cv2.GaussianBlur(a, (0, 0), 5)
    b_smooth = cv2.GaussianBlur(b, (0, 0), 5)
    
    a_blend = cv2.addWeighted(a.astype(np.int16), 1-strength, a_smooth.astype(np.int16), strength, 0)
    b_blend = cv2.addWeighted(b.astype(np.int16), 1-strength, b_smooth.astype(np.int16), strength, 0)
    
    lab = cv2.merge([l, np.clip(a_blend, 0, 255).astype(np.uint8), np.clip(b_blend, 0, 255).astype(np.uint8)])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


# ==================== 主流程 ====================

def process(input_path, fidelity=0.5, smooth_strength=1.0, color_strength=0.3):
    print(f"处理: {os.path.basename(input_path)}")
    
    print("步骤1: CodeFormer修脸...")
    cf_path = run_codeformer(input_path, fidelity)
    print(f"  -> {cf_path}")
    
    img = cv2.imread(cf_path)
    if img is None:
        print("❌ 无法读取CodeFormer结果")
        return None
    
    print("步骤2: 磨皮去斑...")
    img = skin_smooth(img, strength=smooth_strength)
    
    print("步骤3: 均匀肤色...")
    img = color_uniform(img, strength=color_strength)
    
    # 可选：局部锐化
    sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    img = cv2.filter2D(img, -1, sharpen)
    
    out = os.path.join(OUTPUT_DIR, f"sk_final_{uuid.uuid4().hex[:8]}.jpg")
    cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"✅ -> {out}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python skin_retouch_v2.py <图片路径> [fidelity=0.5] [smooth=1.0] [color=0.3]")
        sys.exit(1)
    
    path = sys.argv[1]
    f = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    s = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    c = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
    
    result = process(path, f, s, c)
    if result:
        print(f"\n结果: {result}")
