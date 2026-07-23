# -*- coding: utf-8 -*-
import cv2, numpy as np, os, time, subprocess, warnings
warnings.filterwarnings('ignore')

import cv2, numpy as np, os, time, subprocess, warnings
warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

def ss():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def tap(x,y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True)

# OCR懒加载
_reader = None
def do_ocr(img):
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['ch_sim','en'], gpu=False)
    results = _reader.readtext(img, paragraph=False)
    items = []
    for bbox,text,conf in results:
        if conf < 0.3: continue
        tl,tr,br,bl = bbox
        cx,cy = int((tl[0]+br[0])/2), int((tl[1]+br[1])/2)
        items.append((text.strip(), conf, (cx,cy)))
    return items

def guess_page(items, gmean):
    text = ' '.join([t for t,_,_ in items])
    if any(k in text for k in ['距离','烟幕','弹药','治疗','自我治疗','急救','点击地图']):
        return 'ingame'
    if any(k in text for k in ['开始行动','全面战场','烽火','藏品','市场','商城','通行证','活动','社交','邮件','设置','出发']):
        return 'lobby'
    if any(k in text for k in ['搜索中','等待']):
        return 'match'
    if any(k in text for k in ['大吉大利','胜利','失败','本局','排名','撤离','战绩']):
        return 'result'
    if gmean > 100:
        return 'result'
    return None

def find_btn(items, kws):
    for kw in kws:
        for text,_,pos in items:
            if kw in text:
                return pos
    return None

def page_switch():
    """等画面稳定后OCR判断当前页面"""
    time.sleep(1)
    img = ss()
    if img is None:
        return None, None
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    items = do_ocr(img)
    p = guess_page(items, g.mean())
    return p, img

def is_ingame_fast(gray, img):
    h,w = gray.shape
    # 小地图
    mm = gray[20:220, 20:220]
    if mm.mean() > 30:
        bl = cv2.medianBlur(mm, 5)
        cs = cv2.HoughCircles(bl, cv2.HOUGH_GRADIENT, 1, 100, param1=80, param2=30, minRadius=60, maxRadius=110)
        if cs is not None:
            return True
    # 底部颜色
    if img is not None:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        b = hsv[h-100:h, :]
        r = cv2.inRange(b, (0,50,50), (10,255,255)) | cv2.inRange(b, (160,50,50), (180,255,255))
        bl = cv2.inRange(b, (80,50,50), (130,255,255))
        if cv2.countNonZero(bl) > 200 and cv2.countNonZero(r) > 100:
            return True
    return False

def run_game_loop():
    """游戏中循环"""
    try:
        from ultralytics import YOLO
        model = YOLO(r'C:\u-claw\portable\data\.openclaw\workspace\yolov8n.pt')
    except:
        model = None
    
    start = time.time()
    while time.time() - start < 900:
        img = ss()
        if img is None:
            time.sleep(1)
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = gray.mean()
        
        # 黑暗 -> 退出
        if m < 50:
            print(f"  黑暗(m={m:.0f}), 退出")
            return False
        
        # 不在游戏中 -> OCR确认
        if not is_ingame_fast(gray, img):
            time.sleep(1)
            items = do_ocr(img)
            p = guess_page(items, m)
            print(f"  非游戏中, OCR={p}")
            if p != 'ingame':
                return False
            # OCR说ingame但特征说不是, 继续
            continue
        
        # YOLO
        if model and m > 50:
            try:
                results = model(img, conf=0.3, iou=0.4, verbose=False)
                for r in results:
                    if r.boxes is None: continue
                    for box in r.boxes:
                        x1,y1,x2,y2 = box.xyxy[0].tolist()
                        cx,cy = int((x1+x2)/2), int((y1+y2)/2)
                        cf = box.conf[0].item()
                        if cf > 0.4:
                            for _ in range(3):
                                tap(cx,cy)
                                time.sleep(0.1)
            except:
                pass
        time.sleep(2)
    return False

def run():
    print("=== Delta v6 ===")
    img = ss()
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"初始 mean={g.mean():.0f}")
    
    # 初始画面: 先用OCR定位
    items = do_ocr(img)
    page = guess_page(items, g.mean())
    print(f"初始页面: {page}")
    
    if page == 'ingame':
        run_game_loop()
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- 第{cycle}局 ---")
        
        # 每次从头OCR判断
        img = ss()
        if img is None: continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        items = do_ocr(img)
        page = guess_page(items, g.mean())
        print(f"页面: {page} mean={g.mean():.0f}")
        
        if page is None:
            # OCR判断不了, 用特征
            if is_ingame_fast(g, img):
                print("  特征=ingame")
                page = 'ingame'
            elif g.mean() > 100:
                print("  特征=result")
                page = 'result'
            else:
                time.sleep(3)
                continue
        
        if page == 'lobby':
            btn = find_btn(items, ['出发', '开始行动', '开始战', '行动'])
            if btn:
                print(f"  点 '出发/开始行动' {btn}")
                tap(btn[0], btn[1])
            else:
                # 找不到, 点右下角
                tap(1970, 973)
                print("  点出发位置")
            time.sleep(3)
        
        elif page == 'match':
            print("  匹配中...")
            start_m = time.time()
            entered = False
            while time.time() - start_m < 300:
                time.sleep(2)
                img_m = ss()
                if img_m is None: continue
                gm = cv2.cvtColor(img_m, cv2.COLOR_BGR2GRAY)
                if is_ingame_fast(gm, img_m):
                    print(f"  [{int(time.time()-start_m)}s] 进场!")
                    entered = True
                    break
                if int(time.time()-start_m) % 15 == 0:
                    print(f"  [{int(time.time()-start_m)}s] ...")
            if entered:
                run_game_loop()
        
        elif page == 'ingame':
            run_game_loop()
        
        elif page == 'result':
            btn = find_btn(items, ['返回', '继续', '确认', '回大厅'])
            if btn:
                tap(btn[0], btn[1])
                print(f"  点返回 {btn}")
            else:
                tap(200, 100)
                print("  点左上角")
            time.sleep(5)

if __name__ == '__main__':
    try: run()
    except KeyboardInterrupt: print("\n停止")
