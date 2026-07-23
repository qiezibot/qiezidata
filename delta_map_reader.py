"""
三角洲行动 - 大地图专用识别工具
不使用通用OCR，而是：
1. 模板匹配找地名
2. 颜色分析定位撤离点标记
3. 增强截图+局部裁剪提高识别率

用法:
  python delta_map_reader.py              # 截图+分析
  python delta_map_reader.py --capture     # 只截图保存
  python delta_map_reader.py --debug       # 保存调试图
"""
import subprocess, cv2, numpy as np, sys, os, json, math

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = '1aabaaeb'
DEBUG = '--debug' in sys.argv

# ===== 零号大坝已知地名坐标（大地图全览时） =====
# 这些坐标来自于之前的成功识别的结果
KNOWN_LOCATIONS = {
    # 名称: (x_center, y_center) 在大地图上的位置
    "行政辖区": (1261, 305),
    "降落点": (1390, 446),
    "主变电站": (1350, 571),
    "游客中心": (1631, 813),
    "东区隧道": (1852, 468),
    "巴别塔": (1358, 740),
    "检查站": (735, 415),
    "雷达站": (405, 250),  # 估算
    "采石场": (1080, 620),  # 估算
    "仓库": (740, 570),  # 估算
}

def screencap():
    """获取当前屏幕截图，返回CV2 BGR图像（横屏）"""
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'],
                       capture_output=True, timeout=10)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    if img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def tap(x, y):
    """adb点击"""
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(x), str(y)],
                   capture_output=True, timeout=5)

def swipe(x1, y1, x2, y2, ms=200):
    """adb滑动"""
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe',
                   str(x1), str(y1), str(x2), str(y2), str(ms)],
                   capture_output=True, timeout=5)

def enhance_for_text(img, factor=2.0, brightness=60):
    """大幅增强截图以便识别文字"""
    enhanced = cv2.convertScaleAbs(img, alpha=factor, beta=brightness)
    return enhanced

def find_green_markers(img, min_area=40, max_area=1500):
    """
    在大地图上找绿色标记（撤离点、资源点、玩家）
    返回 [(cx, cy, area, type), ...]
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 绿色标记
    green = cv2.inRange(hsv, (35, 50, 100), (80, 200, 255))
    # 较亮的绿色
    bright_green = cv2.inRange(hsv, (40, 80, 120), (75, 180, 255))
    
    # 合并
    combined = cv2.bitwise_or(green, bright_green)
    
    # 形态学清理
    kernel = np.ones((3,3), np.uint8)
    cleaned = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    markers = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w//2, y + h//2
            
            # 判断类型：更细长的可能是文字，方块形可能是图标
            aspect = w / h if h > 0 else 0
            if 0.7 < aspect < 1.5 and area < 400:
                marker_type = "icon"  # 可能是撤离点/玩家图标
            elif 1.5 < aspect < 5.0 and area > 150:
                marker_type = "label"  # 可能是地名标签
            else:
                marker_type = "other"
            
            markers.append((cx, cy, area, marker_type, w, h))
    
    return markers

def extract_text_region(img, x, y, radius=40):
    """提取以(x,y)为中心的区域做OCR"""
    h, w = img.shape[:2]
    x1 = max(0, x - radius)
    y1 = max(0, y - radius)
    x2 = min(w, x + radius)
    y2 = min(h, y + radius)
    region = img[y1:y2, x1:x2]
    # 放大
    region = cv2.resize(region, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return region, (x1, y1)

def read_region_text(region):
    """对局部区域做简单的文字裁剪+识别"""
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    
    # 自适应二值化
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    
    # 形态学：连接文字
    kernel = np.ones((1, 2), np.uint8)
    connected = cv2.dilate(binary, kernel, iterations=1)
    
    h, w = region.shape[:2]
    # 找前景像素的分布来确定文字区域
    col_proj = cv2.reduce(255 - connected, 0, cv2.REDUCE_AVG).flatten()
    row_proj = cv2.reduce(255 - connected, 1, cv2.REDUCE_AVG).flatten()
    
    # 列投影找到文字左右边界
    col_thresh = np.max(col_proj) * 0.3
    cols_above = np.where(col_proj > col_thresh)[0]
    
    row_thresh = np.max(row_proj) * 0.3
    rows_above = np.where(row_proj > row_thresh)[0]
    
    if len(cols_above) > 5 and len(rows_above) > 5:
        l, r = cols_above[0], cols_above[-1]
        t, b = rows_above[0], rows_above[-1]
        # 扩大一点
        l = max(0, l - 5)
        r = min(w, r + 5)
        t = max(0, t - 5)
        b = min(h, b + 5)
        cropped = binary[t:b, l:r]
        return cropped, (l, r, t, b)
    return binary, (0, w, 0, h)

# ===== 模板匹配识字模块 =====
# 对每个候选区域，截取后尝试用EasyOCR识别（只对小区域，速度快）
def ocr_regions_with_easyocr(img, regions, reader=None):
    """
    对图像上的多个区域分别做OCR
    regions: [(cx, cy, radius), ...]
    reader: easyocr reader 实例，没有则创建
    """
    import easyocr
    if reader is None:
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    
    results = []
    for cx, cy, radius in regions:
        x1 = max(0, cx - radius)
        y1 = max(0, cy - radius)
        x2 = min(img.shape[1], cx + radius)
        y2 = min(img.shape[0], cy + radius)
        
        region = img[y1:y2, x1:x2]
        
        # 放大2倍+增强
        region_big = cv2.resize(region, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(region_big, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(4,4))
        enhanced = clahe.apply(gray)
        # 重新彩色化
        enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        # 临时保存
        tmp_path = r'C:\temp\delta_ocr_crop.png'
        cv2.imwrite(tmp_path, enhanced_color)
        
        # 用EasyOCR
        try:
            r_results = reader.readtext(tmp_path, paragraph=False)
            for bbox, text, conf in r_results:
                if conf > 0.3:
                    # 坐标还原到原图
                    ocr_cx = int((bbox[0][0] + bbox[2][0]) / 2) // 3 + x1
                    ocr_cy = int((bbox[0][1] + bbox[2][1]) / 2) // 3 + y1
                    results.append((text, ocr_cx, ocr_cy, conf))
        except:
            pass
    
    return results

def try_read_map_labels(img, marker_positions):
    """
    对每个绿色标记旁边读文字（尝试下右上方40-100像素范围内）
    marker_positions: [(cx, cy), ...]
    """
    import easyocr
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    
    all_results = []
    for cx, cy in marker_positions:
        # 在标记的右侧和上方搜索文字
        for dx, dy in [(40, -10), (50, 0), (60, 0), (30, -20), (45, -15)]:
            tx, ty = cx + dx, cy + dy
            region = img[max(0,ty-15):ty+15, max(0,tx-30):tx+30]
            if region.shape[0] < 5 or region.shape[1] < 5:
                continue
            
            region_big = cv2.resize(region, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(region_big, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
            enhanced = clahe.apply(gray)
            
            tmp = r'C:\temp\delta_label_read.png'
            cv2.imwrite(tmp, enhanced)
            
            r_res = reader.readtext(tmp, paragraph=False)
            for bbox, text, conf in r_res:
                if conf > 0.3 and len(text) >= 2:
                    ocr_cx = int((bbox[0][0]+bbox[2][0])/2) // 4 + tx - 30
                    ocr_cy = int((bbox[0][1]+bbox[2][1])/2) // 4 + ty - 15
                    all_results.append((text, ocr_cx, ocr_cy, conf))
    
    return all_results

def is_battle_preset(img):
    """判断是否在游戏内（战斗画面）还是在大地图"""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = gray.mean()
    
    # 顶部检测普通/高级按钮
    top_20 = gray[:20, :]
    top_mean = top_20.mean()
    
    # 检测是否有地图图层（深色半透明覆盖）
    center = gray[h//4:3*h//4, w//4:3*w//4]
    center_mean = center.mean()
    
    return {
        "mean_brightness": float(mean_val),
        "top_mean": float(top_mean),
        "center_mean": float(center_mean),
        "is_map_open": center_mean < mean_val * 0.8,  # 地图有暗色覆盖层
        "is_ingame": mean_val > 50 and mean_val < 180,
    }

def open_map():
    """打开游戏内大地图"""
    tap(290, 209)
    import time
    time.sleep(2)
    return screencap()

def close_map():
    """关闭游戏内大地图"""
    tap(2250, 80)
    import time
    time.sleep(1)

def capture_map_with_enhance():
    """
    增强截图流程：
    1. 开地图
    2. adb screencap
    3. 增强亮度
    4. 返回多个亮度版本的图片
    """
    img = open_map()
    if img is None:
        return None, None, None
    
    original = img.copy()
    
    # 多级增强
    bright1 = enhance_for_text(img, 1.5, 40)
    bright2 = enhance_for_text(img, 2.0, 60)
    bright3 = enhance_for_text(img, 3.0, 80)
    
    # CLAHE 自适应增强
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge([cl, a, b])
    clahe_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    if DEBUG:
        cv2.imwrite(r'C:\temp\delta_map_original.png', original)
        cv2.imwrite(r'C:\temp\delta_map_bright2.png', bright2)
        cv2.imwrite(r'C:\temp\delta_map_clahe.png', clahe_img)
    
    return original, bright2, clahe_img

def extract_map_icons_and_text(img, enhanced):
    """分析地图图标和文字"""
    h, w = img.shape[:2]
    results = {
        "green_markers": [],
        "map_info": {
            "width": w,
            "height": h,
        },
        "extraction_zones": [],
    }
    
    green_markers = find_green_markers(img)
    
    # 过滤：排除过于靠近边缘的（可能是UI元素）
    filtered_markers = []
    for cx, cy, area, mtype, mw, mh in green_markers:
        if cx < 50 or cx > w - 50 or cy < 30 or cy > h - 30:
            continue
        filtered_markers.append((cx, cy, area, mtype, mw, mh))
    
    # 标记类型分类
    icons = [(cx, cy) for cx, cy, a, t, w_, h_ in filtered_markers if t == "icon" and 40 < a < 300]
    labels = [(cx, cy) for cx, cy, a, t, w_, h_ in filtered_markers if t == "label" and a > 150]
    
    results["green_markers"] = [{"x": cx, "y": cy, "area": area, "type": mtype, "w": mw, "h": mh} 
                                 for cx, cy, area, mtype, mw, mh in filtered_markers]
    results["icons_count"] = len(icons)
    results["labels_count"] = len(labels)
    
    return results

def try_match_location(markers, known=KNOWN_LOCATIONS):
    """
    尝试匹配已知地名到检测到的绿色标记附近
    返回最可能的撤离点候选
    """
    matches = []
    for name, (lx, ly) in known.items():
        best_dist = 99999
        for mx, my in [(m["x"], m["y"]) for m in markers if m["type"] in ["icon", "label"]]:
            dist = math.sqrt((lx - mx)**2 + (ly - my)**2)
            if dist < best_dist:
                best_dist = dist
        if best_dist < 50:
            matches.append((name, lx, ly, best_dist))
    
    return matches

def main():
    print("🔍 三角洲行动 - 大地图识别工具")
    print("=" * 40)
    
    if '--capture' in sys.argv:
        img = screencap()
        if img is not None:
            cv2.imwrite(r'C:\temp\delta_capture.png', img)
            print(f"截图已保存: C:\\temp\\delta_capture.png ({img.shape[1]}x{img.shape[0]})")
        return
    
    # 判断状态
    img_before = screencap()
    if img_before is None:
        print("❌ 截图失败")
        return
    
    status = is_battle_preset(img_before)
    print(f"\n📊 画面状态:")
    print(f"  平均亮度: {status['mean_brightness']:.0f}")
    print(f"  顶部亮度: {status['top_mean']:.0f}")
    print(f"  中间亮度: {status['center_mean']:.0f}")
    print(f"  地图已打开: {status['is_map_open']}")
    print(f"  游戏内: {status['is_ingame']}")
    
    if not status['is_map_open']:
        print("\n🔄 正在打开地图...")
        img, enhanced, clahe_img = capture_map_with_enhance()
        if img is None:
            print("❌ 截图失败")
            return
    else:
        img = img_before.copy()
        enhanced = enhance_for_text(img, 2.0, 60)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        merged = cv2.merge([cl, a, b])
        clahe_img = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    print(f"\n📐 地图尺寸: {img.shape[1]}x{img.shape[0]}")
    print(f"💡 亮度: 原图={img.mean():.0f} 增强={enhanced.mean():.0f} CLAHE={clahe_img.mean():.0f}")
    
    # 检测绿色标记
    markers = find_green_markers(img)
    print(f"\n🟢 绿色标记检测:")
    print(f"  总数: {len(markers)}")
    
    # 分类
    icons = [(cx, cy, area) for cx, cy, area, t, w_, h_ in markers if t == "icon"]
    labels = [(cx, cy, area) for cx, cy, area, t, w_, h_ in markers if t == "label"]
    others = [(cx, cy, area) for cx, cy, area, t, w_, h_ in markers if t == "other"]
    
    print(f"  图标(可能撤离点): {len(icons)}")
    for cx, cy, area in icons[:10]:
        print(f"    ({cx}, {cy}) 面积={area:.0f}")
    
    if labels:
        print(f"  标签: {len(labels)}")
        for cx, cy, area in labels[:5]:
            print(f"    ({cx}, {cy}) 面积={area:.0f}")
    
    # 尝试关联已知地名
    if icons or labels:
        marker_list = []
        for cx, cy, area, t, w_, h_ in markers:
            marker_list.append({"x": cx, "y": cy, "area": area, "type": t, "w": w_, "h": h_})
        matches = try_match_location(marker_list)
        if matches:
            print(f"\n📍 已知地名匹配:")
            for name, lx, ly, dist in matches:
                print(f"  {name}: 预计({lx},{ly}) 距离={dist:.0f}px")
    
    # 保存调试图
    if DEBUG or True:
        debug = img.copy()
        for cx, cy, area, mtype, mw, mh in markers:
            color = (0, 255, 0) if mtype == "icon" else (0, 200, 200) if mtype == "label" else (100, 100, 100)
            cv2.circle(debug, (cx, cy), 3, color, 2)
            cv2.rectangle(debug, (cx-mw//2, cy-mh//2), (cx+mw//2, cy+mh//2), color, 1)
        
        # 标注已知地名
        for name, (lx, ly) in KNOWN_LOCATIONS.items():
            cv2.putText(debug, name, (lx-30, ly-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
        
        cv2.imwrite(r'C:\temp\delta_map_analyzed.png', debug)
        cv2.imwrite(r'C:\temp\delta_map_enhanced.png', enhanced)
        cv2.imwrite(r'C:\temp\delta_map_clahe_final.png', clahe_img)
        print(f"\n💾 调试图保存: C:\\temp\\delta_map_analyzed.png")
    
    # 输出JSON（给其他脚本用）
    output = {
        "brightness": float(img.mean()),
        "enhanced_brightness": float(enhanced.mean()),
        "map_open": True,
        "markers_count": len(markers),
        "icon_markers": [{"x": cx, "y": cy, "area": area} for cx, cy, area in icons],
        "label_markers": [{"x": cx, "y": cy, "area": area} for cx, cy, area in labels],
    }
    
    output_path = r'C:\temp\delta_map_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📋 数据保存: {output_path}")
    
    return output

if __name__ == '__main__':
    main()
