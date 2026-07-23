# -*- coding: utf-8 -*-
"""
三角洲行动 - 战斗模块 v12
简化版：就在游戏里走，被打就转向，没弹药换武器/刀，半血自我治疗
"""
import subprocess, time, cv2, numpy as np, os

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# ===== 按键 =====
KEY_M = 50     # 地图
KEY_ESC = 111
KEY_BACK = 4
KEY_RELOAD = 23  # R 换弹
KEY_1 = 8      # 武器1
KEY_2 = 9      # 武器2
KEY_3 = 10     # 刀/近战

def tap(x, y): subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=3)
def swipe(x1,y1,x2,y2,ms): subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(int(ms))], capture_output=True, timeout=10)
def keyevent(k): subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'keyevent', str(k)], capture_output=True, timeout=3)

# ===== 截图 =====
def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]: img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

# ===== 血量检测 =====
def check_health(img):
    """返回(血量百分比, 护甲百分比, 是否受击)"""
    h,w = img.shape[:2]
    # 底部12%找红蓝条
    bot = img[int(0.88*h):h, :]
    hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0,50,50), (10,255,255)) | cv2.inRange(hsv, (160,50,50), (180,255,255))
    blue = cv2.inRange(hsv, (80,50,50), (130,255,255))
    
    r_cnt = cv2.countNonZero(red)
    b_cnt = cv2.countNonZero(blue)
    
    # 估算血量：对比之前满血时的红像素数（大约8000+）
    health_pct = min(r_cnt / 100, 1.0)
    armor_pct = min(b_cnt / 100, 1.0)
    
    return health_pct, armor_pct

# ===== 受击检测 =====
def check_hit(img):
    """
    检测是否受到攻击。
    中弹时屏幕边缘会出现红色指示器，左上右上左下右下。
    返回(被打, 方向) 方向: 'left','right','front','back'或None
    """
    h,w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 红色掩码（低饱和也可能有半透明红）
    red = cv2.inRange(hsv, (0,30,50), (10,255,255)) | cv2.inRange(hsv, (160,30,50), (180,255,255))
    
    # 屏幕分成4个边缘区域
    margin = 80
    # 左边缘区域
    left_edge = red[margin:h-margin, 0:margin]
    right_edge = red[margin:h-margin, w-margin:w]
    top_edge = red[0:margin, margin:w-margin]
    bottom_edge = red[h-margin:h, margin:w-margin]
    
    left_hit = cv2.countNonZero(left_edge)
    right_hit = cv2.countNonZero(right_edge)
    top_hit = cv2.countNonZero(top_edge)
    bottom_hit = cv2.countNonZero(bottom_edge)
    
    # 判断是否受击（边缘红色突然增多）
    threshold = 500
    if left_hit > threshold:
        return True, 'left', left_hit
    if right_hit > threshold:
        return True, 'right', right_hit
    if bottom_hit > threshold:
        return True, 'back', bottom_hit
    if top_hit > threshold:
        return True, 'front', top_hit
    
    return False, None, 0

# ===== 弹药检测 =====
def check_ammo(img):
    """
    检测弹药量。底部中间偏右一般有弹药显示。
    简单检测：底部白色文字区域，找数字/斜线
    """
    # 先用OCR快速判断有没有"3/3"这些
    pass

# ===== 自动治疗 =====
def auto_heal(img):
    """血量低时点自我治疗"""
    h,w = img.shape[:2]
    bot = img[int(0.88*h):h, :]
    hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0,50,50), (10,255,255)) | cv2.inRange(hsv, (160,50,50), (180,255,255))
    r_cnt = cv2.countNonZero(red)
    
    # 血量低（红像素少于2000）
    if r_cnt < 2000:
        print(f"  血量低! (红={r_cnt}) 尝试治疗")
        # 治疗按钮一般在右下角，射击按钮附近
        # 常见位置: x=1800-2000, y=600-800
        tap(1900, 700)
        time.sleep(0.3)
        # 如果有"自我治疗"，一般在治疗菜单里
        # 或者直接双击治疗区域
        tap(1900, 700)
        time.sleep(0.3)
        return True
    return False

# ===== 换武器 =====
def switch_weapon():
    """切到近战刀"""
    keyevent(KEY_3)  # 3键通常=近战
    time.sleep(0.2)

def main_weapon():
    """切回主武器"""
    keyevent(KEY_1)
    time.sleep(0.2)

# ===== 倒地检测 =====
def check_down(img):
    """检测是否倒地。倒地时画面变灰+有求救按钮"""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h,w = g.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 倒地特征：画面整体饱和度极低（灰化），底部或有红色边框
    sat = hsv[:,:,1]
    avg_sat = sat.mean()
    g_mean = g.mean()
    
    # 中间区域找"求救"、"呼叫"等文字更快，但这里先用特征
    # 饱和度很低 + 画面不黑 = 可能倒地
    if avg_sat < 30 and 40 < g_mean < 120:
        # 底部检查是否有红色低频闪烁或呼救UI
        bot = img[int(0.85*h):h, :]
        bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
        r_cnt = cv2.countNonZero(red)
        if r_cnt > 500:
            print(f"  倒地! (sat={avg_sat:.0f} m={g_mean:.0f} 红={r_cnt})")
            return True
    return False

def call_for_help():
    """倒地呼救"""
    print("  === 呼救! ===")
    # 呼救按钮一般在右下角或屏幕中间
    # 尝试几个常见位置
    tap(1500, 600)  # 屏幕中央区域
    time.sleep(0.3)
    tap(2000, 900)  # 右下角
    time.sleep(0.3)
    tap(1170, 540)  # 屏幕正中央
    time.sleep(0.3)
    # 有些游戏呼喊是长按/双击
    tap(1500, 600)
    time.sleep(0.5)

# ===== 被攻击紧急反应 =====
def react_to_hit(direction, hit_strength):
    """被打后的反应：转方向、找掩体"""
    if direction == 'left':
        # 子弹从左边来 → 右转
        print(f"  ← 左侧受击! 右转")
        swipe(1200, 500, 2000, 500, 200)
        time.sleep(0.1)
    elif direction == 'right':
        # 右边来 → 左转
        print(f"  → 右侧受击! 左转")
        swipe(1200, 500, 500, 500, 200)
        time.sleep(0.1)
    elif direction == 'front':
        # 前面来 → 左右闪
        print(f"  ↑ 前方受击! 闪避")
        swipe(200, 750, 500, 750, 100)
        time.sleep(0.2)
    elif direction == 'back':
        # 后面来 → 回头
        print(f"  ↓ 后方受击! 回头")
        swipe(500, 500, 2000, 500, 400)
        time.sleep(0.2)

# ===== 移动 =====
def walk_forward(ms=1500):
    """摇杆向前推"""
    swipe(200, 800, 200, 400, ms)

def turn_left():
    swipe(1200, 500, 600, 500, 200)

def turn_right():
    swipe(1200, 500, 2000, 500, 200)

def turn_back():
    swipe(600, 500, 2000, 500, 300)

# ===== 测试 =====
if __name__ == '__main__':
    print("测试: 截图分析")
    img = screenshot()
    if img is None:
        print("截图失败")
        exit()
    h,w = img.shape[:2]
    print(f"画面: {w}x{h}")
    health, armor = check_health(img)
    hit, direction, strength = check_hit(img)
    print(f"血量≈{health:.0%} 护甲≈{armor:.0%}")
    print(f"受击: {hit} 方向:{direction} 强度:{strength}")
