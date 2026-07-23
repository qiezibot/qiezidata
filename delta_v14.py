# -*- coding: utf-8 -*-
"""
三角洲行动 v14 - OCR全界面识别版
每次截图→OCR识别所有文字→根据文字判断当前界面→执行对应操作
"""
import subprocess, time, cv2, numpy as np, sys, os, easyocr

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# 加载OCR（CPU模式，一次加载持续使用）
print("加载OCR...")
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
print("就绪")

# ===== 固定坐标 =====
JOY_X, JOY_Y = 265, 793      # 摇杆中心
FIRE_X, FIRE_Y = 2100, 850    # 射击
HEAL_X, HEAL_Y = 1800, 600    # 治疗区域
NEXT_X, NEXT_Y = 2060, 1003   # 下一步按钮（死亡结算）

# ===== 操作 =====
def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=3)

def swipe(x1, y1, x2, y2, ms):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms))], capture_output=True, timeout=10)

def keyevent(k):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'keyevent', str(k)], capture_output=True, timeout=3)

# ===== 截图 =====
def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

# ===== OCR识别全部文字 =====
def ocr_frame(img):
    """返回列表[(text, cx, cy, conf)]"""
    if img is None: return []
    results = reader.readtext(img, paragraph=False)
    items = []
    for bbox, text, conf in results:
        if conf > 0.3:
            tl, tr, br, bl = bbox
            cx = int((tl[0] + br[0]) / 2)
            cy = int((tl[1] + br[1]) / 2)
            items.append((text.strip(), cx, cy, conf))
    return items

# ===== 页面判断 =====
def guess_page(items, img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img is not None else None
    m = g.mean() if g is not None else 0
    all_text = ' '.join([t for t, _, _, _ in items])
    
    # 黑屏/加载
    if m < 30:
        return 'loading'
    
    # 大厅：有"藏品""市场""出发""仓库"等
    lobby_keywords = ['藏品', '市场', '商城', '通行证', '活动', '社交', '出发', '仓库', '部门', '交易行']
    if any(k in all_text for k in lobby_keywords) and m > 50:
        return 'lobby'
    
    # 地图选择：有"零号大坝""长弓溪谷""航天基地"等
    map_keywords = ['零号大坝', '长弓溪谷', '航天基地', '巴克什', '潮汐监狱', '战略板']
    if any(k in all_text for k in map_keywords):
        return 'map_select'
    
    # 匹配中：有"取消行动"
    if '取消行动' in all_text:
        return 'matching'
    
    # 游戏内：底部有红蓝血条
    if img is not None:
        h, w = img.shape[:2]
        bot = img[int(0.88*h):h, :]
        bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
        blue = cv2.inRange(bot_hsv, (80,50,50), (130,255,255))
        r_cnt, b_cnt = cv2.countNonZero(red), cv2.countNonZero(blue)
        if (r_cnt > 200 or b_cnt > 200) and m > 40 and m < 100:
            return 'ingame'
    
    # 结算/死亡：有"致命一击""淘汰回放""下一步"
    result_keywords = ['致命一击', '淘汰回放', '下一步', '战报', '结算']
    if any(k in all_text for k in result_keywords):
        return 'result'
    
    # 加载公告：有"政府与秩序"或百分比
    if '政府' in all_text or '秩序' in all_text or '阿萨拉' in all_text:
        return 'splash'
    
    return 'unknown'

# ===== 各类界面操作 =====
def handle_lobby(items):
    """大厅：点出发"""
    print("  [大厅] 找出发按钮")
    for text, cx, cy, conf in items:
        if '出发' in text:
            print(f"    找到出发 ({cx},{cy})")
            tap(cx, cy)
            time.sleep(3)
            return
    # 没找到"出发"，点一般位置
    tap(1969, 973)
    time.sleep(3)

def handle_map_select(items):
    """地图选择页面：选零号大坝"""
    print("  [选图] 找零号大坝并确认")
    
    # 先看看有没有"危险行动""黑夜行动"这些模式选项
    # 这些是地图上方的模式标签，不能点
    # 我们要的是最下面的大按钮"出发"
    
    # 找底部"出发"或"开始行动"按钮（y坐标>900）
    bottom_buttons = [(t, cx, cy, c) for t, cx, cy, c in items if cy > 800 and ('出发' in t or '开始' in t or '行动' in t)]
    
    # 先确保零号大坝被选中
    for text, cx, cy, conf in items:
        if '零号大坝' in text:
            print(f"    零号大坝在 ({cx},{cy})")
            # 如果零号大坝没有高亮（选中状态），点一下
            # 不管选没选中，先点底部出发按钮
            break
    
    if bottom_buttons:
        t, cx, cy, c = bottom_buttons[-1]  # 最下面的
        print(f"    底部出发按钮 ({cx},{cy})")
        tap(cx, cy)
        time.sleep(5)
        return
    
    # 没找到出发按钮，可能还在选地图模式
    # 点屏幕底部的常规位置
    print("  没找到出发按钮，点底部")
    tap(1170, 950)
    time.sleep(5)
    
    # 如果还没进，再试一次
    img2 = screenshot()
    if img2 is not None:
        g = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        if g.mean() > 50:
            tap(1969, 973)
            time.sleep(5)

def handle_matching(items):
    """匹配中：等待"""
    print("  [匹配中] 等待...")
    time.sleep(3)

def handle_splash(items):
    """加载公告：点空白处跳过"""
    print("  [公告] 点空白跳过")
    tap(1170, 540)
    time.sleep(2)

def handle_result(items):
    """死亡结算：点下一步"""
    print("  [结算] 找下一步")
    for text, cx, cy, conf in items:
        if '下一步' in text:
            print(f"    找到下一步 ({cx},{cy})")
            tap(cx, cy)
            time.sleep(2)
            return
    # 没找到，点通用位置
    tap(2060, 1003)
    time.sleep(2)

# ===== 游戏内战斗 =====
def handle_ingame(items, img):
    """游戏内：战斗循环"""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = g.mean()
    h, w = img.shape[:2]
    
    # 检测血量
    bot = img[int(0.88*h):h, :]
    bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red_bot = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
    hp_raw = cv2.countNonZero(red_bot)
    
    # 检测受击（屏幕中间段边缘红色）
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0,80,80), (8,255,255)) | cv2.inRange(hsv, (170,80,80), (180,255,255))
    top_start, top_end = int(h*0.15), int(h*0.85)
    left = cv2.countNonZero(red[top_start:top_end, 0:60])
    right = cv2.countNonZero(red[top_start:top_end, w-60:w])
    hit = None
    if left > 2000 and left > right * 1.5: hit = 'left'
    elif right > 2000 and right > left * 1.5: hit = 'right'
    
    print(f"  [战斗] m={m:.0f} hp={hp_raw} hit={hit}")
    
    # OCR文字检查特殊状态
    all_text = ' '.join([t for t,_,_,_ in items])
    
    # 检测到"治疗"或"自我治疗"按钮
    if '自我治疗' in all_text or '治疗' in all_text:
        for t, cx, cy, c in items:
            if '自我治疗' in t or '治疗' in t:
                print(f"  发现治疗按钮 ({cx},{cy})")
                tap(cx, cy)
                time.sleep(1)
                return
    
    # 血量极低
    if hp_raw < 600:
        print("  血量极低! 尝试治疗")
        # 寻找治疗选项
        for t, cx, cy, c in items:
            if '疗' in t or '治' in t or '包' in t:
                tap(cx, cy)
                time.sleep(1)
                return
        tap(HEAL_X, HEAL_Y)
        time.sleep(1)
        return
    
    # 受击转向
    if hit == 'left':
        swipe(1400, 500, 2000, 500, 200)
        time.sleep(0.1)
        tap(FIRE_X, FIRE_Y)
        time.sleep(0.3)
    elif hit == 'right':
        swipe(1400, 500, 800, 500, 200)
        time.sleep(0.1)
        tap(FIRE_X, FIRE_Y)
        time.sleep(0.3)
    
    # 走路+搜索
    # 往前走
    swipe(JOY_X, JOY_Y, JOY_X, 400, 1200)
    time.sleep(0.1)
    # 右转看
    swipe(1400, 500, 2000, 500, 200)
    time.sleep(0.05)
    tap(FIRE_X, FIRE_Y)  # 开火
    time.sleep(0.1)
    # 左转
    swipe(1400, 500, 800, 500, 200)
    time.sleep(0.05)
    tap(FIRE_X, FIRE_Y)
    time.sleep(0.2)
    # 换弹
    keyevent(23)

# ===== 主循环 =====
def main():
    print("=== 三角洲行动 v14 OCR版 ===")
    cycle = 0
    
    while True:
        cycle += 1
        img = screenshot()
        if img is None:
            print(f"[{cycle}] 截图失败")
            time.sleep(2)
            continue
        
        # OCR
        items = ocr_frame(img)
        
        if items:
            # 打印前几个文字
            preview = ' '.join([t[:8] for t,_,_,_ in items[:5]])
            print(f"\n[{cycle}] {preview}...")
        else:
            print(f"\n[{cycle}] 无文字识别")
        
        # 判断页面
        page = guess_page(items, img)
        print(f"  页面: {page}")
        
        if page == 'lobby':
            handle_lobby(items)
        elif page == 'map_select':
            handle_map_select(items)
        elif page == 'matching':
            handle_matching(items)
        elif page == 'splash':
            handle_splash(items)
        elif page == 'result':
            handle_result(items)
        elif page == 'ingame':
            handle_ingame(items, img)
        elif page == 'loading':
            print("  加载中...")
            time.sleep(2)
        else:
            print("  未知页面，点中间跳过")
            tap(1170, 540)
            time.sleep(2)

if __name__ == '__main__':
    main()
