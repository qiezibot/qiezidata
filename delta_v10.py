# -*- coding: utf-8 -*-
"""
Delta Force v10 - 真正会走的战斗脚本
核心改进：长拽摇杆（800ms+）代替短滑，让人物真正移动
"""
import subprocess, time, cv2, numpy as np, os, warnings
warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# ============ 关键坐标（2340x1080横屏） ============
JOY_X, JOY_Y = 250, 750        # 摇杆中心
FIRE_X, FIRE_Y = 2100, 850      # 射击按钮
GO_BTN = (1970, 973)            # 出发按钮
BACK_KEY = '4'

# ============ 基础操作 ============
def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=3)

def swipe(x1, y1, x2, y2, ms=50):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms))], capture_output=True, timeout=3)

def keyevent(k):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'keyevent', str(k)], capture_output=True, timeout=3)

# ============ 移动操作 ============
# 关键思路：用长拖拽（800ms）让人物持续走动
def walk_forward(ms=800):
    """按住摇杆向前推动"""
    swipe(JOY_X, JOY_Y, JOY_X, JOY_Y-400, ms)

def walk_backward(ms=600):
    """向后走"""
    swipe(JOY_X, JOY_Y, JOY_X, JOY_Y+200, ms)

def walk_left(ms=600):
    """向左走"""
    swipe(JOY_X, JOY_Y, JOY_X-400, JOY_Y, ms)

def walk_right(ms=600):
    """向右走"""
    swipe(JOY_X, JOY_Y, JOY_X+400, JOY_Y, ms)

def turn_right():
    """向右转头（屏幕右侧向左滑动）"""
    swipe(1500, 500, 2100, 500, 200)

def turn_left():
    """向左转头"""
    swipe(1500, 500, 900, 500, 200)

def turn_back():
    """向后转头（半秒转180度）"""
    swipe(900, 500, 2100, 500, 200)
    time.sleep(0.1)
    swipe(900, 500, 2100, 500, 200)

def fire(times=1):
    for _ in range(times):
        tap(FIRE_X, FIRE_Y)
        time.sleep(0.05)

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

# ============ 页面识别 ============
PAGE_KWS = {
    'map_select': ['战略板', '零号大坝', '长弓溪谷', '航天基地', '巴克什', '黑夜行动', '危险行动', '衔尾蛇', '潮汐监狱', '红鼠窝'],
    'lobby': ['藏品', '市场', '商城', '通行证', '出发', '仓库', '部门', '交易', '特战', '特勤', '改枪', '全面战场', '开始行动', '烽火碎片'],
    'ingame': ['烟幕', '治疗', '自我治疗', '急救', '医疗箱', '弹药', '点击地图', '3/3', '开镜', '大坝地', '普通', '烟雾', '防守此处'],
    'result': ['大吉大利', '胜利', '失败', '本局', '排名', '撤离', '战绩', '返回大厅', '继续', '段位'],
}

def detect_page(items, gray_mean, bottom_red, bottom_blue):
    all_text = ' '.join([t for t,_,_ in items])
    for page, kws in PAGE_KWS.items():
        for kw in kws:
            if kw in all_text:
                return page
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
    return detect_page(items, g.mean(), br, bb), items

# ============ 页面处理器 ============
def handle_map_select(items):
    print("  [地图选择]")
    btn = None
    for kw in ['零号大坝', '长弓溪谷', '危险行动', '黑夜行动', '航天基地', '巴克什']:
        for text, conf, pos in items:
            if kw in text:
                btn = pos
                break
        if btn: break
    if btn:
        tap(*btn)
    else:
        tap(900, 450)
    time.sleep(2)
    tap(*GO_BTN)
    time.sleep(5)

def handle_lobby(items):
    print("  [大厅]")
    for text, conf, pos in items:
        if '出发' in text or '开始行动' in text:
            tap(*pos)
            print(f"  出发 {pos}")
            time.sleep(3)
            return
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
        e = int(time.time()-start)
        if e % 30 == 0 and e > 0: print(f"  匹配中 {e}s")

def handle_ingame():
    print("  [游戏中]")
    start = time.time()
    frame = 0
    
    while time.time() - start < 900:
        frame += 1
        
        # ---- 真正在战场上走动！ ----
        # 先往前走
        walk_forward(1000)   # 走1秒
        time.sleep(0.2)
        fire(3)
        
        # 转头看右边
        turn_right()
        walk_forward(800)
        time.sleep(0.2)
        fire(2)
        
        # 向左走
        walk_left(500)
        turn_left()
        walk_forward(600)
        time.sleep(0.1)
        fire(3)
        
        # 向右平移
        walk_right(500)
        turn_right()
        walk_forward(500)
        fire(2)
        
        # 掉头往后走（换个方向探索）
        if frame % 3 == 0:
            turn_back()
            walk_forward(800)
            fire(3)
            time.sleep(0.2)
            turn_back()
        
        # 检查状态
        if frame % 4 == 0:
            img = screenshot()
            if img is None: continue
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            m = g.mean()
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h_, w_ = g.shape
            bot = hsv[int(0.85*h_):h_, :]
            r = cv2.inRange(bot, (0,50,50), (10,255,255)) | cv2.inRange(bot, (160,50,50), (180,255,255))
            b = cv2.inRange(bot, (80,50,50), (130,255,255))
            alive = cv2.countNonZero(r) > 100 or cv2.countNonZero(b) > 100
            if not alive and m < 55:
                print(f"  死亡 (m={m:.0f})")
                return
            print(f"  {int(time.time()-start)}s m={m:.0f}")
    
    print("  时间到")

def handle_result(items):
    print("  [结算]")
    for text, conf, pos in items:
        if any(kw in text for kw in ['返回', '继续', '回大厅', '下一步', '确认']):
            tap(*pos)
            time.sleep(5)
            return
    tap(100, 100)
    time.sleep(5)

# ============ 主循环 ============
def main():
    print("=== 三角洲行动 v10 真走动版 ===")
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
