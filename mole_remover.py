"""
专业去斑去痣脚本
策略：
1. 先用CodeFormer修脸改善整体质感（调用ComfyUI）
2. 再用频率分离 + 局部Inpaint精确去斑去痣
"""

import cv2
import numpy as np
import os
import sys
import json
import urllib.request
import urllib.error
import time
import uuid
import shutil

os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==================== ComfyUI API ====================

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type="output"):
    params = f"?filename={filename}&subfolder={subfolder}&type={folder_type}"
    req = urllib.request.Request(f"{COMFYUI_URL}/view{params}")
    return urllib.request.urlopen(req).read()


def run_codeformer(input_path, fidelity=0.5):
    """用CodeFormer修脸"""
    input_dir = r"C:\ComfyUI\input"
    os.makedirs(input_dir, exist_ok=True)
    ext = os.path.splitext(input_path)[1] or ".jpg"
    target_name = f"mole_{uuid.uuid4().hex[:8]}{ext}"
    shutil.copy2(input_path, os.path.join(input_dir, target_name))
    
    workflow = {
        "3": {"class_type": "FaceRestoreModelLoader", "inputs": {"model_name": "codeformer.pth"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": target_name}},
        "5": {"class_type": "FaceRestoreCFWithModel", "inputs": {
            "facerestore_model": ["3", 0], "image": ["4", 0],
            "facedetection": "retinaface_resnet50", "codeformer_fidelity": fidelity
        }},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "cf_mole_"}},
        "9": {"class_type": "PreviewImage", "inputs": {"images": ["5", 0]}}
    }
    
    result = queue_prompt(workflow)
    prompt_id = result["prompt_id"]
    print(f"[CodeFormer] 提交成功, prompt_id={prompt_id}")
    
    start = time.time()
    while time.time() - start < 300:
        try:
            history = get_history(prompt_id)
            if prompt_id in history and history[prompt_id]["status"]["status_str"] == "success":
                outputs = history[prompt_id]["outputs"]
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        for img in node_output["images"]:
                            data = get_image(img["filename"], img.get("subfolder",""), img.get("type","output"))
                            out_path = os.path.join(OUTPUT_DIR, img["filename"])
                            with open(out_path, 'wb') as f:
                                f.write(data)
                            print(f"[CodeFormer] 输出: {out_path}")
                            return out_path
        except:
            pass
        time.sleep(2)
    raise TimeoutError("CodeFormer超时")


# ==================== 去斑去痣（频率分离 + Inpaint） ====================

def frequency_separation_denoise(img, sigma=15, strength=1.0):
    """频率分离：低频层去噪，保留高频纹理"""
    low_freq = cv2.GaussianBlur(img, (0, 0), sigma)
    high_freq = cv2.subtract(img.astype(np.int16), low_freq.astype(np.int16))
    high_freq = np.clip(high_freq, 0, 255).astype(np.uint8)
    # 可以减弱低频（颜色斑块）但不影响高频（纹理）
    low_processed = cv2.medianBlur(low_freq, 5)
    result = cv2.addWeighted(low_processed.astype(np.int16), 1.0, high_freq.astype(np.int16), strength, 0)
    return np.clip(result, 0, 255).astype(np.uint8)


def detect_spots(img, min_radius=3, max_radius=20, sensitivity=0.3):
    """
    检测皮肤斑点（痣/雀斑）
    策略：在LAB颜色空间的A通道和B通道中检测深色圆形区域
    """
    # 转LAB
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # 检测深色区域（L通道低值）
    _, dark_mask = cv2.threshold(l, 70, 255, cv2.THRESH_BINARY_INV)
    
    # 形态学去噪
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # 用HoughCircles找圆形斑点（痣通常是圆形）
    # 先缩小处理加快速度
    h, w = img.shape[:2]
    scale = min(1.0, 2000 / max(h, w))
    small = cv2.resize(l, (int(w*scale), int(h*scale)))
    
    circles = cv2.HoughCircles(
        small, cv2.HOUGH_GRADIENT, dp=1.5, minDist=20,
        param1=50, param2=30 * sensitivity,
        minRadius=int(min_radius * scale), maxRadius=int(max_radius * scale)
    )
    
    spots = []
    if circles is not None:
        circles = np.round(circles[0]).astype(int)
        for (x, y, r) in circles:
            # 映射回原图坐标
            ox, oy, or_ = int(x/scale), int(y/scale), int(r/scale)
            # 检查这个圆是否在暗色区域
            if or_ > 0 and y < small.shape[0] and x < small.shape[1]:
                spots.append((ox, oy, or_))
    
    print(f"[去斑] Hough检测到 {len(spots)} 个圆形斑点")
    return spots, dark_mask


def inpaint_spots(img, spots, radius_scale=1.5):
    """用Telea算法修补斑点"""
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    for (x, y, r) in spots:
        r_inpaint = max(int(r * radius_scale), 3)
        cv2.circle(mask, (x, y), r_inpaint, 255, -1)
    
    if np.sum(mask) == 0:
        print("[去斑] 没有检测到斑点")
        return img
    
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    print(f"[去斑] Inpaint完成，修补了 {len(spots)} 个斑点")
    return result


def adaptive_spot_removal(img, sensitivity=0.3):
    """
    完整的去斑流水线：
    1. 频率分离减弱色斑
    2. Hough检测圆形斑点
    3. 局部Inpaint
    """
    print("[去斑] 开始频率分离去噪...")
    denoised = frequency_separation_denoise(img, sigma=15)
    
    print("[去斑] 检测斑点...")
    spots, dark_mask = detect_spots(denoised, sensitivity=sensitivity)
    
    print("[去斑] Inpaint修补...")
    result = inpaint_spots(denoised, spots)
    
    return result


# ==================== 主流程 ====================

def process(input_path, fidelity=0.5, do_codeformer=True, do_spot_removal=True):
    print(f"\n{'='*50}")
    print(f"开始处理: {input_path}")
    
    current_img_path = input_path
    
    if do_codeformer:
        print(f"\n{'='*50}")
        print("步骤1: CodeFormer修脸")
        current_img_path = run_codeformer(current_img_path, fidelity)
    
    if do_spot_removal:
        print(f"\n{'='*50}")
        print("步骤2: 去斑去痣")
        img = cv2.imread(current_img_path)
        if img is None:
            print(f"❌ 无法读取图片: {current_img_path}")
            return None
        
        result = adaptive_spot_removal(img)
        
        out_path = os.path.join(OUTPUT_DIR, f"final_{uuid.uuid4().hex[:8]}.png")
        cv2.imwrite(out_path, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        print(f"[去斑] 最终结果: {out_path}")
        current_img_path = out_path
    
    print(f"\n{'✅ 完成'}")
    return current_img_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python mole_remover.py <图片路径> [fidelity] [sensitivity]")
        print("  fidelity=0.5  (0-1, CodeFormer程度)")
        print("  sensitivity=0.3 (0-1, 斑点检测灵敏度)")
        sys.exit(1)
    
    img_path = sys.argv[1]
    fidelity = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    sensitivity = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    
    try:
        result = process(img_path, fidelity=fidelity, do_codeformer=True, do_spot_removal=True)
        if result:
            print(f"\n结果文件: {result}")
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
