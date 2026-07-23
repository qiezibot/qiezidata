"""
去胡子 v3 — 整张图送CodeFormer（保持人脸结构）
然后用遮罩只取胡须区域混合回原图
"""

import cv2
import numpy as np
import os
import sys
import uuid
import json
import urllib.request
import time

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_beard_mask(img):
    """检测人脸，几何定位胡须区域，生成羽化遮罩"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
    
    scale = min(800 / max(h, w), 1.0)
    small = cv2.resize(gray, (int(w*scale), int(h*scale))) if scale < 1 else gray
    
    faces = face_cascade.detectMultiScale(small, 1.15, 4, minSize=(80, 80))
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(small, 1.08, 3, minSize=(60, 60))
    
    if len(faces) == 0:
        return None
    
    face = max(faces, key=lambda r: r[2]*r[3])
    fx, fy, fw, fh = [int(v / scale) for v in face]
    
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # 嘴部区域（脸部下半 50%-82%）
    mouth_y1 = fy + int(fh * 0.50)
    mouth_y2 = fy + int(fh * 0.82)
    mouth_x1 = fx + int(fw * 0.18)
    mouth_x2 = fx + int(fw * 0.82)
    mouth_cx = (mouth_x1 + mouth_x2) // 2
    mouth_cy = (mouth_y1 + mouth_y2) // 2
    mouth_w = mouth_x2 - mouth_x1
    mouth_h = mouth_y2 - mouth_y1
    
    # 人中
    nose_y = fy + int(fh * 0.35)
    cv2.ellipse(mask,
                ((mouth_x1 + mouth_x2)//2, (nose_y + mouth_y1)//2),
                (int(mouth_w*0.45), int((mouth_y1 - nose_y)*0.5) + 10),
                0, 0, 360, 255, -1)
    
    # 下巴
    chin_bottom = fy + fh
    cv2.ellipse(mask,
                ((mouth_x1 + mouth_x2)//2, (mouth_y2 + chin_bottom)//2),
                (int(mouth_w*0.5) + 15, int((chin_bottom - mouth_y2)*0.55) + 15),
                0, 0, 360, 255, -1)
    
    # 去掉嘴
    cv2.ellipse(mask, (mouth_cx, mouth_cy), 
                (int(mouth_w*0.35), int(mouth_h*0.30)), 0, 0, 360, 0, -1)
    
    # 大羽化
    mask = cv2.GaussianBlur(mask, (51, 51), 20)
    
    return mask, (fx, fy, fw, fh)


def run_comfyui_workflow(wf, timeout_sec=120):
    """提交工作流到ComfyUI并等待结果"""
    payload = {"prompt": wf, "client_id": f"beard_v3_{uuid.uuid4().hex[:8]}"}
    
    req = urllib.request.Request(
        "http://127.0.0.1:8188/prompt",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        prompt_id = json.loads(resp.read())['prompt_id']
        print(f"提交成功: {prompt_id}")
    
    for _ in range(timeout_sec // 2):
        time.sleep(2)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=5) as resp:
                history = json.loads(resp.read())
                if prompt_id in history:
                    outputs = history[prompt_id]['outputs']
                    for node_id, node_out in outputs.items():
                        if 'images' in node_out:
                            img_info = node_out['images'][0]
                            return os.path.join(r"C:\ComfyUI\output", img_info['filename'])
                    break
        except:
            pass
    return None


def process(input_path):
    print(f"处理: {os.path.basename(input_path)}")
    
    img = cv2.imread(input_path)
    if img is None:
        print("❌ 读取失败")
        return None
    
    h, w = img.shape[:2]
    print(f"尺寸: {w}x{h}")
    
    print("步骤1: 检测人脸+生成胡须遮罩...")
    result = create_beard_mask(img)
    if result is None:
        print("❌ 未检测到人脸")
        return None
    mask, (fx, fy, fw, fh) = result
    print(f"人脸区域: ({fx},{fy}) {fw}x{fh}")
    
    print("步骤2: 整张图送ComfyUI CodeFormer...")
    input_name = f"beard_full_{uuid.uuid4().hex[:8]}.png"
    cv2.imwrite(os.path.join(r"C:\ComfyUI\input", input_name), img)
    
    # 简化工作流：只修人脸不放大
    wf = {
        "1": {
            "inputs": {"image": input_name, "upload": "image"},
            "class_type": "LoadImage"
        },
        "2": {
            "inputs": {"model_name": "codeformer.pth"},
            "class_type": "FaceRestoreModelLoader"
        },
        "3": {
            "inputs": {
                "facerestore_model": ["2", 0],
                "image": ["1", 0],
                "facedetection": "retinaface_resnet50",
                "codeformer_fidelity": 0.8  # 高保真，尽量接近原脸
            },
            "class_type": "FaceRestoreCFWithModel"
        },
        "4": {
            "inputs": {"images": ["3", 0], "filename_prefix": "beard_full_"},
            "class_type": "SaveImage"
        }
    }
    
    codeformer_out = run_comfyui_workflow(wf)
    
    if codeformer_out and os.path.exists(codeformer_out):
        restored = cv2.imread(codeformer_out)
        if restored is not None:
            print(f"CodeFormer输出: {codeformer_out}")
            restored = cv2.resize(restored, (w, h))
            
            # 用羽化遮罩混合：只取胡须区域的CodeFormer结果
            mask_3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            
            # 原图在遮罩区域也做一点点皮肤增强
            result = img.astype(np.float32) * (1.0 - mask_3 * 0.85) + \
                     restored.astype(np.float32) * mask_3 * 0.85
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            print("步骤3: 混合完成")
        else:
            result = img.copy()
    else:
        print("⚠️ CodeFormer未完成")
        result = img.copy()
    
    uid = uuid.uuid4().hex[:8]
    
    # 对比图
    scale = min(1.0, 2000 / max(h, w))
    preview_r = cv2.resize(result, (int(w*scale), int(h*scale)))
    preview_o = cv2.resize(img, (int(w*scale), int(h*scale)))
    side = np.hstack([preview_o, preview_r])
    
    compare_out = os.path.join(OUTPUT_DIR, f"beard_v3_compare_{uid}.jpg")
    cv2.imwrite(compare_out, side, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    out_jpg = os.path.join(OUTPUT_DIR, f"beard_v3_{uid}.jpg")
    cv2.imwrite(out_jpg, preview_r, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    print(f"✅ 完成")
    return out_jpg, compare_out


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else r"C:\temp\comfy_results\retouch_ai_ed479b96.png"
    result = process(path)
    if result:
        print(f"\n预览: {result[0]}")
        print(f"对比: {result[1]}")
