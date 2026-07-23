"""
去斑去痣 v5 — 形态学黑帽 + 多尺度检测
核心思路：
1. 原图不缩不降质
2. 用Morphological BlackHat提取暗色小结构
3. 多尺度检测（不同大小斑点分开处理）
4. 逐点Inpaint
"""

import cv2
import numpy as np
import os
import sys
import uuid
from collections import defaultdict

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def detect_spots_blackhat(img):
    """
    用黑帽变换 + 多尺度检测
    黑帽 = 闭运算 - 原图，提取暗色小结构
    """
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 多尺度检测：不同大小的核抓不同大小的斑点
    all_spots_mask = np.zeros((h, w), dtype=np.uint8)
    
    # 小斑点 (3-8像素)
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    blackhat1 = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k1)
    _, spots1 = cv2.threshold(blackhat1, 8, 255, cv2.THRESH_BINARY)
    all_spots_mask = cv2.bitwise_or(all_spots_mask, spots1)
    
    # 中斑点 (8-15像素)
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    blackhat2 = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k2)
    _, spots2 = cv2.threshold(blackhat2, 12, 255, cv2.THRESH_BINARY)
    all_spots_mask = cv2.bitwise_or(all_spots_mask, spots2)
    
    # 大斑点 (15-30像素)
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    blackhat3 = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k3)
    _, spots3 = cv2.threshold(blackhat3, 18, 255, cv2.THRESH_BINARY)
    all_spots_mask = cv2.bitwise_or(all_spots_mask, spots3)
    
    # 去掉太暗的全局阴影（不是斑点）
    _, global_dark = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
    all_spots_mask = cv2.bitwise_and(all_spots_mask, cv2.bitwise_not(global_dark))
    
    # 形态学清理
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    all_spots_mask = cv2.morphologyEx(all_spots_mask, cv2.MORPH_OPEN, k3, iterations=1)
    all_spots_mask = cv2.morphologyEx(all_spots_mask, cv2.MORPH_CLOSE, k3, iterations=1)
    
    # 提取连通域
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(all_spots_mask, connectivity=8)
    
    spots = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if 3 <= area <= 400:  # 3-400像素的斑点
            x, y, cw, ch = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            cx, cy = int(centroids[i][0]), int(centroids[i][1])
            r = max(int(np.sqrt(area / np.pi)) + 1, 2)
            spots.append((cx, cy, r, area, x, y, cw, ch))
    
    print(f"[黑帽] 检测到 {len(spots)} 个斑点")
    return spots, all_spots_mask


def detect_dark_skin_pixels(img):
    """
    补充检测：皮肤区域内的深色像素（痣通常在肤色区域）
    """
    h, w = img.shape[:2]
    
    # 皮肤检测
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    skin = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
    
    # 在皮肤区域内找深色像素
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, dark = cv2.threshold(gray, 85, 255, cv2.THRESH_BINARY_INV)
    
    skin_dark = cv2.bitwise_and(dark, skin)
    
    # 去掉小噪点
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    skin_dark = cv2.morphologyEx(skin_dark, cv2.MORPH_OPEN, k3, iterations=1)
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(skin_dark, connectivity=8)
    
    extra_spots = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if 4 <= area <= 300:
            cx, cy = int(centroids[i][0]), int(centroids[i][1])
            r = max(int(np.sqrt(area / np.pi)) + 1, 2)
            extra_spots.append((cx, cy, r, area, 0, 0, 0, 0))
    
    print(f"[皮肤暗点] 额外检测到 {len(extra_spots)} 个")
    return extra_spots, skin_dark


def aggressive_inpaint(img, spots, method='ns'):
    """
    强力修补：每个斑点独立修补，半径放大以确保覆盖
    """
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # 按大小分组，小斑点用更小半径，大斑点用更大半径
    for (cx, cy, r, area, x, y, cw, ch) in spots:
        if area < 10:
            radius = max(int(r * 2.5), 3)
        elif area < 30:
            radius = max(int(r * 2.0), 4)
        else:
            radius = max(int(r * 1.8), 5)
        cv2.circle(mask, (cx, cy), radius, 255, -1)
    
    # 先用Telea粗略补
    result1 = cv2.inpaint(img, mask, 2, cv2.INPAINT_TELEA)
    
    # 再用NS精细补
    result2 = cv2.inpaint(result1, mask, 1, cv2.INPAINT_NS)
    
    return result2


def edge_protect_blend(original, processed, spots, feather=4):
    """
    边缘保护混合：只在斑点位置用处理结果，其他地方保持原图
    """
    h, w = original.shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    
    for (cx, cy, r, area, x, y, cw, ch) in spots:
        radius = max(int(r * 3), feather)
        cv2.circle(mask, (cx, cy), radius, 1.0, -1)
    
    mask = cv2.GaussianBlur(mask, (0, 0), feather)
    mask = np.clip(mask, 0, 1)
    
    result = (original.astype(np.float32) * (1.0 - mask[:, :, np.newaxis]) +
              processed.astype(np.float32) * mask[:, :, np.newaxis])
    return np.clip(result, 0, 255).astype(np.uint8)


def process(input_path, debug_save=True):
    print(f"处理: {os.path.basename(input_path)}")
    print(f"[v5] 直接在原图操作，不依赖AI")
    
    img = cv2.imread(input_path)
    if img is None:
        print("❌ 读取失败")
        return None
    
    h, w = img.shape[:2]
    print(f"尺寸: {w}x{h}")
    
    # 去重合并斑点
    spots1, _ = detect_spots_blackhat(img)
    spots2, _ = detect_dark_skin_pixels(img)
    
    # 合并检测结果（去重）
    all_spots = spots1 + spots2
    if not all_spots:
        print("⚠️ 未检测到斑点")
        return None
    
    print(f"总计检测到 {len(all_spots)} 个斑点")
    
    print("修补中...")
    inpainted = aggressive_inpaint(img, all_spots)
    
    print("边缘混合中...")
    result = edge_protect_blend(img, inpainted, all_spots, feather=4)
    
    # 保存
    out_png = os.path.join(OUTPUT_DIR, f"v5_{uuid.uuid4().hex[:8]}.png")
    cv2.imwrite(out_png, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    
    # 预览图
    scale = min(1.0, 2000 / max(w, h))
    if scale < 1:
        preview = cv2.resize(result, (int(w*scale), int(h*scale)))
    else:
        preview = result
    out_jpg = os.path.join(OUTPUT_DIR, f"v5_preview_{uuid.uuid4().hex[:8]}.jpg")
    cv2.imwrite(out_jpg, preview, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    if debug_save:
        debug = img.copy()
        for (cx, cy, r, area, *_ ) in all_spots:
            cv2.circle(debug, (cx, cy), r, (0, 0, 255), 1)
        ds = min(1.0, 1200 / max(w, h))
        debug_small = cv2.resize(debug, (int(w*ds), int(h*ds)))
        debug_out = os.path.join(OUTPUT_DIR, f"v5_debug_{uuid.uuid4().hex[:8]}.jpg")
        cv2.imwrite(debug_out, debug_small, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"标记图: {debug_out}")
    
    print(f"✅ 完成")
    print(f"预览: {out_jpg}")
    print(f"原分辨率: {out_png}")
    return out_jpg, out_png


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python spot_v5.py <图片路径>")
        sys.exit(1)
    
    result = process(sys.argv[1])
    if result:
        print(f"\n结果: {result[0]}")
