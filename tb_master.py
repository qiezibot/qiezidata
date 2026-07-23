"""
淘宝主图精修工具
功能：
1. 抠图（rembg）— 去背景
2. 换背景 — 白底、纯色、渐变
3. 自动调色 — 亮度/对比度/饱和度优化
4. 人脸修复 — GFPGAN/CodeFormer修脸（如果画面有人）

用法：
  python tb_master.py <图片路径> [选项]
  
选项：
  --bg white|red|blue|black|gradient  背景颜色（默认white）
  --no-face                            跳过人脸修复
  --brightness 1.0                     亮度（默认1.0）
  --contrast 1.0                       对比度（默认1.0）
  --saturation 1.2                     饱和度（默认1.2）
"""

import cv2
import numpy as np
import os
import sys
import json
import uuid
import urllib.request
import time
from rembg import remove, new_session

# ============ 配置 ============
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = r"C:\temp\comfy_results"

# 常用淘宝背景色
BG_COLORS = {
    "white": (255, 255, 255),
    "red": (220, 40, 40),
    "blue": (40, 100, 200),
    "black": (30, 30, 30),
    "pink": (255, 200, 220),
    "cream": (255, 245, 230),
    "gray": (240, 240, 240),
}

os.makedirs(OUTPUT_DIR, exist_ok=True)


def remove_background(input_path, output_path):
    """rembg抠图，输出RGBA"""
    print(f"[抠图] {os.path.basename(input_path)}")
    
    # CPU inference（CUDA有版本问题但CPU更快启动）
    session = new_session('u2net', providers=['CPUExecutionProvider'])
    
    with open(input_path, 'rb') as f:
        data = f.read()
    
    out_data = remove(data, session=session)
    
    with open(output_path, 'wb') as f:
        f.write(out_data)
    
    # 验证
    img = cv2.imread(output_path, cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[-1] != 4:
        print("[抠图] ❌ 输出格式不对")
        return None
    # 检查是否有透明像素
    alpha = img[:,:,3]
    transparent = (alpha == 0).sum()
    total = alpha.size
    print(f"[抠图] ✅ 完成 | 分辨率: {img.shape[1]}x{img.shape[0]} | 透明占比: {transparent/total*100:.1f}%")
    return img


def change_background(rgba_img, bg_color_name="white"):
    """换背景"""
    if bg_color_name in BG_COLORS:
        bg_rgb = BG_COLORS[bg_color_name]
    elif bg_color_name.startswith("#"):
        # 十六进制
        h = bg_color_name.lstrip("#")
        bg_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        bg_rgb = (bg_rgb[2], bg_rgb[1], bg_rgb[0])  # RGB→BGR
    else:
        bg_rgb = (255, 255, 255)
    
    h, w = rgba_img.shape[:2]
    bg = np.full((h, w, 3), bg_rgb, dtype=np.uint8)
    alpha = rgba_img[:,:,3:4] / 255.0
    result = (rgba_img[:,:,:3] * alpha + bg * (1 - alpha)).astype(np.uint8)
    
    name_map = {v: k for k, v in BG_COLORS.items()}
    color_name = name_map.get(bg_rgb, bg_color_name)
    print(f"[换背景] {color_name} | RGB({bg_rgb[2]},{bg_rgb[1]},{bg_rgb[0]})")
    return result


def auto_tune(img, brightness=1.0, contrast=1.0, saturation=1.2):
    """自动调色"""
    print(f"[调色] 亮度={brightness} 对比度={contrast} 饱和度={saturation}")
    
    # 亮度和对比度
    result = cv2.convertScaleAbs(img, alpha=contrast, beta=(brightness - 1) * 128)
    
    # 饱和度
    if saturation != 1.0:
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:,:,1] = np.clip(hsv[:,:,1] * saturation, 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    return result


def face_restore_gfpgan(input_path):
    """ComfyUI GFPGAN修脸"""
    print(f"[修脸] GFPGAN")
    
    # 复制到input
    input_name = f"tb_face_{uuid.uuid4().hex[:8]}.png"
    shutil = __import__('shutil')
    shutil.copy2(input_path, os.path.join(r'C:\ComfyUI\input', input_name))
    
    wf = {
        '1': {'inputs': {'image': input_name, 'upload': 'image'}, 'class_type': 'LoadImage'},
        '2': {'inputs': {'model_name': 'GFPGANv1.4.pth'}, 'class_type': 'FaceRestoreModelLoader'},
        '3': {'inputs': {'facerestore_model': ['2',0], 'image': ['1',0], 'facedetection': 'YOLOv5n', 'codeformer_fidelity': 0.3}, 'class_type': 'FaceRestoreCFWithModel'},
        '4': {'inputs': {'images': ['3',0], 'filename_prefix': 'tb_face_'}, 'class_type': 'SaveImage'}
    }
    
    payload = {'prompt': wf, 'client_id': f'tb_{uuid.uuid4().hex[:8]}'}
    req = urllib.request.Request(f'{COMFYUI_URL}/prompt', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    pid = json.loads(urllib.request.urlopen(req, timeout=30).read())['prompt_id']
    
    for _ in range(60):
        time.sleep(2)
        try:
            with urllib.request.urlopen(f'{COMFYUI_URL}/history/{pid}', timeout=5) as r:
                hh = json.loads(r.read())
                if pid in hh:
                    for no in hh[pid]['outputs'].values():
                        if 'images' in no:
                            out_path = os.path.join(r'C:\ComfyUI\output', no['images'][0]['filename'])
                            print(f"[修脸] ✅ {out_path}")
                            return cv2.imread(out_path)
        except:
            pass
    
    print("[修脸] ❌ 超时")
    return None


def process(input_path, bg_color="white", do_face=True, brightness=1.0, contrast=1.0, saturation=1.2):
    """完整流程"""
    uid = uuid.uuid4().hex[:8]
    basename = os.path.basename(input_path)
    
    print(f"\n{'='*50}")
    print(f"淘宝主图精修: {basename}")
    print(f"背景: {bg_color} | 修脸: {'是' if do_face else '否'}")
    print(f"{'='*50}\n")
    
    # 1. 抠图
    rgba = remove_background(input_path, os.path.join(OUTPUT_DIR, f"tb_rmbg_{uid}.png"))
    if rgba is None:
        return None
    
    # 2. 换背景
    img_bg = change_background(rgba, bg_color)
    
    # 3. 调色
    img_tuned = auto_tune(img_bg, brightness, contrast, saturation)
    
    # 4. 人脸修复（可选）
    if do_face:
        # 先保存临时图
        temp_path = os.path.join(OUTPUT_DIR, f"tb_temp_{uid}.png")
        cv2.imwrite(temp_path, img_tuned)
        restored = face_restore_gfpgan(temp_path)
        if restored is not None:
            # 取回原尺寸
            restored = cv2.resize(restored, (img_tuned.shape[1], img_tuned.shape[0]))
            img_tuned = restored
        try:
            os.remove(temp_path)
        except:
            pass
    
    # 5. 输出
    out_path = os.path.join(OUTPUT_DIR, f"tb_final_{uid}.jpg")
    cv2.imwrite(out_path, img_tuned, [cv2.IMWRITE_JPEG_QUALITY, 97])
    print(f"\n✅ 完成: {out_path}")
    print(f"   尺寸: {img_tuned.shape[1]}x{img_tuned.shape[0]}")
    
    # 对比预览
    orig = cv2.imread(input_path)
    s = min(800/max(img_tuned.shape[0], img_tuned.shape[1]), 1.0)
    po = cv2.resize(orig, (int(img_tuned.shape[1]*s), int(img_tuned.shape[0]*s)))
    pt = cv2.resize(img_tuned, (int(img_tuned.shape[1]*s), int(img_tuned.shape[0]*s)))
    side = cv2.hconcat([po, pt])
    cmp_path = os.path.join(OUTPUT_DIR, f"tb_compare_{uid}.jpg")
    cv2.imwrite(cmp_path, side, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"对比: {cmp_path}")
    
    return out_path, cmp_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="淘宝主图精修")
    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("--bg", default="white", help="背景色: white/red/blue/black/pink/cream 或 #hex")
    parser.add_argument("--no-face", action="store_true", help="跳过人脸修复")
    parser.add_argument("--brightness", type=float, default=1.0, help="亮度 0.5-1.5")
    parser.add_argument("--contrast", type=float, default=1.0, help="对比度 0.5-1.5")
    parser.add_argument("--saturation", type=float, default=1.2, help="饱和度 0.5-2.0")
    
    args = parser.parse_args()
    
    result = process(
        args.input,
        bg_color=args.bg,
        do_face=not args.no_face,
        brightness=args.brightness,
        contrast=args.contrast,
        saturation=args.saturation,
    )
    
    if result:
        print(f"\n结果文件: {result[0]}")
        print(f"对比图: {result[1]}")
    else:
        print("\n❌ 处理失败")
        sys.exit(1)
