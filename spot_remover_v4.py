"""
精准去斑去痣 v4
策略：在原图上精确定位斑点位置 → 缩放比对 → 局部Inpaint
不依赖AI，不变形
"""

import cv2
import numpy as np
import os
import sys
import uuid

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def detect_dark_spots(img):
    """
    精确检测深色斑点（痣/雀斑）
    在多个颜色空间中检测暗色小区域
    """
    h, w = img.shape[:2]
    
    # 1. 在灰度图中检测暗色区域
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 自适应阈值找到暗斑
    block_size = min(151, w if w % 2 == 1 else w + 1)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, block_size, 10)
    
    # 2. 在LAB空间的A通道找红色/棕色斑点
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a_ch, b_ch = cv2.split(lab)
    
    # 痣通常在L通道较暗
    _, l_dark = cv2.threshold(l, 80, 255, cv2.THRESH_BINARY_INV)
    
    # 3. 合并检测结果
    combined = cv2.bitwise_and(thresh, l_dark)
    
    # 形态学过滤（去掉小噪点，保留圆形斑点）
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, k3, iterations=1)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k5, iterations=1)
    
    # 4. 找到连通区域
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(combined, connectivity=8)
    
    spots = []
    min_area = 8   # 最小斑点面积（像素）
    max_area = 800  # 最大斑点面积
    
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            cw = stats[i, cv2.CC_STAT_WIDTH]
            ch = stats[i, cv2.CC_STAT_HEIGHT]
            cx, cy = int(centroids[i][0]), int(centroids[i][1])
            
            # 计算斑点的圆度
            if cw > 0 and ch > 0:
                aspect_ratio = max(cw, ch) / min(cw, ch)
                # 痣通常是类圆形（长宽比不超过2.5）
                if aspect_ratio < 2.5:
                    radius = max(int(np.sqrt(area / np.pi)) + 1, 2)
                    spots.append((cx, cy, radius, area))
    
    print(f"[检测] 找到 {len(spots)} 个斑点")
    return spots, combined


def create_spots_mask(h, w, spots, radius_scale=1.8):
    """生成斑点遮罩"""
    mask = np.zeros((h, w), dtype=np.uint8)
    for (cx, cy, r, area) in spots:
        r_pad = max(int(r * radius_scale), 3)
        cv2.circle(mask, (cx, cy), r_pad, 255, -1)
    return mask


def smart_inpaint(img, spots, method='ns'):
    """
    智能修补：对每个斑点分别修补，避免大范围模糊
    """
    result = img.copy()
    h, w = img.shape[:2]
    
    # 对大面积斑点先用Telea，再用NS精细补
    large_spots = [(cx, cy, r, a) for (cx, cy, r, a) in spots if a > 50]
    small_spots = [(cx, cy, r, a) for (cx, cy, r, a) in spots if a <= 50]
    
    if small_spots:
        mask_small = np.zeros((h, w), dtype=np.uint8)
        for (cx, cy, r, area) in small_spots:
            cv2.circle(mask_small, (cx, cy), max(int(r * 1.5), 2), 255, -1)
        result = cv2.inpaint(result, mask_small, 2, cv2.INPAINT_TELEA)
    
    if large_spots:
        mask_large = np.zeros((h, w), dtype=np.uint8)
        for (cx, cy, r, area) in large_spots:
            cv2.circle(mask_large, (cx, cy), max(int(r * 2.0), 3), 255, -1)
        result = cv2.inpaint(result, mask_large, 3, cv2.INPAINT_NS)
    
    return result


def local_blend(original, processed, spots, feather_radius=5):
    """局部羽化混合，让修补边缘自然过渡"""
    h, w = original.shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    
    for (cx, cy, r, area) in spots:
        cv2.circle(mask, (cx, cy), max(int(r * 3), feather_radius), 1.0, -1)
    
    # 高斯模糊遮罩边缘
    mask = cv2.GaussianBlur(mask, (0, 0), feather_radius)
    mask = np.clip(mask, 0, 1)
    
    result = (original.astype(np.float32) * (1.0 - mask[:, :, np.newaxis]) +
              processed.astype(np.float32) * mask[:, :, np.newaxis])
    return np.clip(result, 0, 255).astype(np.uint8)


def process(input_path, sensitivity=8, radius_scale=1.8):
    """
    sensitivity: 最小斑点面积（越小越敏感）
    radius_scale: 修补半径倍数（越大修补范围越大）
    """
    print(f"处理: {os.path.basename(input_path)}")
    
    img = cv2.imread(input_path)
    if img is None:
        print("❌ 无法读取图片")
        return None
    
    h, w = img.shape[:2]
    print(f"尺寸: {w}x{h}")
    
    # 1. 检测斑点
    print("步骤1: 检测斑点...")
    spots, dark_mask = detect_dark_spots(img)
    
    if not spots:
        print("⚠️ 未检测到斑点")
        return None
    
    # 2. 智能修补
    print("步骤2: Inpaint修补...")
    inpainted = smart_inpaint(img, spots)
    
    # 3. 局部羽化混合，让修补边缘自然
    print("步骤3: 边缘混合...")
    result = local_blend(img, inpainted, spots, feather_radius=5)
    
    # 保存原分辨率版本
    out_png = os.path.join(OUTPUT_DIR, f"v4_{uuid.uuid4().hex[:8]}.png")
    cv2.imwrite(out_png, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    
    # 预览版
    scale = min(1.0, 2000 / max(w, h))
    if scale < 1:
        preview = cv2.resize(result, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    else:
        preview = result
    out_jpg = os.path.join(OUTPUT_DIR, f"v4_preview_{uuid.uuid4().hex[:8]}.jpg")
    cv2.imwrite(out_jpg, preview, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    # 也保存一张标记图，看看检测到了哪些位置
    debug = img.copy()
    for (cx, cy, r, area) in spots:
        cv2.circle(debug, (cx, cy), r, (0, 0, 255), 1)
    debug_scale = min(1.0, 1500 / max(w, h))
    debug_small = cv2.resize(debug, (int(w*debug_scale), int(h*debug_scale)))
    debug_out = os.path.join(OUTPUT_DIR, f"v4_debug_{uuid.uuid4().hex[:8]}.jpg")
    cv2.imwrite(debug_out, debug_small, [cv2.IMWRITE_JPEG_QUALITY, 85])
    
    print(f"✅ 完成 (检测到 {len(spots)} 个斑点)")
    print(f"  原分辨率: {out_png}")
    print(f"  预览: {out_jpg}")
    print(f"  标记图: {debug_out}")
    return out_jpg, out_png, debug_out, len(spots)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python spot_remover_v4.py <图片路径> [sensitivity=8] [radius_scale=1.8]")
        print("  sensitivity: 越小越敏感，默认8像素")
        print("  radius_scale: 修补半径倍数，越大补得越宽")
        sys.exit(1)
    
    path = sys.argv[1]
    sens = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    rs = float(sys.argv[3]) if len(sys.argv) > 3 else 1.8
    
    result = process(path, sens, rs)
    if result:
        print(f"\n预览: {result[0]}")
        print(f"标记图: {result[2]}")
