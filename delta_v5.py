# -*- coding: utf-8 -*-
"""
Delta Force v5
- 页面切换时用OCR识别（慢但准）
- 游戏中只用快速特征检测（快）
- 所有按钮由OCR定位再点击
"""
import cv2, numpy as np, os, time, subprocess, warnings
warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')
MATCH_TIMEOUT = 300

# ---------- ADB ----------
def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True)

# ---------- OCR ----------
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

def ocr_page(items):
    """OCR文字判断页面"""
    all_text = ' '.join([t for t, _, _ in items])
    
    # 游戏中特有文字
    if '距离' in all_text or '烟幕' in all_text or '弹药' in all_text or '治疗' in all_text:
        return 'ingame'
    if '点击地图' in all_text:
        return 'ingame'
    if '自我治疗' in all_text or '医疗箱' in all_text or '急救' in all_text:
        return 'ingame'
    
    # 结算
    if any(kw in all_text for kw in ['大吉大利', '胜利', '失败', '本局', '排名', '撤离', '战绩']):
        return 'result'
    
    # 匹配
    if '搜索中' in all_text or '等待' in all_text:
        return 'match'
    
    # 大厅
    if '开始行动' in all_text or '全面战场' in all_text:
        return 'lobby'
    
    # 模式选择
    if any(m in all_text for m in ['攻守', '占领', '闪击']):
        return 'lobby'
    
    return None  # 不确定

def ocr_find(items, keywords):
    """找含关键词的按钮位置"""
    for kw in keywords:
        for text, conf, pos in items:
            if kw in text:
                return pos
    return None

# ---------- 快速特征检测 ----------
def fast_is_ingame(gray, h, w, color_img):
    """快速判断是否还在游戏中（不用OCR）"""
    # 方法1: 小地图
    mm = gray[20:220, 20:220]
    if mm.mean() > 30:
        blurred = cv2.medianBlur(mm, 5)
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 100,
                                       param1=80, param2=30, minRadius=60, maxRadius=110)
        if circles is not None:
            return True
    
    # 方法2: 底部颜色特征（血条红+护甲蓝）
    if color_img is not None:
        hsv = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
        bottom = hsv[h-100:h, :]
        red = cv2.inRange(bottom, (0,50,50), (10,255,255)) | cv2.inRange(bottom, (160,50,50), (180,255,255))
        blue = cv2.inRange(bottom, (80,50,50), (130,255,255))
        if cv2.countNonZero(blue) > 200 and cv2.countNonZero(red) > 100:
            return True
    
    return False

# ---------- 各页面处理 ----------
def handle_lobby(img):
    """大厅→OCR找开始行动→点击"""
    print("  [大厅]")
    items = ocr(img)
    page = ocr_page(items)
    print(f"  OCR判断: {page}")
    
    pos = ocr_find(items, ['开始行动', '开始战'])
    if pos:
        print(f"  点击开始行动 {pos}")
        tap(pos[0], pos[1])
        time.sleep(2)
        return True
    
    # 找不到, 尝试其他关键词
    pos = ocr_find(items, ['行动'])
    if pos:
        print(f"  点击行动 {pos}")
        tap(pos[0], pos[1])
        time.sleep(2)
        return True
    
    print("  找不到按钮, 等3s")
    time.sleep(3)
    return False

def handle_match(img):
    """匹配→等进场 (快速检测)"""
    print("  [匹配]")
    start = time.time()
    while time.time() - start < MATCH_TIMEOUT:
        time.sleep(2)
        img = screenshot()
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if fast_is_ingame(gray, h, w, img):
            elapsed = int(time.time() - start)
            print(f"  [{elapsed}s] 进场!")
            return True
        # 回到大厅
        if gray.mean() > 60:
            items = ocr(img)
            if ocr_page(items) == 'lobby':
                print(f"  [{int(time.time()-start)}s] 回大厅")
                return False
        if int(time.time()-start) % 15 == 0:
            print(f"  [{int(time.time()-start)}s] ...")
    print("  超时")
    return False

def handle_ingame(img):
    """游戏中→YOLO循环"""
    try:
        from ultralytics import YOLO
        model = YOLO(r'C:\u-claw\portable\data\.openclaw\workspace\yolov8n.pt')
    except:
        model = None
    
    print("  [游戏中]")
    start = time.time()
    dark_frames = 0
    while time.time() - start < 900:
        img = screenshot()
        if img is None:
            time.sleep(1)
            continue
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        mean_val = gray.mean()
        
        # 持续黑暗 -> 退出
        if mean_val < 50:
            dark_frames += 1
        else:
            dark_frames = 0
        
        if dark_frames > 10:
            print(f"  画面持续黑暗, 退出游戏循环")
            return
        
        # 快速检测是否游戏中
        if not fast_is_ingame(gray, h, w, img):
            # OCR确认
            items = ocr(img)
            p = ocr_page(items)
            if p != 'ingame' and p is not None:
                print(f"  页面变化: {p}")
                return
        
        if model and mean_val > 50:
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
                            for _ in range(3):
                                tap(cx, cy)
                                time.sleep(0.1)
            except:
                pass
        
        time.sleep(2)

def handle_result(img):
    """结算→OCR找返回→点击"""
    print("  [结算]")
    items = ocr(img)
    pos = ocr_find(items, ['返回', '继续', '下一步', '确认', '回大厅'])
    if pos:
        print(f"  点击返回 {pos}")
        tap(pos[0], pos[1])
    else:
        print("  未找到返回按钮, 点左下角")
        tap(200, 100)
    time.sleep(5)

# ---------- 主循环 ----------
def main():
    print("=== Delta Force v5 ===")
    print("加载OCR...")
    dummy = ocr(screenshot())
    print("就绪!")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- 第{cycle}局 ---")
        img = screenshot()
        if img is None:
            continue
        
        # OCR判断当前页面
        items = ocr(img)
        page = ocr_page(items)
        gray_mean = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()
        print(f"OCR: {page}, mean={gray_mean:.0f}")
        
        if page == 'lobby':
            handle_lobby(img)
        elif page == 'match':
            handle_match(img)
        elif page == 'ingame':
            handle_ingame(img)
        elif page == 'result':
            handle_result(img)
        else:
            # OCR不确定, 用特征判断
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            if fast_is_ingame(gray, h, w, img):
                print("  特征检测=ingame")
                handle_ingame(img)
            elif gray.mean() > 100:
                print("  特征检测=result")
                handle_result(img)
            else:
                print("  不确定, 等3s")
                time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
