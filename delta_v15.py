# -*- coding: utf-8 -*-
"""
三角洲行动 v15 - OCR全流程闭环版
完整流程：大厅→选图→匹配→进游戏→战斗→死亡→结算→回大厅→重复
所有页面判断基于OCR识别的文字关键词
"""
import subprocess, time, cv2, numpy as np, easyocr, sys, os

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# ===== 坐标 =====
JOY_X, JOY_Y = 265, 793      # 摇杆
FIRE_X, FIRE_Y = 2100, 850    # 射击
HEAL_X, HEAL_Y = 1800, 600    # 治疗
NEXT_X, NEXT_Y = 2060, 1003   # 下一步

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=3)

def swipe(x1, y1, x2, y2, ms):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms))], capture_output=True, timeout=8)

def keyevent(k):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'keyevent', str(k)], capture_output=True, timeout=3)

def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

# ===== 全局OCR =====
log("加载OCR...")
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
log("就绪")

def ocr_items(img):
    """OCR文字列表"""
    if img is None: return [], ''
    results = reader.readtext(img, paragraph=False)
    items = []
    for bbox, text, conf in results:
        if conf > 0.3:
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            items.append((text.strip(), cx, cy, conf))
    all_text = ' '.join([t for t, _, _, _ in items])
    return items, all_text

# ===== 页面判断 =====
def detect_page(items, all_text, img):
    """返回页面类型"""
    if img is None: return 'loading'
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = g.mean()
    
    # 退出登录确认界面
    if '确定退出登录' in all_text or '确定退出' in all_text:
        return 'logout_confirm'
    
    # 结算/死亡
    if any(k in all_text for k in ['致命一击', '淘汰回放', '下一步', '战报', '结算奖励']):
        return 'result'
    
    # 地图选择
    if any(k in all_text for k in ['零号大坝', '长弓溪谷', '航天基地', '巴克什', '战略板']):
        return 'map_select'
    
    # 匹配中（有"取消行动"）
    if '取消行动' in all_text:
        return 'matching'
    
    # 大厅（有"出发"和仓库/藏品等）
    if '出发' in all_text and any(k in all_text for k in ['藏品', '市场', '商城', '仓库']):
        return 'lobby'
    
    # 大厅（只有出发+其他底部按钮）
    if '出发' in all_text and m > 100:
        return 'lobby'
    
    # 游戏内检测（底部血条）
    if m > 40 and m < 130:
        h, w = img.shape[:2]
        bot = img[int(0.88*h):h, :]
        bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
        blue = cv2.inRange(bot_hsv, (80,50,50), (130,255,255))
        r_cnt, b_cnt = cv2.countNonZero(red), cv2.countNonZero(blue)
        if r_cnt > 300 or b_cnt > 200:
            # 双重确认：血量条颜色正确
            return 'ingame'
    
    # 公告/加载
    if any(k in all_text for k in ['政府', '秩序', '阿萨拉', '88%', '95%']):
        return 'splash'
    
    # 黑屏
    if m < 30:
        return 'loading'
    
    return 'unknown'

# ===== 各页面处理函数 =====

def handle_lobby(items, all_text):
    """大厅 → 点出发进匹配"""
    log("大厅 → 找出发按钮")
    for text, cx, cy, conf in items:
        if '出发' in text:
            log(f"  出发 ({cx},{cy})")
            tap(cx, cy)
            return True
    # 没找到文字版出发，点默认位置
    tap(1969, 973)
    return True

def handle_map_select(items, all_text):
    """选图 → 选零号大坝 → 点出发"""
    log("选图 → 找出发按钮")
    
    # 先看有没有"取消行动"（说明还在上一级）
    if '取消行动' in all_text:
        # 这是匹配界面，不是选图
        return False
    
    # 找底部出发/行动按钮
    for text, cx, cy, conf in items:
        if cy > 850 and ('出发' in text or '开始行动' in text or '行动' in text):
            log(f"  底部出发 ({cx},{cy})")
            tap(cx, cy)
            return True
    
    # 没找到出发，点"零号大坝"选中
    for text, cx, cy, conf in items:
        if '零号大坝' in text:
            log(f"  选中零号大坝 ({cx},{cy})")
            tap(cx + 60, cy + 30)
            time.sleep(1)
            # 再试出发
            tap(1170, 950)
            time.sleep(1)
            tap(1969, 973)
            return True
    
    # 点中间
    tap(1170, 950)
    return True

def handle_matching(items, all_text):
    """匹配中等待"""
    log("匹配中...")
    time.sleep(3)

def handle_splash(items, all_text):
    """公告/加载界面，点跳过"""
    log("公告 → 点跳过")
    tap(1170, 540)
    time.sleep(2)

def handle_result(items, all_text):
    """结算 → 点下一步"""
    log("结算 → 找下一步")
    for text, cx, cy, conf in items:
        if '下一步' in text:
            log(f"  下一步 ({cx},{cy})")
            tap(cx, cy)
            return
    # 没找到，点通用
    tap(2060, 1003)
    time.sleep(2)
    
    # 再结算多层的，点中间
    tap(1170, 540)
    time.sleep(1)
    tap(1170, 540)

def handle_logout_confirm(items, all_text):
    """退出登录确认 → 点取消"""
    log("退出确认 → 找取消")
    for text, cx, cy, conf in items:
        if '取消' in text:
            log(f"  取消 ({cx},{cy})")
            tap(cx, cy)
            return
    # 默认位置
    tap(931, 742)

def handle_unknown(items, all_text, img):
    """未知页面 → 尝试点中间或返回"""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img is not None else None
    m = g.mean() if g is not None else 0
    log(f"未知页面(m={m:.0f}) → 点中间")
    tap(1170, 540)
    time.sleep(1)

# ===== 游戏内战斗 =====
def handle_ingame(items, all_text, img):
    """游戏内战斗循环 - 跑一步"""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = g.mean()
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 血条
    bot = img[int(0.88*h):h, :]
    bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red_bot = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
    hp_raw = cv2.countNonZero(red_bot)
    
    log(f"战斗 m={m:.0f} hp={hp_raw}")
    
    # --- 治疗 ---
    heal_words = [('自我治疗', t, cx, cy) for t, cx, cy, c in items if '自我治疗' in t]
    gen_heal = [(t, cx, cy) for t, cx, cy, c in items if ('治疗' in t or '疗' in t) and 400 < cy < 800]
    
    if heal_words:
        _, _, cx, cy = heal_words[0]
        log(f"  自我治疗! ({cx},{cy})")
        tap(cx, cy)
        time.sleep(1)
        return
    
    if hp_raw < 400 and gen_heal:
        t, cx, cy = gen_heal[0]
        log(f"  血低+治疗按钮 ({cx},{cy})")
        tap(cx, cy)
        time.sleep(1)
        return
    
    # 血量低但没有治疗文字 → 先找找治疗
    if hp_raw < 400:
        log(f"  血低, 尝试通用治疗 ({HEAL_X},{HEAL_Y})")
        tap(HEAL_X, HEAL_Y)
        time.sleep(0.5)
        tap(HEAL_X, HEAL_Y)
        time.sleep(1)
    
    # --- 受击检测（受击指示器是半透明的红色方向标志） ---
    red = cv2.inRange(hsv, (0,80,80), (8,255,255)) | cv2.inRange(hsv, (170,80,80), (180,255,255))
    top_start, top_end = int(h*0.15), int(h*0.85)
    left = cv2.countNonZero(red[top_start:top_end, 0:80])
    right = cv2.countNonZero(red[top_start:top_end, w-80:w])
    
    if left > 3000 and left > right * 2:
        log(f"  受击左! → 右转")
        swipe(1400, 500, 2000, 500, 200)
        time.sleep(0.1)
        tap(FIRE_X, FIRE_Y)
        time.sleep(0.1)
    elif right > 3000 and right > left * 2:
        log(f"  受击右! → 左转")
        swipe(1400, 500, 800, 500, 200)
        time.sleep(0.1)
        tap(FIRE_X, FIRE_Y)
        time.sleep(0.1)
    
    # --- 正常移动 ---
    # 前进
    swipe(JOY_X, JOY_Y, JOY_X, 400, 1200)
    time.sleep(0.1)
    # 右转 + 开火
    swipe(1400, 500, 2000, 500, 200)
    time.sleep(0.05)
    tap(FIRE_X, FIRE_Y)
    time.sleep(0.05)
    tap(FIRE_X, FIRE_Y)
    time.sleep(0.1)
    # 左回 + 开火
    swipe(1400, 500, 800, 500, 200)
    time.sleep(0.05)
    tap(FIRE_X, FIRE_Y)
    time.sleep(0.1)
    # 换弹
    keyevent(23)
    time.sleep(0.2)

# ===== 主循环 =====
def main():
    log("=== 三角洲行动 v15 ===")
    cycle = 0
    battle_steps = 0
    
    while True:
        img = screenshot()
        if img is None:
            time.sleep(1)
            continue
        
        items, all_text = ocr_items(img)
        page = detect_page(items, all_text, img)
        
        # 非战斗页面时重置步数
        if page != 'ingame':
            battle_steps = 0
        
        if page == 'ingame':
            battle_steps += 1
            if cycle == 0:
                cycle = 1
            log(f"[第{cycle}局 步{battle_steps}]")
            try:
                handle_ingame(items, all_text, img)
            except Exception as e:
                log(f"  战斗异常: {e}")
                time.sleep(0.5)
        
        elif page == 'lobby':
            cycle += 1
            log(f"[第{cycle}局] 大厅")
            handle_lobby(items, all_text)
            time.sleep(3)
        
        elif page == 'map_select':
            log("[选图]")
            handle_map_select(items, all_text)
            time.sleep(3)
        
        elif page == 'matching':
            log("[匹配]")
            time.sleep(3)
        
        elif page == 'splash':
            handle_splash(items, all_text)
        
        elif page == 'result':
            log("[结算]")
            handle_result(items, all_text)
            time.sleep(2)
        
        elif page == 'logout_confirm':
            log("[退出确认]")
            handle_logout_confirm(items, all_text)
            time.sleep(1)
        
        elif page == 'loading':
            log("[加载]")
            time.sleep(2)
        
        else:
            handle_unknown(items, all_text, img)
        
        # 快循环（战斗时每步执行，非战斗时慢一点）
        if page in ['ingame']:
            pass  # 快速进入下一帧
        elif page in ['loading', 'matching']:
            time.sleep(1)
        else:
            time.sleep(0.5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log("手动停止")
