# -*- coding: utf-8 -*-
"""
Delta Force 智能助手 v4
页面识别: 图像特征(快) + OCR文字(只在需要时)
按钮定位: OCR找文字 -> 点击
敌人检测: YOLOv8(后续训练)
"""
import cv2, numpy as np, os, time, subprocess, warnings
warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# -------- ADB --------
def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True)

# -------- OCR (延迟加载) --------
reader = None
def ocr(img):
    global reader
    if reader is None:
        import easyocr
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    results = reader.readtext(img, paragraph=False)
    items = []
    for bbox, text, conf in results:
        if conf < 0.3:
            continue
        tl, tr, br, bl = bbox
        cx, cy = int((tl[0]+br[0])/2), int((tl[1]+br[1])/2)
        items.append((text.strip(), conf, (cx, cy)))
    return items

# -------- 快速页面识别 (图像特征) --------
def detect_page_fast(gray, h, w, color_img=None):
    """不用OCR，纯图像特征判断页面
    多维度: 小地图 + UI元素(红色血条/蓝色护甲/白色UI) + 亮度
    """
    mean_val = gray.mean()
    
    # ---------- ingame检测 ----------
    # 方法1: 小地图圆形
    minimap_roi = gray[20:220, 20:220]
    has_minimap = False
    if minimap_roi.size > 0 and mean_val > 40:
        blurred = cv2.medianBlur(minimap_roi, 5)
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 100,
                                   param1=80, param2=30, minRadius=60, maxRadius=110)
        has_minimap = circles is not None
    
    if has_minimap:
        return 'ingame'
    
    # 方法2: 游戏UI特征 (血条红 + 护甲蓝 + 底部武器栏)
    if color_img is not None and mean_val > 50:
        hsv = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
        # 底部100像素的红色(血条)和蓝色(护甲条)
        bottom_hsv = hsv[h-100:h, :]
        red_bottom = cv2.inRange(bottom_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bottom_hsv, (160,50,50), (180,255,255))
        blue_bottom = cv2.inRange(bottom_hsv, (80,50,50), (130,255,255))
        r_count = cv2.countNonZero(red_bottom)
        b_count = cv2.countNonZero(blue_bottom)
        
        # 游戏中: 底部有红+蓝色块 (血条+护甲)
        if b_count > 100 and r_count > 50:
            return 'ingame'
        
        # 底部左侧(武器栏)有亮色UI
        bottom_left = gray[h-150:h-20, w//4:w//2]
        if bottom_left.std() > 35 and bottom_left.mean() > 55:
            return 'ingame'
    
    # ---------- 结算 ----------
    if mean_val > 100:
        mid = gray[h//2-200:h//2+200, w//4:3*w//4]
        if mid.mean() > 80:
            return 'result'
        return 'result'
    
    # ---------- 暗画面: 大厅 vs 匹配 ----------
    if mean_val < 75:
        bottom_roi = gray[h-150:h-20, w//4:3*w//4]
        bottom_std = bottom_roi.std()
        if bottom_std > 18:
            return 'lobby'
        # 再检测右下角找按钮
        right_btn = gray[h-150:h-30, w-400:w-50]
        if right_btn.std() > 25:
            return 'lobby'
        return 'match'
    
    return 'unknown'

# -------- 找按钮文字 --------
def find_keyword(items, keywords):
    """找第一个匹配关键词的按钮坐标"""
    for kw in keywords:
        for text, conf, pos in items:
            if kw in text:
                return pos
    return None

# -------- 各页面处理 --------
def handle_lobby(img):
    """大厅: OCR找'开始行动' 或 点底部大按钮"""
    print("  [大厅] 找开始行动...")
    items = ocr(img)
    pos = find_keyword(items, ['开始行动', '开始战', '行动'])
    if pos:
        print(f"  点击 '{pos}'")
        tap(pos[0], pos[1])
        time.sleep(2)
        return
    
    # OCR没找到 -> 点底部偏右
    h, w = img.shape[:2]
    tap(int(w*0.78), int(h*0.88))
    time.sleep(2)
    print("  点击右下角")

def handle_match(img):
    """匹配等待: 等进场"""
    print("  [匹配中] ...")
    start = time.time()
    while time.time() - start < 300:
        time.sleep(2)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        page = detect_page_fast(gray, *img.shape[:2], img)
        if page == 'ingame':
            print(f"  [{int(time.time()-start)}s] 进场!")
            return True
        if page == 'lobby':
            print(f"  [{int(time.time()-start)}s] 回大厅")
            return False
        img = screenshot()
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        page = detect_page_fast(gray, *img.shape[:2], img)
        if int(time.time()-start) % 15 == 0:
            print(f"  [{int(time.time()-start)}s] ...")
    print("  超时")
    return False

def handle_ingame(img):
    """游戏中: YOLO检测+开枪"""
    try:
        from ultralytics import YOLO
        model = YOLO(r'C:\u-claw\portable\data\.openclaw\workspace\yolov8n.pt')
    except:
        model = None
        print("  YOLO未加载")
    
    start = time.time()
    while time.time() - start < 900:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        page = detect_page_fast(gray, *img.shape[:2], img)
        
        if page == 'result':
            print("  结算")
            return
        if page != 'ingame':
            print(f"  页面变化: {page}")
            return
        
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
                        if conf > 0.4:
                            print(f"  射击 ({cx},{cy})")
                            for _ in range(3):
                                tap(cx, cy)
                                time.sleep(0.1)
            except:
                pass
        
        time.sleep(1)
        img = screenshot()
        if img is None:
            time.sleep(1)
            continue

def handle_result(img):
    """结算: 找'返回' 或 点中间"""
    print("  [结算] 返回...")
    items = ocr(img)
    pos = find_keyword(items, ['返回', '继续', '下一步', '确认'])
    if pos:
        tap(pos[0], pos[1])
    else:
        tap(1170, 500)  # 中间偏上
    time.sleep(3)

def handle_unknown(img):
    """未知页面: 等或返回"""
    print("  [未知] 等待...")
    time.sleep(3)

# -------- 主循环 --------
def main():
    print("=== Delta Force v4 ===")
    print("初始化OCR...")
    dummy = ocr(screenshot())
    print("就绪!")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- 第{cycle}局 ---")
        
        img = screenshot()
        if img is None:
            time.sleep(2)
            continue
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = img.shape[:2]
        page = detect_page_fast(gray, h, w, img)
        print(f"页面: {page} mean={gray.mean():.1f}")
        
        handlers = {
            'lobby': handle_lobby,
            'match': handle_match,
            'ingame': handle_ingame,
            'result': handle_result,
        }
        handler = handlers.get(page, handle_unknown)
        handler(img)
        
        if page == 'match':
            # match返回False表示回大厅了，继续下一轮
            continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
