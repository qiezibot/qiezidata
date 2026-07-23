"""
三角洲行动 - 撤离导航模块
结合小地图绿色标记检测 + 摇杆控制，引导人物走向撤离点
"""

import cv2
import numpy as np
import subprocess
import time
import sys

# 固定参数
ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = '1aabaaeb'
JOYSTICK_CENTER = (265, 793)  # 摇杆中心
SCREEN_W, SCREEN_H = 2340, 1080

# 方向映射：角度→摇杆滑动方向
# 上=0°, 右=90°, 下=180°, 左=270°
DIRECTION_MAP = {
    0: (265, 400),    # 北（上）
    45: (600, 450),   # 东北
    90: (800, 500),   # 东（右）
    135: (600, 650),  # 东南（右前）
    180: (265, 900),  # 南（下）
    225: (100, 650),  # 西南（左后）
    270: (100, 500),  # 西（左）
    315: (100, 450),  # 西北（左前）
}


def screenshot():
    """从手机截图并返回OpenCV图像"""
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=10)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    if img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def find_minimap(img):
    """定位小地图"""
    top_area = img[0:300, 0:300]
    gray = cv2.cvtColor(top_area, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(enhanced, (9, 9), 2)
    
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
        param1=50, param2=25, minRadius=70, maxRadius=150
    )
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype(int)
        circles = sorted(circles, key=lambda c: c[2], reverse=True)
        return circles[0][0], circles[0][1], circles[0][2]
    return 140, 140, 120


def find_evac_markers(img, mm_cx, mm_cy, mm_r):
    """在小地图上找绿色撤离标记"""
    h, w = img.shape[:2]
    
    x1, y1 = max(0, mm_cx - mm_r - 5), max(0, mm_cy - mm_r - 5)
    x2, y2 = min(w, mm_cx + mm_r + 5), min(h, mm_cy + mm_r + 5)
    minimap_roi = img[y1:y2, x1:x2]
    
    if minimap_roi.size == 0:
        return None, None
    
    hsv = cv2.cvtColor(minimap_roi, cv2.COLOR_BGR2HSV)
    
    # 检测绿色标记（撤离点）：比较亮的纯绿色
    green_mask = cv2.inRange(hsv, (40, 80, 80), (80, 255, 255))
    
    # 只保留小地图圆形内部
    center_local = (minimap_roi.shape[1] // 2, minimap_roi.shape[0] // 2)
    circle_mask = np.zeros(green_mask.shape, dtype=np.uint8)
    cv2.circle(circle_mask, center_local, mm_r - 3, 255, -1)
    green_mask = cv2.bitwise_and(green_mask, circle_mask)
    
    # 也检测蓝色标记（队友），排除掉
    blue_mask = cv2.inRange(hsv, (100, 80, 80), (130, 255, 255))
    blue_mask = cv2.bitwise_and(blue_mask, circle_mask)
    
    green_pixels = cv2.findNonZero(green_mask)
    if green_pixels is not None and len(green_pixels) > 5:
        x, y, gw, gh = cv2.boundingRect(green_pixels)
        marker_cx = x + gw // 2
        marker_cy = y + gh // 2
        
        dx = marker_cx - center_local[0]
        dy = marker_cy - center_local[1]
        angle = np.degrees(np.arctan2(dx, -dy))
        if angle < 0:
            angle += 360
        
        # 距离小地图中心的像素距离（相对百分比）
        dist_px = np.sqrt(dx**2 + dy**2)
        dist_pct = dist_px / mm_r * 100
        
        return angle, dist_pct
    
    return None, None


def angle_to_swipe(angle):
    """角度→摇杆滑动目标坐标"""
    closest = min(DIRECTION_MAP.keys(), key=lambda k: abs(k - angle))
    return DIRECTION_MAP[closest]


def tap(x, y):
    """adb点击"""
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(x), str(y)], 
                   capture_output=True, timeout=5)


def swipe(x1, y1, x2, y2, duration_ms=1000):
    """adb滑动"""
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', 
                    str(x1), str(y1), str(x2), str(y2), str(duration_ms)],
                   capture_output=True, timeout=5)


def check_dead(img):
    """检查是否死亡"""
    results_reader = None  # lazy import
    return False


def navigate_to_evac(max_steps=100):
    """
    主导航循环：检测撤离方向→朝方向走→检测是否到达
    """
    print("=== 撤离导航启动 ===")
    
    for step in range(max_steps):
        img = screenshot()
        if img is None:
            print("截图失败")
            break
        
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = g.mean()
        
        # 死亡检测
        bot = img[int(0.88 * img.shape[0]):, :]
        bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(bot_hsv, (0, 50, 50), (10, 255, 255)) | cv2.inRange(bot_hsv, (160, 50, 50), (180, 255, 255))
        hp = cv2.countNonZero(red)
        
        # 找小地图
        mm_cx, mm_cy, mm_r = find_minimap(img)
        
        # 找撤离方向
        angle, dist_pct = find_evac_markers(img, mm_cx, mm_cy, mm_r)
        
        if angle is not None:
            dirs = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
            idx = int((angle + 22.5) / 45) % 8
            dir_text = dirs[idx]
            
            # 走向撤离点
            sx, sy = angle_to_swipe(angle)
            print(f"步{step}: 撤离点在{dir_text}({angle:.0f}°) 距离{100-dist_pct:.0f}% 血量{hp}")
            
            # 朝撤离方向走1.5秒
            swipe(JOYSTICK_CENTER[0], JOYSTICK_CENTER[1], sx, sy, 1500)
            time.sleep(1.8)
            
            # 随机轻微转头看路（模拟人类观察环境）
            if step % 3 == 0:
                swipe(1400, 500, 1700, 500, 200)
                time.sleep(0.3)
        else:
            # 没检测到撤离标记，说明不在小地图范围内
            print(f"步{step}: 未检测到撤离标记 血量{hp}")
            
            # 尝试换方向找：朝当前方向继续走
            swipe(JOYSTICK_CENTER[0], JOYSTICK_CENTER[1], 265, 400, 1500)
            time.sleep(1.8)
            
            # 转头看看四周
            if step % 2 == 0:
                swipe(1400, 500, 2000, 500, 400)
                time.sleep(0.5)
        
        # 血量低时治疗
        if hp < 100:
            tap(1800, 600)
            time.sleep(0.5)
            tap(1800, 600)
            time.sleep(1)
        
        # 每5步截图保存
        if step > 0 and step % 5 == 0:
            cv2.imwrite(f'C:\\temp\\delta_nav_step{step}.png', img)
            
    print("=== 导航结束 ===")


if __name__ == "__main__":
    navigate_to_evac()
