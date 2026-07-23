# -*- coding: utf-8 -*-
"""
Delta Force 自动化 v7
画面识别引擎 delta_v7_vision.py + 循环逻辑
"""
import subprocess, os, sys, time, cv2, numpy as np
import warnings; warnings.filterwarnings('ignore')

# 引入画面识别模块
sys.path.insert(0, os.path.dirname(__file__))
import delta_v7_vision as vision

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')
MAX_GAME_MINUTES = 15

tap = vision.tap

def ocr_find(items, keywords):
    for kw in keywords:
        for text, conf, pos in items:
            if kw in text:
                return pos
    return None

# ========== 页面处理器 ==========
def handle_lobby(img, items):
    print("  [大厅]")
    btn = ocr_find(items, ['出发', '开始行动', '开始战', '行动'])
    if btn:
        print(f"  点击 {btn}")
        tap(*btn)
    else:
        # OCR找不到，分析特征右下角
        h,w = img.shape[:2]
        tap(int(w*0.84), int(h*0.9))
        print(f"  点右下角")
    time.sleep(3)

def handle_match(img, items):
    print("  [匹配]")
    start = time.time()
    while time.time() - start < 300:
        time.sleep(2)
        img = vision.screenshot()
        if img is None:
            continue
        items = vision.ocr(img)
        page, feat = vision.detect_page(img, items)
        if page == 'ingame':
            print(f"  [{int(time.time()-start)}s] 进场!")
            handle_ingame(img, items)
            return
        if page == 'lobby' or page == 'result':
            print(f"  [{int(time.time()-start)}s] 回到{page}")
            return
        if int(time.time()-start) % 15 == 0:
            print(f"  [{int(time.time()-start)}s] ...")
    print("  匹配超时")

def handle_ingame(img, items):
    print("  [游戏中]")
    # 只在进场时加载YOLO（节省时间）
    model = None
    try:
        from ultralytics import YOLO
        model = YOLO(r'C:\u-claw\portable\data\.openclaw\workspace\yolov8n.pt')
    except:
        pass
    
    dark_count = 0
    start = time.time()
    while time.time() - start < MAX_GAME_MINUTES*60:
        time.sleep(2)
        img = vision.screenshot()
        if img is None: continue
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = gray.mean()
        
        # 黑暗：可能退出/黑屏
        if m < 50:
            dark_count += 1
            if dark_count > 5:
                print("  黑暗退出")
                return
            continue
        dark_count = 0
        
        # 快速特征检测是否还在游戏中
        feat = vision.extract_features(img)
        if feat['bottom_red'] < 200 and feat['bottom_blue'] < 100:
            # 特征不像游戏中，OCR确认
            items = vision.ocr(img)
            page, _ = vision.detect_page(img, items)
            if page != 'ingame':
                print(f"  页面变化: {page}")
                return
            continue
        
        # YOLO检测敌人
        if model:
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
                                tap(cx, cy)
                                time.sleep(0.1)
            except:
                pass

def handle_result(img, items):
    print("  [结算]")
    btn = ocr_find(items, ['返回', '继续', '确认', '回大厅', '下一步'])
    if btn:
        tap(*btn)
        print(f"  点击返回 {btn}")
    else:
        # 找不到返回按钮
        h,w = img.shape[:2]
        # 尝试左下角
        tap(200, 100)
        print("  点左上角")
    time.sleep(5)

# ========== 主循环 ==========
def main():
    print("=== Delta Force v7 ===")
    print("加载OCR...")
    dummy = vision.screenshot()
    vision.ocr(dummy)  # 预热
    print("就绪!\n")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"--- 第{cycle}局 ---")
        
        img = vision.screenshot()
        if img is None:
            time.sleep(2)
            continue
        items = vision.ocr(img)
        page, feat = vision.detect_page(img, items)
        m = feat['mean']
        print(f"页面: {page} mean={m:.0f} 红={feat['bottom_red']} 蓝={feat['bottom_blue']}")
        
        if page == 'lobby':
            handle_lobby(img, items)
        elif page == 'match':
            handle_match(img, items)
        elif page == 'ingame':
            handle_ingame(img, items)
        elif page == 'result':
            handle_result(img, items)
        elif page == 'black':
            print("  黑屏,等3s")
            time.sleep(3)
        else:
            print("  未知,等3s")
            time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
