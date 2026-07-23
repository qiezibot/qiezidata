# -*- coding: utf-8 -*-
"""
Delta Force v11 - 最简单的战斗脚本
- 不进大厅、不选图、不碰地图
- 只在游戏内：走 → 转 → 打 → 循环
- 死了自动识别黑屏 → 再重进游戏
"""
import subprocess, time, cv2, numpy as np, os, warnings
warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# 摇杆定位（左半屏偏下）
JOY_X = 250
JOY_Y = 750

# 转头（右半屏划动）
LOOK_CENTER = 1200
LOOK_Y = 500

# 开火（右下角）
FIRE_X = 2100
FIRE_Y = 850

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=3)

def swipe(x1, y1, x2, y2, ms):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms))], capture_output=True, timeout=max(ms//1000+3, 5))

def keyevent(k):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'keyevent', str(k)], capture_output=True, timeout=3)

# ============ 截图分析（纯轻量，不用OCR） ============
def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def is_alive(img=None):
    """快速判断是否还在游戏中活着，纯特征判断，不用OCR"""
    if img is None:
        r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=10)
        img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
        if img is None: return True
        if img.shape[0] > img.shape[1]:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = g.mean()
    
    # 底部15%区域判断血条/护甲（红/蓝）
    h, w = g.shape
    bot = img[int(0.85*h):h, :]
    hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0,50,50), (10,255,255)) | cv2.inRange(hsv, (160,50,50), (180,255,255))
    blue = cv2.inRange(hsv, (80,50,50), (130,255,255))
    br = cv2.countNonZero(red)
    bb = cv2.countNonZero(blue)
    
    # 条件：有红条(血)或蓝条(护甲)且画面不黑=活着
    if m < 50 and br < 100 and bb < 100:
        return False  # 黑屏+无UI=死亡/结算
    if br < 50 and bb < 50 and m < 60:
        return False  # 也可能是结算页
    
    return True

# ============ 战斗中 ============
def in_game_loop():
    """只在游戏内的循环，不管别的"""
    start = time.time()
    step = 0
    
    while time.time() - start < 900:  # 最长一局15分钟
        step += 1
        
        # === 走路（关键：长拽，真正走路）===
        # 往前冲
        swipe(JOY_X, JOY_Y, JOY_X, JOY_Y-400, 2000)  # 按住2秒走
        time.sleep(0.1)
        
        # 边转头边开火
        for _ in range(3):
            # 右转头
            swipe(LOOK_CENTER, LOOK_Y, LOOK_CENTER+500, LOOK_Y, 150)
            time.sleep(0.05)
            tap(FIRE_X, FIRE_Y)
            time.sleep(0.05)
        
        # 再往前走
        swipe(JOY_X, JOY_Y, JOY_X, JOY_Y-400, 1500)
        
        # 左转头
        for _ in range(3):
            swipe(LOOK_CENTER, LOOK_Y, LOOK_CENTER-400, LOOK_Y, 150)
            time.sleep(0.05)
            tap(FIRE_X, FIRE_Y)
            time.sleep(0.05)
        
        # 往左平移
        swipe(JOY_X, JOY_Y, JOY_X-300, JOY_Y, 800)
        time.sleep(0.1)
        
        swipe(JOY_X, JOY_Y, JOY_X, JOY_Y-400, 1500)
        
        for _ in range(3):
            swipe(LOOK_CENTER, LOOK_Y, LOOK_CENTER+400, LOOK_Y, 150)
            time.sleep(0.05)
            tap(FIRE_X, FIRE_Y)
            time.sleep(0.05)
        
        # 每3步大转向
        if step % 3 == 0:
            # 180度转头
            swipe(LOOK_CENTER-200, LOOK_Y, LOOK_CENTER+500, LOOK_Y, 300)
            time.sleep(0.1)
            swipe(LOOK_CENTER-200, LOOK_Y, LOOK_CENTER+500, LOOK_Y, 300)
            # 往回走
            swipe(JOY_X, JOY_Y, JOY_X, JOY_Y-400, 2000)
            time.sleep(0.1)
        
        # 检查是否还活着
        if step % 3 == 0:
            if not is_alive():
                print(f"  死亡/结算 ({int(time.time()-start)}s)")
                return
            print(f"  {int(time.time()-start)}s 存活")
    
    print("  单局结束")

# ============ 等待进入游戏 ============
def wait_in_game():
    """等着进游戏"""
    print("  [等待进场]")
    start = time.time()
    while time.time() - start < 300:
        time.sleep(3)
        r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=10)
        img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
        if img is None: continue
        if img.shape[0] > img.shape[1]:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = g.mean()
        h,w = g.shape
        bot = img[int(0.85*h):h, :]
        hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(hsv, (0,50,50), (10,255,255)) | cv2.inRange(hsv, (160,50,50), (180,255,255))
        blue = cv2.inRange(hsv, (80,50,50), (130,255,255))
        br = cv2.countNonZero(red)
        bb = cv2.countNonZero(blue)
        
        # 进场判断：画面不黑+有UI
        if m > 60 and (br > 200 or bb > 200):
            print(f"  进场!")
            in_game_loop()
            return
        if m > 70:
            print(f"  等待 {int(time.time()-start)}s (m={m:.0f})")
    
    print("  超时")

# ============ 主循环 ============
def main():
    print("=== 三角洲行动 v11 ===")
    print("纯战斗模式 - 不碰地图，只走位开枪")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- 第{cycle}轮 ---")
        
        # 先关任何可能打开的地图
        keyevent(50)   # M 关地图
        time.sleep(0.1)
        keyevent(4)    # 返回
        time.sleep(1)
        
        img = screenshot()
        if img is None: continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        if is_alive(img):
            print("  已经在游戏中!")
            in_game_loop()
        else:
            print("  不在游戏中,等待进场...")
            wait_in_game()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
