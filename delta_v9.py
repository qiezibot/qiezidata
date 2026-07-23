# -*- coding: utf-8 -*-
"""
Delta Force v9 - 正确按键位置的战斗脚本
摇杆在左侧，视角在右侧平移，射击在右下角
"""
import subprocess, time, cv2, numpy as np, os, warnings
warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')
SCREEN_DIR = r'C:\temp\delta_screenshots'
os.makedirs(SCREEN_DIR, exist_ok=True)

# ============ 关键坐标（2340x1080横屏） ============
# 摇杆中心（左半屏偏下）
JOY_X, JOY_Y = 250, 750
# 视角控制区（右半屏）
LOOK_LEFT = (800, 500)    # 向左看的drag起点
LOOK_RIGHT = (1800, 500)  # 向右看的drag起点
# 射击按钮（右下角）
FIRE_X, FIRE_Y = 2100, 850
# 地图关闭（按返回键）
BACK_KEY = '4'
# 地图选择"出发"按钮
GO_BTN = (1970, 973)

# ============ 基础操作 ============
def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=3)

def swipe(x1, y1, x2, y2, ms=50):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms))], capture_output=True, timeout=3)

def keyevent(k):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'keyevent', str(k)], capture_output=True, timeout=3)

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
PAGE_KWS = {
    'map_select': ['战略板', '零号大坝', '长弓溪谷', '航天基地', '巴克什', '黑夜行动', '危险行动', '衔尾蛇行动', '潮汐监狱', '红鼠窝'],
    'lobby': ['藏品', '市场', '商城', '通行证', '出发', '仓库', '部门', '交易', '特战', '特勤', '改枪', '全面战场', '开始行动', '烽火碎片'],
    'ingame': ['烟幕', '治疗', '自我治疗', '急救', '医疗箱', '弹药', '点击地图', '距离', '3/3', '2/3', '开镜', '大坝地', '普通', '烟幕', '烟雾'],
    'result': ['大吉大利', '胜利', '失败', '本局', '排名', '撤离', '战绩', '返回大厅', '继续'],
}

def detect_page(items, gray_mean, bottom_red, bottom_blue):
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

# ============ 游戏操作 ============
def walk_forward(steps=1):
    """摇杆向前推"""
    for _ in range(steps):
        swipe(JOY_X, JOY_Y, JOY_X, JOY_Y-400, 30)

def walk_backward(steps=1):
    """向后"""
    for _ in range(steps):
        swipe(JOY_X, JOY_Y, JOY_X, JOY_Y+200, 30)

def turn_left():
    """向左转视角：在右侧从左向右滑"""
    swipe(LOOK_LEFT[0], LOOK_LEFT[1], LOOK_LEFT[0]-300, LOOK_LEFT[1], 40)

def turn_right():
    """向右转视角：在右侧从右向左滑"""
    swipe(LOOK_RIGHT[0], LOOK_RIGHT[1], LOOK_RIGHT[0]+300, LOOK_RIGHT[1], 40)

def look_around():
    """环顾四周观察"""
    # 快速扫一圈
    swipe(800, 500, 1600, 500, 80)
    time.sleep(0.05)
    swipe(1600, 500, 800, 500, 80)
    time.sleep(0.05)
    swipe(1200, 400, 1200, 600, 80)

def fire(times=1):
    """开火"""
    for _ in range(times):
        tap(FIRE_X, FIRE_Y)
        time.sleep(0.03)

# ============ 页面处理器 ============
def handle_map_select(items):
    print("  [地图选择]")
    # 关地图？不，这是在选地图界面，点一个地图进去
    btn = ocr_find(items, ['零号大坝', '长弓溪谷', '危险行动', '黑夜行动', '航天基地', '巴克什'])
    if btn:
        tap(*btn)
        print(f"  选地图 {btn}")
    else:
        tap(900, 450)  # 中间随便点
        print("  点中间")
    time.sleep(2)
    tap(*GO_BTN)
    print(f"  出发 {GO_BTN}")
    time.sleep(5)

def handle_lobby(items):
    print("  [大厅]")
    btn = ocr_find(items, ['出发', '开始行动', '开始战'])
    if btn:
        tap(*btn)
        print(f"  出发 {btn}")
    else:
        tap(*GO_BTN)
    time.sleep(3)

def handle_match(items):
    print("  [匹配]")
    start = time.time()
    while time.time() - start < 300:
        time.sleep(2)
        img = screenshot()
        if img is None: continue
        page, items = analyze(img)
        if page in ('ingame', 'map_select', 'lobby', 'result'):
            if page == 'ingame':
                print(f"  进场!")
                handle_ingame()
            else:
                print(f"  到{page}")
            return
        elapsed = int(time.time()-start)
        if elapsed % 20 == 0 and elapsed > 0:
            print(f"  匹配中 {elapsed}s")

def handle_ingame():
    print("  [游戏中]")
    start = time.time()
    frame = 0
    
    while time.time() - start < 900:
        frame += 1
        
        # === 战斗操作 ===
        # 先环顾四周
        if frame % 8 == 0:
            look_around()
        
        # 前进（摇杆推上）
        walk_forward(3)
        
        # 开火
        fire(2)
        
        # 如果地图意外打开了，关掉
        if frame % 15 == 0:
            keyevent(BACK_KEY)
        
        # 换个方向继续
        turn_right()
        
        walk_forward(3)
        fire(1)
        
        turn_left()
        walk_forward(2)
        
        # 向前跑几步
        if frame % 3 == 0:
            walk_forward(5)
            fire(3)
        
        # 时不时后退+转向，别卡在墙上
        if frame % 5 == 0:
            walk_backward(2)
            turn_right()
            turn_right()  # 掉头
        
        # 检查状态
        if frame % 8 == 0:
            img = screenshot()
            if img is None: continue
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            m = g.mean()
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h_, w_ = g.shape
            bot = hsv[int(0.85*h_):h_, :]
            r = cv2.inRange(bot, (0,50,50), (10,255,255)) | cv2.inRange(bot, (160,50,50), (180,255,255))
            b = cv2.inRange(bot, (80,50,50), (130,255,255))
            br, bb = cv2.countNonZero(r), cv2.countNonZero(b)
            alive = br > 100 or bb > 100
            if not alive and m < 55:
                print(f"  死亡 (m={m:.0f} r={br} b={bb})")
                return
            print(f"  {int(time.time()-start)}s 活(m={m:.0f})")
    
    print("  时间到")

def handle_result(items):
    print("  [结算]")
    btn = ocr_find(items, ['返回', '继续', '回大厅', '下一步', '确认', '前往'])
    if btn:
        tap(*btn)
    else:
        # 点左上角返回
        tap(100, 100)
    time.sleep(5)

# ============ 主循环 ============
def main():
    print("=== 三角洲行动 v9 ===")
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
            time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止")
