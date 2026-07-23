# -*- coding: utf-8 -*-
"""
Albion Online 自动采集脚本 v1
功能：检测游戏窗口 → 找可采集资源 → 走过去采集 → 循环
原理：纯图像识别 + pyautogui模拟操作，不注入游戏
"""

import cv2
import numpy as np
import pyautogui
import time
import os
import sys
from PIL import ImageGrab

# ===== 配置 =====
GAME_WINDOW_TITLE = 'Albion Online'  # 游戏窗口标题
COLLECT_KEY = 'E'  # 采集/交互键
MOUNT_KEY = 'V'  # 上马键
INVENTORY_KEY = 'I'  # 背包键
INVENTORY_FULL_THRESHOLD = 0.7  # 背包70%满就算满了

# 资源颜色范围（HSV）
# 树木 - 绿色/棕色
TREE_COLORS = [
    ((30, 30, 30), (50, 255, 200)),   # 深绿
    ((10, 30, 30), (25, 255, 200)),   # 棕色
]
# 矿石 - 灰色/白色
ORE_COLORS = [
    ((0, 0, 50), (180, 30, 255)),     # 灰色
    ((0, 0, 150), (180, 20, 255)),    # 亮白
]
# 纤维/麻 - 浅绿/黄绿
FIBER_COLORS = [
    ((25, 30, 100), (45, 200, 255)),  # 黄绿色
]
# 皮革/动物 - 棕色/红色
HIDE_COLORS = [
    ((0, 50, 50), (10, 255, 200)),    # 红棕色
    ((10, 30, 30), (30, 200, 180)),   # 黄棕色
]

# 所有可采集资源
ALL_RESOURCE_COLORS = TREE_COLORS + ORE_COLORS + FIBER_COLORS + HIDE_COLORS

# 调试模式
DEBUG = True


def find_game_window():
    """尝试找到Albion Online游戏窗口"""
    import pygetwindow as gw
    try:
        windows = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
        if windows:
            return windows[0]
        # 模糊匹配
        all_titles = gw.getAllTitles()
        for t in all_titles:
            if 'albion' in t.lower() or '阿尔比恩' in t:
                windows = gw.getWindowsWithTitle(t)
                if windows:
                    return windows[0]
    except:
        pass
    
    # 找不到窗口就全屏检测
    print('[!] 没找到游戏窗口，将使用全屏模式')
    print('[!] 请确保游戏窗口在前台运行')
    return None


def capture_game_screen(window=None):
    """截取游戏画面"""
    if window and hasattr(window, 'left'):
        try:
            bbox = (window.left, window.top, window.left + window.width, window.top + window.height)
            screen = ImageGrab.grab(bbox=bbox)
        except:
            screen = ImageGrab.grab()
    else:
        screen = ImageGrab.grab()
    return cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)


def detect_resources(img):
    """检测画面中的可采集资源"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    
    # 资源点列表
    resource_points = []
    
    for color_range in ALL_RESOURCE_COLORS:
        lower, upper = color_range
        mask = cv2.inRange(hsv, lower, upper)
        
        # 降噪
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < 5000:  # 过滤掉太小或太大的
                x, y, cw, ch = cv2.boundingRect(cnt)
                cx, cy = x + cw // 2, y + ch // 2
                
                # 忽略屏幕边缘区域
                if cx < 20 or cx > w - 20 or cy < 20 or cy > h - 20:
                    continue
                    
                resource_points.append((cx, cy, area))
    
    # 按距离屏幕中心排序（最近的最优先）
    center_x, center_y = w // 2, h // 2
    resource_points.sort(key=lambda p: (p[0] - center_x) ** 2 + (p[1] - center_y) ** 2)
    
    return resource_points


def move_to_target(x, y, screen_w, screen_h):
    """移动鼠标到目标位置并交互"""
    # 计算相对屏幕的位置
    screen_x = x
    screen_y = y
    
    # 移动到目标
    pyautogui.moveTo(screen_x, screen_y, duration=0.3)
    
    # 右键点击移动过去
    pyautogui.click(button='right')
    time.sleep(1.5)  # 等待走到
    
    # 按E键采集
    pyautogui.press('e')
    time.sleep(0.5)
    
    # 等待采集动画（持续按E）
    for _ in range(5):
        time.sleep(0.8)
        pyautogui.press('e')


def check_proximity(img, window):
    """简单检测是否在资源旁边（画面中心附近有资源色块）"""
    h, w = img.shape[:2]
    center_region = img[h//3:2*h//3, w//3:2*w//3]
    hsv = cv2.cvtColor(center_region, cv2.COLOR_BGR2HSV)
    
    # 检查中心区域是否有资源颜色
    for color_range in ALL_RESOURCE_COLORS:
        lower, upper = color_range
        mask = cv2.inRange(hsv, lower, upper)
        if cv2.countNonZero(mask) > 200:  # 有足够像素
            return True
    return False


def main():
    print('=' * 50)
    print('  Albion Online 自动采集脚本 v1')
    print('  按 Ctrl+C 停止')
    print('=' * 50)
    print()
    print('[+] 正在查找游戏窗口...')
    
    # 找窗口
    win = find_game_window()
    if win:
        print(f'[+] 找到窗口: {win.title}')
        try:
            win.activate()
        except:
            pass
    else:
        print('[!] 未找到窗口，将使用全屏截图')
    
    time.sleep(2)
    
    cycle_count = 0
    last_move_time = time.time()
    
    try:
        while True:
            cycle_count += 1
            print(f'\n--- 循环 #{cycle_count} ---')
            
            # 截图
            img = capture_game_screen(win)
            h, w = img.shape[:2]
            
            if DEBUG:
                debug_img = img.copy()
            
            # 检测资源
            resources = detect_resources(img)
            
            if resources:
                print(f'[+] 发现 {len(resources)} 个资源点')
                
                # 走到最近的资源
                target = resources[0]
                tx, ty, ta = target
                print(f'  -> 前往资源 ({tx}, {ty}), 大小: {ta}')
                
                # 移动并采集
                move_to_target(tx, ty, w, h)
                
                if DEBUG:
                    cv2.circle(debug_img, (tx, ty), 10, (0, 255, 0), 2)
                
            else:
                print('[-] 未发现资源，朝随机方向移动...')
                # 随机方向走几步
                directions = [(0.3, 0.5), (0.7, 0.5), (0.5, 0.3), (0.5, 0.7)]
                dir_idx = cycle_count % len(directions)
                dx, dy = directions[dir_idx]
                target_x = int(w * dx)
                target_y = int(h * dy)
                pyautogui.moveTo(target_x, target_y, duration=0.3)
                pyautogui.click(button='right')
                time.sleep(2)
            
            if DEBUG:
                # 显示调试画面（缩放）
                scale = min(800 / w, 600 / h, 1.0)
                disp = cv2.resize(debug_img, (int(w * scale), int(h * scale)))
                cv2.imshow('Albion Bot Debug', disp)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
            
            # 随机等待，看起来像真人
            time.sleep(1 + np.random.random() * 2)
            
    except KeyboardInterrupt:
        print('\n[!] 用户停止')
    finally:
        cv2.destroyAllWindows()
        print('[+] 脚本已停止')


if __name__ == '__main__':
    main()
