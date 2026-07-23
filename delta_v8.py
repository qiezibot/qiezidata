# -*- coding: utf-8 -*-
"""
Delta Force v8 - 正经战斗脚本
- 画面识别（所有页面）+ 自动化操作
- 游戏中：走位开火
- 全部基于adb，不需要图像处理耗时
"""
import subprocess, time, cv2, numpy as np, os, sys, warnings
warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')
SCREEN_DIR = r'C:\temp\delta_screenshots'
os.makedirs(SCREEN_DIR, exist_ok=True)

# ============ 基础操作 ============
def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=3)

def swipe(x1, y1, x2, y2, ms=50):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms))], capture_output=True, timeout=3)

# ============ 截图 ============
_reader = None
def ocr(img):
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

def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def ocr_find(items, keywords):
    for kw in keywords:
        for text, conf, pos in items:
            if kw in text:
                return pos
    return None

# ============ 页面识别 ============
# 按页面组织关键词
PAGE_KWS = {
    'map_select': ['战略板', '零号大坝', '长弓溪谷', '航天基地', '巴克什', '黑夜行动', '危险行动'],
    'lobby': ['藏品', '市场', '商城', '通行证', '出发', '仓库', '部门', '交易', '特战', '特勤', '改枪', '全面战场', '开始行动', '烽火碎片'],
    'ingame': ['烟幕', '治疗', '自我治疗', '急救', '医疗箱', '弹药', '点击地图', '距离', '3/3', '2/3', '开镜', '大坝地', '普通'],
    'result': ['大吉大利', '胜利', '失败', '本局', '排名', '撤离', '战绩', '返回大厅', '继续',
               '总分', '击杀', '伤害', '承伤', '救援', '存活时间'],
    'match': ['搜索中', '等待', '匹配', '队列'],
}

def detect_page(items, gray_mean, bottom_red, bottom_blue):
    # OCR关键词匹配
    all_text = ' '.join([t for t,_,_ in items])
    
    for page, kws in PAGE_KWS.items():
        for kw in kws:
            if kw in all_text:
                return page
    
    # 特征判断
    if bottom_red > 500 or bottom_blue > 200:
        return 'ingame'
    if gray_mean > 100 and bottom_red < 200:
        return 'result'
    if gray_mean < 40:
        return 'black'
    if 40 < gray_mean < 100 and bottom_red < 200:
        return 'unknown'
    
    return 'unknown'

def analyze(img):
    items = ocr(img)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    bot = hsv[int(0.85*h):h, :]
    r = cv2.inRange(bot, (0,50,50), (10,255,255)) | cv2.inRange(bot, (160,50,50), (180,255,255))
    b = cv2.inRange(bot, (80,50,50), (130,255,255))
    br, bb = cv2.countNonZero(r), cv2.countNonZero(b)
    page = detect_page(items, g.mean(), br, bb)
    return page, items

# ============ 页面处理器 ============
def handle_map_select(items):
    """地图选择界面 -> 选模式进入"""
    print("  [地图选择]")
    # 找地图按钮，点任意一个
    btn = ocr_find(items, ['零号大坝', '长弓溪谷', '危险行动', '黑夜行动'])
    if btn:
        print(f"  选地图 {btn}")
        tap(*btn)
        time.sleep(2)
        # 点确认/开始
        img2 = screenshot()
        items2 = ocr(img2)
        go = ocr_find(items2, ['出发', '开始', '确认', '行动'])
        if go:
            tap(*go)
            print(f"  出发 {go}")
        else:
            tap(1970, 973)  # 出发按钮位置
        time.sleep(3)
        return True
    # 找个位置点
    tap(940, 300)  # 点一个地图
    time.sleep(2)
    tap(1970, 973)  # 出发
    time.sleep(3)
    return True

def handle_lobby(items):
    """大厅 -> 点击出发"""
    print("  [大厅]")
    btn = ocr_find(items, ['出发', '开始行动', '开始战', '行动'])
    if btn:
        print(f"  点击 {btn}")
        tap(*btn)
    else:
        tap(1970, 973)
        print("  点出发位置")
    time.sleep(3)

def handle_match(items):
    """匹配 -> 等待进场"""
    print("  [匹配]")
    start = time.time()
    while time.time() - start < 300:
        time.sleep(2)
        img = screenshot()
        if img is None: continue
        page, items = analyze(img)
        if page == 'ingame':
            print(f"  [{int(time.time()-start)}s] 进场!")
            handle_ingame()
            return
        if page in ('lobby', 'result', 'map_select'):
            print(f"  [{int(time.time()-start)}s] 回到{page}")
            return
        if int(time.time()-start) % 15 == 0:
            print(f"  [{int(time.time()-start)}s] ...")

def handle_ingame():
    """游戏中 -> 真的打起来！"""
    print("  [游戏中 - 战斗]")
    start = time.time()
    frame = 0
    
    while time.time() - start < 900:
        frame += 1
        
        # ----- 战斗操作 -----
        # 1. 转头观察（先右后左）
        swipe(1800, 500, 2200, 500, 60)
        
        # 2. 向前跑
        for _ in range(3):
            swipe(400, 700, 400, 200, 20)
        
        # 3. 开火！
        tap(2200, 850)
        time.sleep(0.03)
        tap(2200, 850)
        
        # 4. 左转看看
        swipe(1800, 500, 1400, 500, 60)
        
        # 5. 前进
        for _ in range(3):
            swipe(400, 700, 400, 200, 20)
        
        tap(2200, 850)
        time.sleep(0.03)
        tap(2200, 850)
        
        # 每5轮大幅转向
        if frame % 5 == 0:
            # 回头看
            swipe(1400, 500, 2000, 500, 100)
            for _ in range(5):
                swipe(400, 200, 400, 700, 20)
            swipe(2000, 500, 1400, 500, 100)
        
        # 每5轮检查状态+保存截图做分析
        if frame % 5 == 0:
            img = screenshot()
            if img is None: continue
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            m = g.mean()
            if m < 50:
                # 先策略打法：躲一下不跑
                time.sleep(2)
                # 回头跑
                swipe(1400, 500, 2000, 500, 100)
                for _ in range(5):
                    swipe(400, 200, 400, 700, 30)
                time.sleep(1)
                img2 = screenshot()
                if img2 is not None:
                    m2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY).mean()
                    if m2 < 50:
                        print(f"  死亡(s={m:.0f}m={m2:.0f})")
                        return
            print(f"  战斗 {int(time.time()-start)}s")
    
    print("  游戏时间到")

def handle_result(items):
    """结算 -> 点返回"""
    print("  [结算]")
    btn = ocr_find(items, ['返回', '继续', '确认', '回大厅', '下一步'])
    if btn:
        tap(*btn)
        print(f"  点击返回 {btn}")
    else:
        tap(200, 100)
        print("  点左上角")
    time.sleep(5)

# ============ 主循环 ============
def main():
    print("=== 三角洲行动 v8 ===")
    print("加载OCR...")
    dummy = screenshot()
    ocr(dummy)
    print("就绪!")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- 第{cycle}局 ---")
        
        img = screenshot()
        if img is None: continue
        page, items = analyze(img)
        print(f"页面: {page}")
        
        if page == 'map_select':
            handle_map_select(items)
        elif page == 'lobby':
            handle_lobby(items)
        elif page == 'match':
            handle_match(items)
        elif page == 'ingame':
            handle_ingame()
        elif page == 'result':
            handle_result(items)
        else:
            print("  未知页面, 等3s")
            time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
