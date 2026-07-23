# -*- coding: utf-8 -*-
"""
Delta Force 智能助手 v3
所有按钮用OCR文字识别定位 + 点击
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

# ---------- OCR引擎 ----------
reader = None
def get_reader():
    global reader
    if reader is None:
        import easyocr
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return reader

def ocr_image(img):
    """返回 [(text, conf, (cx,cy)), ...]"""
    r = get_reader()
    results = r.readtext(img, paragraph=False)
    items = []
    for (bbox, text, conf) in results:
        if conf < 0.3:
            continue
        tl, tr, br, bl = bbox
        cx, cy = int((tl[0]+br[0])/2), int((tl[1]+br[1])/2)
        items.append((text.strip(), conf, (cx, cy), bbox))
    return items

# ---------- 页面识别 ----------
def detect_page(ocr_items, gray_mean):
    """
    通过OCR文字判断页面
    关键词匹配:
      - 匹配中: 搜索中, 等待
      - 大厅: 开始行动, 全面战场, 烽火地带
      - 游戏中: 点击地图, 烟雾, 距离xx米
      - 结算: 胜利, 失败, 大吉大利, 排名
    """
    all_text = ' '.join([t for t, _, _, _ in ocr_items])
    
    # 游戏中
    if '点击地图' in all_text or '距离' in all_text:
        return 'ingame'
    
    # 结算
    if any(kw in all_text for kw in ['大吉大利', '胜利', '失败', '排名', '撤离']):
        return 'result'
    
    # 匹配等待
    if '搜索中' in all_text or '等待' in all_text:
        return 'match'
    
    # 大厅/选模式
    if '开始行动' in all_text or '全面战场' in all_text:
        return 'lobby'
    
    # 模式选择(已经选了模式但还没开始)
    if all_text in ['攻守', '占领', '闪击'] or any(m in all_text for m in ['攻守', '占领', '闪击']):
        return 'mode_select'
    
    return 'unknown'

def find_text_button(ocr_items, keyword):
    """找含有关键词的文字区域，返回中心坐标"""
    for text, conf, (cx, cy), bbox in ocr_items:
        if keyword in text:
            return (cx, cy)
    return None

def find_all_keyword(ocr_items, keyword):
    """找含有关键词的所有位置"""
    return [(cx, cy) for text, conf, (cx, cy), bbox in ocr_items if keyword in text]

# ---------- 各页面处理 ----------
def handle_lobby(ocr_items, img):
    """大厅: 找'开始行动'按钮"""
    btn = find_text_button(ocr_items, '开始行动')
    if btn:
        print(f"  找到 '开始行动' at {btn}")
        tap(btn[0], btn[1])
        time.sleep(2)
        return True
    else:
        print("  OCR没找到'开始行动'，截图分析...")
        # OCR可能漏了，直接分析底部
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        bottom = gray[h-150:h-20, w//3:2*w//3]
        # 找亮部
        _, bright = cv2.threshold(bottom, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        big = [c for c in contours if cv2.contourArea(c) > 5000]
        if big:
            c = max(big, key=cv2.contourArea)
            x, y, bw, bh = cv2.boundingRect(c)
            cx, cy = w//3 + x + bw//2, h-150 + y + bh//2
            print(f"  底部最大亮区域 at ({cx},{cy})")
            tap(cx, cy)
            time.sleep(2)
            return True
        return False

def handle_match(ocr_items):
    """匹配等待中"""
    print("  匹配等待中...")
    start = time.time()
    while time.time() - start < MATCH_TIMEOUT:
        img = screenshot()
        if img is None:
            time.sleep(2)
            continue
        items = ocr_image(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        page = detect_page(items, gray.mean())
        
        if page == 'ingame':
            print(f"  [{int(time.time()-start)}s] 进场！")
            return True
        if page == 'lobby':
            print(f"  [{int(time.time()-start)}s] 回到大厅")
            return False
        
        elapsed = int(time.time() - start)
        if elapsed % 10 == 0:
            print(f"  [{elapsed}s] 等待中...")
        time.sleep(2)
    print(f"  超时")
    return False

def handle_ingame(img):
    """游戏中: YOLO检测"""
    try:
        from ultralytics import YOLO
        model = YOLO(r'C:\u-claw\portable\data\.openclaw\workspace\yolov8n.pt')
    except:
        model = None
    
    start = time.time()
    while time.time() - start < 900:
        img = screenshot()
        if img is None:
            time.sleep(1)
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        items = ocr_image(img)
        page = detect_page(items, gray.mean())
        
        if page == 'result':
            print("  结算")
            return True
        if page != 'ingame':
            print(f"  离开游戏 -> {page}")
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
            except:
                pass
        time.sleep(1)
    return False

def handle_result(ocr_items):
    """结算: 找'返回'或'继续'"""
    print("  结算页面")
    # 先找返回/继续按钮
    btn = find_text_button(ocr_items, '返回') or find_text_button(ocr_items, '继续') or find_text_button(ocr_items, '下一步')
    if btn:
        tap(btn[0], btn[1])
    else:
        tap(1170, 800)
    time.sleep(5)

# ---------- 主循环 ----------
def main():
    print("=== Delta Force v3 - OCR识别 ===")
    print("首次加载OCR模型需等待...")
    get_reader()
    print("OCR就绪")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- 第{cycle}局 ---")
        img = screenshot()
        if img is None:
            time.sleep(2)
            continue
        
        t0 = time.time()
        items = ocr_image(img)
        ocr_time = time.time() - t0
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        page = detect_page(items, gray.mean())
        print(f"页面: {page}, OCR耗时: {ocr_time:.1f}s")
        
        # 打印所有检测到的文字
        if items:
            texts = [f"{t}({c:.2f})" for t, c, _, _ in items[:8]]
            print(f"  文字: {', '.join(texts)}")
        
        if page == 'lobby':
            handle_lobby(items, img)
        elif page == 'match':
            if not handle_match(items):
                continue
        elif page == 'ingame':
            handle_ingame(img)
        elif page == 'result':
            handle_result(items)
        else:
            time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
