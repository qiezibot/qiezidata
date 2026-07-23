"""
去斑 v6 — 全面去除黑白黄各种斑点
策略：HSV+HLS双色彩空间检测 → 合并所有斑类型 → 强力修补
"""

import cv2
import numpy as np
import os
import sys
import uuid

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def detect_all_spots(img):
    """多维度检测所有类型斑点"""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    combined_mask = np.zeros((h, w), dtype=np.uint8)
    
    # ========== 1. 黑帽检测深色斑点（痣/雀斑） ==========
    for ksize in [(5,5), (11,11), (21,21)]:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ksize)
        bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k)
        _, spots = cv2.threshold(bh, 6, 255, cv2.THRESH_BINARY)
        combined_mask = cv2.bitwise_or(combined_mask, spots)
    
    # ========== 2. HSV检测黄斑/褐斑 ==========
    h_ch, s_ch, v_ch = cv2.split(hsv)
    
    # 黄褐色范围: H 10-30, S > 40, V 中等
    yellow_mask1 = cv2.inRange(hsv, np.array([8, 30, 60]), np.array([35, 255, 200]))
    
    # 棕褐色范围: H 0-20, S > 50, V 较低
    brown_mask = cv2.inRange(hsv, np.array([0, 40, 40]), np.array([20, 255, 150]))
    
    # 红色痘印范围: H 160-180, S > 60
    red_mask = cv2.inRange(hsv, np.array([160, 50, 40]), np.array([180, 255, 200]))
    
    for color_mask in [yellow_mask1, brown_mask, red_mask]:
        # 形态学提取斑点结构
        k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, k3, iterations=1)
        combined_mask = cv2.bitwise_or(combined_mask, cleaned)
    
    # ========== 3. LAB色差检测 ==========
    l_ch, a_ch, b_ch = cv2.split(lab)
    
    # A通道（绿到红）：红色斑点在A通道值高
    _, a_high = cv2.threshold(a_ch, 135, 255, cv2.THRESH_BINARY)
    # B通道（蓝到黄）：黄色斑点在B通道值高
    _, b_high = cv2.threshold(b_ch, 140, 255, cv2.THRESH_BINARY)
    
    for cm in [a_high, b_high]:
        k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(cm, cv2.MORPH_OPEN, k3, iterations=1)
        combined_mask = cv2.bitwise_or(combined_mask, cleaned)
    
    # ========== 4. 滤波：只保留小尺寸斑点 ==========
    # 去掉太大区域（不是斑点）
    k_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    large_regions = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, k_large)
    combined_mask = cv2.bitwise_xor(combined_mask, large_regions)
    
    # 去掉太小的噪点
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, k2, iterations=1)
    
    # ========== 5. 提取连通域 ==========
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(combined_mask, connectivity=8)
    
    spots = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if 3 <= area <= 500:
            cx, cy = int(centroids[i][0]), int(centroids[i][1])
            r = max(int(np.sqrt(area / np.pi)) + 1, 2)
            spots.append((cx, cy, r, area))
    
    print(f"[v6] 检测到 {len(spots)} 个斑点 (共{num_labels-1}个连通域)")
    return spots, combined_mask


def multi_pass_inpaint(img, spots):
    """多轮修补：用不同算法逐步填补"""
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    for (cx, cy, r, area) in spots:
        if area < 8:
            radius = max(int(r * 3), 3)
        elif area < 20:
            radius = max(int(r * 2.5), 4)
        elif area < 50:
            radius = max(int(r * 2.0), 5)
        else:
            radius = max(int(r * 1.8), 6)
        cv2.circle(mask, (cx, cy), radius, 255, -1)
    
    # 第1轮：Telea快速填充
    r1 = cv2.inpaint(img, mask, 2, cv2.INPAINT_TELEA)
    # 第2轮：NS精细修补
    r2 = cv2.inpaint(r1, mask, 1, cv2.INPAINT_NS)
    # 第3轮：再补一次
    r3 = cv2.inpaint(r2, mask, 1, cv2.INPAINT_TELEA)
    
    return r3


def skin_blend(original, processed):
    """
    只在皮肤区域内混合，保护非皮肤区域完全不变
    """
    h, w = original.shape[:2]
    
    # 检测皮肤
    ycrcb = cv2.cvtColor(original, cv2.COLOR_BGR2YCrCb)
    skin = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
    skin_f = cv2.GaussianBlur(skin.astype(np.float32), (31, 31), 15) / 255.0
    
    result = (original.astype(np.float32) * (1.0 - skin_f[:, :, np.newaxis]) +
              processed.astype(np.float32) * skin_f[:, :, np.newaxis])
    return np.clip(result, 0, 255).astype(np.uint8)


def process(input_path):
    print(f"处理: {os.path.basename(input_path)}")
    
    original = cv2.imread(input_path)
    if original is None:
        print("❌ 读取失败")
        return None
    
    h, w = original.shape[:2]
    print(f"尺寸: {w}x{h}")
    
    # 1. 多维度检测
    print("步骤1: 多维度检测（黑斑+黄斑+红斑+褐斑）...")
    spots, spot_mask = detect_all_spots(original)
    
    if not spots:
        print("⚠️ 未检测到斑点")
        return None
    
    # 2. 强力修补
    print("步骤2: 三轮修补...")
    inpainted = multi_pass_inpaint(original, spots)
    
    # 3. 只在皮肤区域混合
    print("步骤3: 皮肤区域混合...")
    result = skin_blend(original, inpainted)
    
    # 保存
    uid = uuid.uuid4().hex[:8]
    out_png = os.path.join(OUTPUT_DIR, f"v6_{uid}.png")
    cv2.imwrite(out_png, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    
    # 预览
    scale = min(1.0, 2000 / max(w, h))
    preview = cv2.resize(result, (int(w*scale), int(h*scale))) if scale < 1 else result
    out_jpg = os.path.join(OUTPUT_DIR, f"v6_preview_{uid}.jpg")
    cv2.imwrite(out_jpg, preview, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    # 标记图（用不同颜色标不同类型的斑）
    debug = original.copy()
    for (cx, cy, r, area) in spots:
        color = (0, 0, 255) if area < 15 else (255, 0, 0) if area < 30 else (0, 255, 255)
        cv2.circle(debug, (cx, cy), max(r, 2), color, 1)
    ds = min(1.0, 1200 / max(w, h))
    debug_out = os.path.join(OUTPUT_DIR, f"v6_debug_{uid}.jpg")
    debug_small = cv2.resize(debug, (int(w*ds), int(h*ds)))
    cv2.imwrite(debug_out, debug_small, [cv2.IMWRITE_JPEG_QUALITY, 85])
    
    print(f"✅ 完成")
    print(f"预览: {out_jpg}")
    return out_jpg, out_png, debug_out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python spot_v6.py <图片路径>")
        sys.exit(1)
    
    result = process(sys.argv[1])
    if result:
        print(f"\n结果: {result[0]}")
