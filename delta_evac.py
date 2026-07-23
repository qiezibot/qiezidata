"""
三角洲行动 - 撤离点识别模块
在小地图上检测绿色撤离标记，判断撤离点方向和距离
"""
import cv2
import numpy as np


def find_minimap(img):
    """
    在游戏画面中定位小地图（左上角圆形区域）
    返回小地图位置和采样数据
    """
    h, w = img.shape[:2]
    
    # 小地图通常在左上角
    top_area = img[0:300, 0:300]
    gray = cv2.cvtColor(top_area, cv2.COLOR_BGR2GRAY)
    
    # CLAHE增强对比度
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 霍夫圆检测找小地图
    blurred = cv2.GaussianBlur(enhanced, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
        param1=50, param2=25, minRadius=70, maxRadius=150
    )
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype(int)
        # 选第一个最大的圆（小地图是最大的圆形）
        circles = sorted(circles, key=lambda c: c[2], reverse=True)
        cx, cy, r = circles[0]
        return cx, cy, r, enhanced
    
    # 没找到圆形，返回默认位置
    return 140, 140, 120, enhanced


def find_evac_markers(img, minimap_center=None, minimap_radius=None):
    """
    在小地图上检测绿色撤离标记
    返回撤离点相对玩家方向角度和可见性
    """
    h, w = img.shape[:2]
    
    # 定位小地图
    cx, cy, r, _ = find_minimap(img)
    if minimap_center:
        cx, cy = minimap_center
    if minimap_radius:
        r = minimap_radius
    
    # 小地图区域
    x1, y1 = max(0, cx - r - 5), max(0, cy - r - 5)
    x2, y2 = min(w, cx + r + 5), min(h, cy + r + 5)
    minimap_roi = img[y1:y2, x1:x2]
    
    if minimap_roi.size == 0:
        return None, None, None
    
    # 转HSV
    hsv = cv2.cvtColor(minimap_roi, cv2.COLOR_BGR2HSV)
    
    # 绿色撤离标记检测：
    # 三角洲行动中绿色标记通常为纯绿色三角形/人形，HSV范围较窄
    green_mask = cv2.inRange(hsv, (40, 80, 80), (80, 255, 255))
    
    # 排除圆形边框上的误检
    mask_circle = np.zeros(green_mask.shape, dtype=np.uint8)
    center_local = (minimap_roi.shape[1] // 2, minimap_roi.shape[0] // 2)
    cv2.circle(mask_circle, center_local, r - 5, 255, -1)
    green_mask = cv2.bitwise_and(green_mask, mask_circle)
    
    # 找绿色点
    green_pixels = cv2.findNonZero(green_mask)
    
    if green_pixels is not None and len(green_pixels) > 5:
        # 聚类绿色点（可能有多个撤离点）
        # 用简单方法：取第一个明显绿色区域
        x, y, gw, gh = cv2.boundingRect(green_pixels)
        marker_cx = x + gw // 2
        marker_cy = y + gh // 2
        
        # 计算相对角度（以小地图中心为原点，上为北）
        dx = marker_cx - center_local[0]
        dy = marker_cy - center_local[1]
        angle = np.degrees(np.arctan2(dx, -dy))  # 上=0, 右=90, 下=180, 左=-90
        if angle < 0:
            angle += 360
        
        # 检测到的绿色像素数量
        pixel_count = len(green_pixels)
        
        return angle, (marker_cx + x1, marker_cy + y1), pixel_count
    
    return None, None, 0


def detect_nearby_evac_text(img):
    """
    检测画面中"撤离点"相关文字和距离
    使用简单颜色分析法，不依赖OCR
    """
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 当接近撤离点时，屏幕上会出现白色/黄色文字和距离提示
    # 检测底部区域（通常显示交互提示）
    bot = img[int(h * 0.85):h, :]
    bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    
    # 白色文字区域（交互提示通常为白色字体）
    white_text = cv2.inRange(bot_hsv, (0, 0, 200), (180, 30, 255))
    white_count = cv2.countNonZero(white_text)
    
    # 检查底部是否有大量白色文字（撤离点交互提示）
    return white_count > 100


def detect_hud_indicators(img):
    """
    检测游戏内基本HUD元素（用于判断是否在游戏内）
    """
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = g.mean()
    
    # 检查关键HUD位置
    # 1. 顶部坐标区域 (30-170, 30-70)
    coord_area = img[25:75, 25:175]
    coord_gray = cv2.cvtColor(coord_area, cv2.COLOR_BGR2GRAY)
    coord_text = cv2.mean(coord_gray)[0] < 200  # 有深色文字
    
    # 2. 底部血条区域
    hp_area = img[int(h * 0.88):int(h * 0.95), 250:450]
    hp_hsv = cv2.cvtColor(hp_area, cv2.COLOR_BGR2HSV)
    hp_red = cv2.inRange(hp_hsv, (0, 50, 50), (10, 255, 255)) | cv2.inRange(hp_hsv, (160, 50, 50), (180, 255, 255))
    has_hp = cv2.countNonZero(hp_red) > 50
    
    return {
        'brightness': m,
        'has_coord': coord_text,
        'has_hp': has_hp,
        'in_game': m < 160 and m > 40 and has_hp
    }


def find_compass_direction(img):
    """
    检测顶部的方向指示（北/东北/东等）
    """
    top = img[0:60, 750:1300]
    hsv = cv2.cvtColor(top, cv2.COLOR_BGR2HSV)
    # 方向文字的典型颜色：白色/亮青色
    text_mask = cv2.inRange(hsv, (0, 0, 180), (180, 50, 255))
    return cv2.countNonZero(text_mask) > 50


if __name__ == "__main__":
    import subprocess, sys
    
    adb = r'D:\MuMuPlayer\nx_main\adb.exe'
    phone = '1aabaaeb'
    
    # 截图
    r = subprocess.run([adb, '-s', phone, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=10)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        print("截图失败")
        sys.exit(1)
    
    if img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    
    # 检测
    cx, cy, r, _ = find_minimap(img)
    print(f"小地图中心: ({cx},{cy}) 半径: {r}")
    
    angle, pos, count = find_evac_markers(img)
    if angle is not None:
        dirs = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
        idx = int((angle + 22.5) / 45) % 8
        dir_text = dirs[idx]
        print(f"撤离标记: 方向{dir_text}({angle:.0f}°) 像素{count}")
    else:
        print("未检测到绿色撤离标记")
    
    hud = detect_hud_indicators(img)
    print(f"HUD: 亮度={hud['brightness']:.0f} 坐标={'有' if hud['has_coord'] else '无'} 血条={'有' if hud['has_hp'] else '无'} 游戏内={'是' if hud['in_game'] else '否'}")
    
    # 保存分析图
    debug = img.copy()
    cv2.circle(debug, (cx, cy), r, (0, 255, 0), 2)
    if pos:
        cv2.circle(debug, pos, 5, (0, 0, 255), -1)
    cv2.imwrite(r'C:\temp\delta_evac_debug.png', debug)
    print("分析图已保存到 C:\\temp\\delta_evac_debug.png")
