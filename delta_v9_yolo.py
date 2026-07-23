"""
Delta Force v9 - YOLO自瞄脚本
特性: 页面识别 + YOLO检测敌人 + 自动开枪 + 自动打药
"""

import cv2, numpy as np, os, sys, time, subprocess, json, warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# ===== 配置 =====
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')
ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
YOLO_MODEL = r'C:\u-claw\portable\data\.openclaw\workspace\yolov8n.pt'

# 屏幕坐标（2340x1080）
START_BTN = (1700, 960)     # "开始行动" 右下角（黑色字体）
BACK_BTN  = (200, 100)      # 返回按钮 左上角
HEAL_BTN  = (1800, 600)     # 治疗背包打开位置

MATCH_TIMEOUT = 300         # 匹配等待最久5分钟

# ===== YOLO初始化 =====
def init_yolo():
    from ultralytics import YOLO
    model = YOLO(YOLO_MODEL)
    return model

# ===== ADB工具 =====
def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(x), str(y)], capture_output=True)

def swipe(x1, y1, x2, y2, dur=200):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2), str(dur)], capture_output=True)

# ===== 页面识别 =====
def detect_page(img):
    """
    识别当前在哪个页面: lobby/match/ingame/result/unknown
    基于画面特征判断
    """
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = gray.mean()
    
    # 检测小地图：左上角 200x200 找圆形
    minimap_roi = gray[20:220, 20:220]
    has_minimap = False
    if minimap_roi.size > 0:
        blurred = cv2.medianBlur(minimap_roi, 5)
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 100,
                                   param1=80, param2=30, minRadius=60, maxRadius=110)
        has_minimap = circles is not None
    
    # 检测右下角是否有按钮（大厅或结算的特征）
    btn_roi = gray[h-150:h-30, w-400:w-50]
    btn_std = btn_roi.std() if btn_roi.size > 0 else 0
    
    # 检测底部中央是否有文字/UI（模式选择栏）
    mid_bottom = gray[h-120:h-20, w//3:2*w//3]
    mid_bottom_std = mid_bottom.std() if mid_bottom.size > 0 else 0
    
    # 检测画面右上角是否有"返回"/"X"按钮（结算或匹配中可能有）
    top_right = gray[30:130, w-200:w-30]
    tr_std = top_right.std() if top_right.size > 0 else 0
    
    if has_minimap:
        # 有小地图 → 游戏中（包括跳伞/飞机/落地）
        return 'ingame'
    
    # 结算页面：画面亮(>120)，中间有数据面板，无小地图
    if mean_val > 100:
        mid_roi = gray[h//2-100:h//2+100, w//4:3*w//4]
        mid_mean = mid_roi.mean() if mid_roi.size > 0 else 0
        if mid_mean > 80:
            return 'result'
        return 'lobby'
    
    # 暗画面：区分 大厅 vs 匹配
    # 大厅：底部有UI元素(模式选择栏)，标准差大
    # 匹配：几乎全黑，UI元素很少
    if btn_std > 25 or mid_bottom_std > 20:
        # 底部有按钮/UI → 大厅
        return 'lobby'
    
    if tr_std > 20:
        # 右上角有按钮 → 可能结算中
        return 'result'
    
    # 画面很暗且无UI元素 → 匹配中或加载中
    return 'match'

def wait_for_enter(timeout=MATCH_TIMEOUT):
    """等待进入游戏（检测到小地图）"""
    start = time.time()
    while time.time() - start < timeout:
        img = screenshot()
        if img is None:
            time.sleep(2)
            continue
        
        page = detect_page(img)
        elapsed = int(time.time() - start)
        print(f"  {elapsed}s page={page} mean={img.mean():.1f}")
        
        if page == 'ingame':
            print("[进场成功!] 检测到小地图，进入游戏")
            return True
        if page == 'match':
            # 还在匹配
            pass
        elif page == 'result':
            print("[结算] 还没进就结算了？")
            return False
        elif page == 'lobby':
            print("[回到大厅] 匹配取消了？")
            return False
        
        time.sleep(1)
    
    print(f"[超时] 匹配等待{timeout}秒未进入")
    return False

def wait_for_game_end(timeout=900):
    """游戏中循环，直到结算"""
    start = time.time()
    no_progress = 0
    
    while time.time() - start < timeout:
        img = screenshot()
        if img is None:
            time.sleep(1)
            continue
        
        page = detect_page(img)
        mean_val = img.mean()
        
        if page == 'result':
            print("[结算] 本局结束")
            return True
        if page == 'match' or page == 'lobby':
            print("[异常] 被踢回大厅")
            return False
        
        # 游戏中 → YOLO检测敌人
        if page == 'ingame':
            try:
                # 检查血量
                hp_color = check_hp(img)
                if hp_color == 'low':
                    heal()
                
                # YOLO检测
                enemies = detect_enemies(img)
                if enemies:
                    for e in enemies:
                        # 准星瞄准+开枪
                        aim_shoot(e, img.shape[:2])
                        time.sleep(0.1)
                
                time.sleep(1)
            except Exception as ex:
                print(f"[YOLO错误] {ex}")
                time.sleep(2)
        else:
            time.sleep(2)
    
    print("[超时] 游戏中超时")
    return False

# ===== 检查血量 =====
def check_hp(img):
    """
    检查血量状态
    血条通常在屏幕底部中央偏左，绿色/红色
    """
    h, w = img.shape[:2]
    # 底部中央血条区域
    hp_roi = img[h-80:h-30, w//2-100:w//2+100]
    if hp_roi.size == 0:
        return 'ok'
    
    hsv = cv2.cvtColor(hp_roi, cv2.COLOR_BGR2HSV)
    
    # 红色范围（低血量）
    red_mask = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255)) | \
               cv2.inRange(hsv, (160, 50, 50), (180, 255, 255))
    red_ratio = cv2.countNonZero(red_mask) / hp_roi.size
    
    if red_ratio > 0.3:
        return 'low'
    return 'ok'

def heal():
    """打药"""
    tap(HEAL_BTN[0], HEAL_BTN[1])
    time.sleep(1.5)

# ===== YOLO检测 =====
def detect_enemies(img):
    """YOLOv8检测敌人"""
    model = yolo_model
    results = model(img, conf=0.3, iou=0.4, verbose=False)
    
    detections = []
    for r in results:
        boxes = r.boxes
        if boxes is None:
            continue
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())
            detections.append({
                'box': [int(x1), int(y1), int(x2-x1), int(y2-y1)],
                'confidence': conf,
                'class_id': cls
            })
    return detections

def aim_shoot(enemy, img_shape):
    """瞄准敌人并开枪"""
    x, y, bw, bh = enemy['box']
    center_x = x + bw//2
    center_y = y + bh//2
    
    # 多点连射
    for _ in range(5):
        tap(center_x, center_y)
        time.sleep(0.15)

# ===== 主循环 =====
def main_loop():
    global yolo_model
    yolo_model = init_yolo()
    print(f"YOLO加载完成. 使用ADB: {ADB}")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*40}")
        print(f"Delta Force v9 - YOLO自瞄 - 第{cycle}局")
        print('='*40)
        
        # 阶段1: 识别当前页面
        img = screenshot()
        if img is None:
            print("[错误] 截图失败，重试")
            time.sleep(2)
            continue
        
        page = detect_page(img)
        print(f"[当前页面] {page} mean={img.mean():.1f}")
        
        # 阶段2: 如果在匹配中 → 等进场
        if page == 'match':
            print("[匹配中] 等待进入游戏...")
            if not wait_for_enter():
                # 等不到，回大厅重来
                print("[无法进场] 返回重试")
                time.sleep(3)
                continue
        
        # 阶段3: 如果在游戏中 → 打一局
        if page == 'ingame':
            print("[游戏中] 开始战斗循环")
            wait_for_game_end()
            continue
        
        # 阶段4: 结算页面 → 点返回
        if page == 'result':
            print("[结算] 等待返回大厅...")
            time.sleep(3)
            tap(BACK_BTN[0], BACK_BTN[1])
            time.sleep(2)
            tap(BACK_BTN[0], BACK_BTN[1])
            time.sleep(3)
            continue
        
        # 阶段5: 大厅 → 点开始行动
        if page == 'lobby':
            print("[大厅] 点击开始行动...")
            tap(START_BTN[0], START_BTN[1])
            time.sleep(1)
            tap(START_BTN[0], START_BTN[1])  # 双击保险
            time.sleep(2)
            continue
        
        # 未知页面 → 尝试返回
        print("[未知页面] 尝试返回...")
        tap(200, 100)
        time.sleep(3)

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n[停止] 用户中断")
    except Exception as e:
        print(f"[崩溃] {e}")
        import traceback
        traceback.print_exc()
