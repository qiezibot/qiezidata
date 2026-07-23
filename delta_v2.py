# -*- coding: utf-8 -*-
"""
Delta Force 智能界面识别 + 自动化脚本 v2
逻辑: 截图 -> 识别界面 -> 找按钮 -> 点击
不硬编码坐标, 用画面特征动态找按钮
"""
import cv2, numpy as np, os, sys, time, subprocess, warnings
warnings.filterwarnings('ignore', category=FutureWarning)

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')
YOLO_MODEL_PATH = r'C:\u-claw\portable\data\.openclaw\workspace\yolov8n.pt'
MATCH_TIMEOUT = 300

def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True)

def find_buttons(gray):
    """找画面中的亮色按钮区域"""
    h, w = gray.shape
    _, bright = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    buttons = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 500:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        buttons.append({'x': x+bw//2, 'y': y+bh//2, 'x1': x, 'y1': y, 'w': bw, 'h': bh, 'area': area})
    buttons.sort(key=lambda b: b['area'], reverse=True)
    return buttons

def has_minimap(gray):
    """左上角检测小地图圆形"""
    roi = gray[20:220, 20:220]
    if roi.size == 0:
        return False
    blurred = cv2.medianBlur(roi, 5)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 100,
                               param1=80, param2=30, minRadius=60, maxRadius=110)
    return circles is not None

def analyze_page(img):
    """返回(page_type, buttons)"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = gray.mean()
    buttons = find_buttons(gray)
    minimap = has_minimap(gray)

    # 游戏中: 有小地图
    if minimap:
        return 'ingame', buttons

    # 结算: 很亮
    if mean_val > 110:
        return 'result', buttons

    # 大厅: 暗背景, 但右下角有大按钮
    big_btns = [b for b in buttons if b['area'] > 8000]
    if len(big_btns) > 0:
        return 'lobby', buttons

    # 匹配: 很暗, 几乎没按钮
    if mean_val < 70:
        return 'match', buttons

    # 其他
    if mean_val > 80:
        return 'result', buttons
    return 'unknown', buttons

def find_lobby_start(buttons, h, w):
    """在大厅找开始行动按钮: 右下1/4区域的最大按钮"""
    candidates = [b for b in buttons if b['x'] > w*0.55 and b['y'] > h*0.65]
    if candidates:
        return max(candidates, key=lambda b: b['area'])
    if buttons:
        return buttons[0]
    return None

def handle_lobby(img):
    """大厅: 找开始行动按钮并点击"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    buttons = find_buttons(gray)
    btn = find_lobby_start(buttons, h, w)
    if btn:
        print(f"  点击开始行动: ({btn['x']}, {btn['y']})")
        tap(btn['x'], btn['y'])
        time.sleep(1.5)
        tap(btn['x'], btn['y'])
        time.sleep(1.5)
        return True
    else:
        print("  找不到开始行动按钮!")
        return False

def handle_match():
    """等待进场: 直到检测到小地图"""
    start = time.time()
    while time.time() - start < MATCH_TIMEOUT:
        img = screenshot()
        if img is None:
            time.sleep(2)
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        g_mean = gray.mean()
        mm = has_minimap(gray)
        # 如果在游戏中
        if mm:
            print(f"  [{int(time.time()-start)}s] 进场成功!")
            return True
        # 回到大厅 = 取消匹配
        buttons = find_buttons(gray)
        big = [b for b in buttons if b['area'] > 8000]
        if len(big) > 0 and g_mean < 100:
            print(f"  [{int(time.time()-start)}s] 回到大厅")
            return False
        elapsed = int(time.time() - start)
        if elapsed % 15 == 0:
            print(f"  [{elapsed}s] 等待中...")
        time.sleep(2)
    print(f"  [{MATCH_TIMEOUT}s] 超时")
    return False

def handle_ingame():
    """游戏中: YOLO检测敌人"""
    try:
        from ultralytics import YOLO
        model = YOLO(YOLO_MODEL_PATH)
    except:
        print("  YOLO加载失败, 跳过检测")
        model = None

    start = time.time()
    while time.time() - start < 900:
        img = screenshot()
        if img is None:
            time.sleep(1)
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 检测进场/结算
        if has_minimap(gray) == False and gray.mean() > 100:
            print("  检测到结算")
            return True
        if has_minimap(gray) == False and gray.mean() < 70:
            print("  被踢回大厅")
            return False

        if model:
            try:
                results = model(img, conf=0.3, iou=0.4, verbose=False)
                for r in results:
                    if r.boxes is None:
                        continue
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                        conf = box.conf[0].item()
                        print(f"  敌人 ({cx},{cy}) conf={conf:.2f}")
                        for _ in range(5):
                            tap(cx, cy)
                            time.sleep(0.12)
            except Exception as e:
                print(f"  YOLO err: {e}")
        time.sleep(1)
    print("  ingame超时")
    return False

def handle_result():
    """结算: 点中间下方返回"""
    print("  处理结算...")
    time.sleep(5)
    tap(1170, 800)
    time.sleep(3)
    tap(1170, 800)
    time.sleep(3)

def main():
    print("Delta Force v2 - 智能界面识别")
    cycle = 0
    while True:
        cycle += 1
        print(f"\n=== 第{cycle}局 ===")
        img = screenshot()
        if img is None:
            time.sleep(2)
            continue
        page, buttons = analyze_page(img)
        print(f"页面: {page}, mean={img.mean():.1f}, 按钮数={len([b for b in buttons if b['area']>500])}")
        if page == 'lobby':
            handle_lobby(img)
        elif page == 'match':
            if not handle_match():
                continue
        elif page == 'ingame':
            handle_ingame()
        elif page == 'result':
            handle_result()
        else:
            time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
