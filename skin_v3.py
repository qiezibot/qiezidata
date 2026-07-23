"""
皮肤精修 v3 — 纯OpenCV，不依赖任何AI模型
核心：只在皮肤区域做微小平滑，完全不碰五官边缘
"""

import cv2
import numpy as np
import os
import sys
import uuid

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def skin_detection(img):
    """检测皮肤区域 — YCrCb色彩空间"""
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)
    skin = cv2.inRange(ycrcb, lower, upper)
    
    # 形态学平滑皮肤遮罩
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, k, iterations=2)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, k, iterations=1)
    
    # 高斯模糊遮罩边缘，实现平滑过渡
    skin_soft = cv2.GaussianBlur(skin.astype(np.float32), (31, 31), 15) / 255.0
    return skin_soft


def smooth_skin_only(img, strength=0.5):
    """
    仅在皮肤区域做微小平滑
    策略：用极小半径的双边滤波模糊皮肤区域，原图与模糊图按遮罩混合
    """
    h, w = img.shape[:2]
    
    # 检测皮肤
    print("[v3] 检测皮肤区域...")
    skin_mask = skin_detection(img)
    
    # 轻微的快速双边滤波（只模糊小斑点）
    print("[v3] 双边滤波...")
    # 对大图降采样加速
    scale = min(1.0, 1500 / max(h, w))
    if scale < 1:
        small = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_LINEAR)
        small_bf = cv2.bilateralFilter(small, d=7, sigmaColor=25, sigmaSpace=7)
        bf = cv2.resize(small_bf, (w, h), interpolation=cv2.INTER_LINEAR)
    else:
        bf = cv2.bilateralFilter(img, d=7, sigmaColor=25, sigmaSpace=7)
    
    # 边缘保护：用原图梯度做边缘权重
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    # 边缘处权重小（不混合模糊图），平坦处权重大
    edge_weight = 1.0 - np.clip(grad_mag / 30.0, 0, 1)
    edge_weight = cv2.GaussianBlur(edge_weight, (15, 15), 5)
    edge_weight = np.stack([edge_weight]*3, axis=2)
    
    # 最终遮罩 = 皮肤区域 × 边缘保护
    final_mask = skin_mask[:, :, np.newaxis] * edge_weight * strength
    
    # 混合
    img_f = img.astype(np.float32)
    bf_f = bf.astype(np.float32)
    result = img_f * (1 - final_mask) + bf_f * final_mask
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    return result


def remove_red_spots(img, strength=0.3):
    """去红色痘印/红斑 — 在RGB的R通道做局部平滑"""
    b, g, r = cv2.split(img.astype(np.float32))
    
    # 检测红色区域（R > G 且 R > B）
    red_mask = (r > g * 1.15) & (r > b * 1.1)
    red_mask = red_mask.astype(np.float32)
    red_mask = cv2.GaussianBlur(red_mask, (15, 15), 5)
    
    # 平滑R通道
    r_smooth = cv2.GaussianBlur(r, (0, 0), 5)
    r_new = r * (1.0 - red_mask * strength) + r_smooth * (red_mask * strength)
    r_new = np.clip(r_new, 0, 255).astype(np.uint8)
    b_u8 = b.astype(np.uint8)
    g_u8 = g.astype(np.uint8)
    
    result = cv2.merge([b_u8, g_u8, r_new])
    return result


def subtle_enhance(img, strength=0.2):
    """微小对比度增强 + 轻微锐化"""
    # 局部对比度增强（CLAHE）
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    l = cv2.addWeighted(l.astype(np.int16), 1, clahe.apply(l).astype(np.int16), strength * 0.5, 0)
    l = np.clip(l, 0, 255).astype(np.uint8)
    lab = cv2.merge([l, a, b])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    return result


def process(input_path, smooth_strength=0.5, red_strength=0.3, enhance_strength=0.2):
    print(f"处理: {os.path.basename(input_path)}")
    
    img = cv2.imread(input_path)
    if img is None:
        print("❌ 无法读取图片")
        return None
    
    h, w = img.shape[:2]
    print(f"尺寸: {w}x{h}")
    
    print("步骤1: 皮肤区域平滑去斑...")
    img = smooth_skin_only(img, strength=smooth_strength)
    
    print("步骤2: 去红色痘印...")
    img = remove_red_spots(img, strength=red_strength)
    
    print("步骤3: 轻微增强...")
    img = subtle_enhance(img, strength=enhance_strength)
    
    # 保存原分辨率
    out_png = os.path.join(OUTPUT_DIR, f"v3_{uuid.uuid4().hex[:8]}.png")
    cv2.imwrite(out_png, img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    
    # 也保存一份缩小的JPG用于预览
    scale = min(1.0, 2000 / max(w, h))
    if scale < 1:
        preview = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    else:
        preview = img
    out_jpg = os.path.join(OUTPUT_DIR, f"v3_preview_{uuid.uuid4().hex[:8]}.jpg")
    cv2.imwrite(out_jpg, preview, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    print(f"✅ 完成")
    print(f"  原分辨率: {out_png}")
    print(f"  预览: {out_jpg}")
    return out_jpg, out_png


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python skin_v3.py <图片路径> [smooth_strength=0.5] [red_strength=0.3]")
        sys.exit(1)
    
    path = sys.argv[1]
    s = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    r = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    
    result = process(path, s, r)
    if result:
        print(f"\n预览: {result[0]}")
