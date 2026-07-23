"""
去胡子 v2 — 先用Haar+Cascade定位胡须区域生成遮罩
然后用CodeFormer只修遮罩区域 + 羽化混合到原图
不糊！保持皮肤纹理
"""

import cv2
import numpy as np
import os
import sys
import uuid
import torch

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
    
    # 嘴部区域（脸部下半 55%-80%）
    mouth_y1 = fy + int(fh * 0.55)
    mouth_y2 = fy + int(fh * 0.80)
    mouth_x1 = fx + int(fw * 0.20)
    mouth_x2 = fx + int(fw * 0.80)
    mouth_cx = (mouth_x1 + mouth_x2) // 2
    mouth_cy = (mouth_y1 + mouth_y2) // 2
    mouth_w = mouth_x2 - mouth_x1
    mouth_h = mouth_y2 - mouth_y1
    
    # 人中（嘴上到鼻子下）
    nose_y = fy + int(fh * 0.35)
    upper_top = nose_y
    upper_bottom = mouth_y1
    if upper_bottom > upper_top:
        cv2.ellipse(mask,
                    ((mouth_x1 + mouth_x2)//2, (upper_top + upper_bottom)//2),
                    (mouth_w//2 + 5, (upper_bottom - upper_top)//2 + 5),
                    0, 0, 360, 255, -1)
    
    # 下巴（嘴下到脸底）
    chin_top = mouth_y2
    chin_bottom = fy + fh
    if chin_bottom > chin_top:
        cv2.ellipse(mask,
                    ((mouth_x1 + mouth_x2)//2, (chin_top + chin_bottom)//2),
                    (mouth_w//2 + 15, (chin_bottom - chin_top)//2 + 15),
                    0, 0, 360, 255, -1)
    
    # 去掉嘴内部
    cv2.ellipse(mask, (mouth_cx, mouth_cy), 
                (int(mouth_w*0.38), int(mouth_h*0.35)), 0, 0, 360, 0, -1)
    
    # 大羽化
    mask = cv2.GaussianBlur(mask, (51, 51), 20)
    
    return mask


def codeformer_restore_region(img, mask):
    """
    用ComfyUI的CodeFormer只修胡须区域
    策略：把胡须区域的图裁出来送CodeFormer，然后混合回去
    """
    # 找到mask的非零区域
    ys, xs = np.where(mask > 10)
    if len(xs) == 0:
        return img
    
    y1, y2 = ys.min(), ys.max()
    x1, x2 = xs.min(), xs.max()
    
    # 扩大裁剪区域（CodeFormer需要完整的人脸才能正确修复）
    pad = 50
    y1 = max(0, y1 - pad)
    y2 = min(img.shape[0], y2 + pad)
    x1 = max(0, x1 - pad)
    x2 = min(img.shape[1], x2 + pad)
    
    # 裁出包含胡须的人脸区域
    face_crop = img[y1:y2, x1:x2].copy()
    crop_h, crop_w = face_crop.shape[:2]
    
    print(f"CodeFormer输入区域: ({x1},{y1})-({x2},{y2}) = {crop_w}x{crop_h}")
    
    # ---------- 使用ComfyUI API调用CodeFormer ----------
    import urllib.request
    import json
    
    # 把裁图保存到ComfyUI的input目录
    input_name = f"beard_crop_{uuid.uuid4().hex[:8]}.png"
    cv2.imwrite(os.path.join(r"C:\ComfyUI\input", input_name), face_crop)
    
    # 准备工作流JSON
    wf = {
        "3": {
            "inputs": {"image": input_name, "upload": "image"},
            "class_type": "LoadImage",
            "_meta": {"title": "裁切胡须区域"}
        },
        "4": {
            "class_type": "FaceRestoreModelLoader",
            "inputs": {"model_name": "codeformer.pth"},
            "_meta": {"title": "CodeFormer模型"}
        },
        "5": {
            "class_type": "FaceRestoreCFWithModel",
            "inputs": {
                "facerestore_model": ["4", 0],
                "image": ["3", 0],
                "facedetection": "retinaface_resnet50",
                "codeformer_fidelity": 0.7
            },
            "_meta": {"title": "CodeFormer修胡子区域"}
        },
        "6": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["5", 0],
                "filename_prefix": "beard_region_"
            },
            "_meta": {"title": "保存"}
        }
    }
    
    wf_path = os.path.join(r"C:\ComfyUI\workflows", f"beard_region_temp.json")
    with open(wf_path, 'w') as f:
        json.dump(wf, f)
    
    # 提交到ComfyUI
    payload = {
        "prompt": wf,
        "client_id": "beard_remover_v2"
    }
    
    req = urllib.request.Request(
        "http://127.0.0.1:8188/prompt",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
        prompt_id = result['prompt_id']
        print(f"提交成功, prompt_id: {prompt_id}")
    
    # 等待完成
    import time
    output_file = None
    for attempt in range(120):
        time.sleep(2)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=5) as resp:
                history = json.loads(resp.read())
                if prompt_id in history:
                    outputs = history[prompt_id]['outputs']
                    for node_id, node_out in outputs.items():
                        if 'images' in node_out:
                            img_info = node_out['images'][0]
                            output_file = os.path.join(
                                r"C:\ComfyUI\output",
                                img_info['filename']
                            )
                            print(f"输出: {output_file}")
                            break
                    break
        except:
            pass
    else:
        print("⚠️ 超时未完成")
        # 还是用inpaint兜底
        return None
    
    if output_file and os.path.exists(output_file):
        restored = cv2.imread(output_file)
        if restored is not None:
            # 把修复后的区域混合回原图
            restored = cv2.resize(restored, (crop_w, crop_h))
            
            # 取对应区域的原图羽化遮罩
            crop_mask = mask[y1:y2, x1:x2]
            # 扩展遮罩到3通道
            crop_mask_3 = cv2.cvtColor(crop_mask, cv2.COLOR_GRAY2BGR) / 255.0
            
            result = img.copy()
            roi = result[y1:y2, x1:x2].astype(np.float32)
            restored_f = restored.astype(np.float32)
            
            blended = roi * (1.0 - crop_mask_3) + restored_f * crop_mask_3
            result[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)
            
            return result
    
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
    mask = create_beard_mask(img)
    if mask is None:
        print("❌ 未检测到人脸")
        return None
    
    print("步骤2: CodeFormer只修胡须区域...")
    result = codeformer_restore_region(img, mask)
    
    if result is None:
        print("⚠️ CodeFormer失败，用高级Inpaint兜底...")
        # 多尺度Inpaint + 纹理转移
        r1 = cv2.inpaint(img, (mask * 0.3).astype(np.uint8), 3, cv2.INPAINT_TELEA)
        # 再用原图的高频纹理做融合
        lap = cv2.Laplacian(img, cv2.CV_32F)
        lap_blur = cv2.GaussianBlur(lap, (5, 5), 2)
        texture = cv2.convertScaleAbs(img.astype(np.float32) + lap_blur * 0.1)
        texture = np.clip(texture, 0, 255).astype(np.uint8)
        
        mask_3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
        result = (img.astype(np.float32) * (1.0 - mask_3 * 0.5) +
                  texture.astype(np.float32) * mask_3 * 0.5)
        result = np.clip(result, 0, 255).astype(np.uint8)
    
    uid = uuid.uuid4().hex[:8]
    
    # 保存预览
    scale = min(1.0, 2000 / max(h, w))
    preview = cv2.resize(result, (int(w*scale), int(h*scale)))
    out_jpg = os.path.join(OUTPUT_DIR, f"beard_v2_{uid}.jpg")
    cv2.imwrite(out_jpg, preview, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    # 全尺寸
    out_png = os.path.join(OUTPUT_DIR, f"beard_v2_{uid}.png")
    cv2.imwrite(out_png, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    
    # 对比图
    side = np.hstack([
        cv2.resize(img, (int(w*scale), int(h*scale))),
        preview
    ])
    compare_out = os.path.join(OUTPUT_DIR, f"beard_v2_compare_{uid}.jpg")
    cv2.imwrite(compare_out, side, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    print(f"✅ 完成")
    print(f"对比图: {compare_out}")
    print(f"预览: {out_jpg}")
    return out_jpg, out_png


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python beard_remover_v2.py <图片路径>")
        sys.exit(1)
    
    result = process(sys.argv[1])
    if result:
        print(f"\n结果: {result[0]}")
