# -*- coding: utf-8 -*-
"""
三角洲行动 - 完整战斗循环 v13
2026-06-12 根据学习资料重写
核心玩法理解：
  烽火地带 = 搜物资 + 打人 + 撤离
  摇杆：左下角 (265, 793)
  移动：swipe(摇杆x, 摇杆y, 目标x, 目标y, 时长)
  转视角：右半屏滑动 (右滑=向右看)
  射击：右下角 (2100, 850)
  治疗：右侧偏下
  换武器：keyevent 1/2/3
  换弹：keyevent 23 (R)
  交互/E：关键交互键
  地图M：keyevent 50
  背包Tab：keyevent 61
"""
import subprocess, time, cv2, numpy as np, sys, os

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# ===== 固定坐标（基于2340x1080横屏） =====
# 摇杆（之前检测到圆形在左下角）
JOY_X, JOY_Y = 265, 793
# 模拟摇杆前推目标
JOY_FRONT_X, JOY_FRONT_Y = 265, 400
# 模拟摇杆后拉
JOY_BACK_X, JOY_BACK_Y = 265, 950
# 模拟摇杆左移
JOY_LEFT_X, JOY_LEFT_Y = JOY_X - 100, JOY_Y
# 模拟摇杆右移
JOY_RIGHT_X, JOY_RIGHT_Y = JOY_X + 100, JOY_Y

# 转视角（右半屏中心拖拽）
TURN_CENTER_X, TURN_CENTER_Y = 1400, 500

# 射击（右下角）
FIRE_X, FIRE_Y = 2100, 850

# 治疗区域（右侧偏下，药品在技能栏附近或快捷治疗）
HEAL_X, HEAL_Y = 1800, 600

# 交互/拾取/E键位置
INTERACT_X, INTERACT_Y = 1600, 700

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

# ===== 状态判断 =====
def check_ingame(img):
    """判断是否在游戏中"""
    if img is None: return False
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = g.mean()
    if m < 30: return False  # 纯黑/加载
    
    # 底部血条检测
    bot = img[int(0.88*h):h, :]
    bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
    blue = cv2.inRange(bot_hsv, (80,50,50), (130,255,255))
    r_cnt = cv2.countNonZero(red)
    b_cnt = cv2.countNonZero(blue)
    return (r_cnt > 100 or b_cnt > 100) and m > 40

def check_health(img):
    """血量检测，返回(1-100)"""
    h, w = img.shape[:2]
    bot = img[int(0.88*h):h, :]
    bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
    r_cnt = cv2.countNonZero(red)
    # 满血约8000红像素
    hp = min(r_cnt / 80, 100)
    return hp

def check_armor(img):
    """护甲检测"""
    h, w = img.shape[:2]
    bot = img[int(0.88*h):h, :]
    bot_hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    blue = cv2.inRange(bot_hsv, (80,50,50), (130,255,255))
    b_cnt = cv2.countNonZero(blue)
    ap = min(b_cnt / 80, 100)
    return ap

def check_hit(img):
    """受击检测：游戏内中弹时会有半透明红色方向指示器
    改进：用高频闪烁+仅取边缘中间段（避开UI和血条）"""
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 取更窄的红色范围（避开UI的橙色/红色按钮）
    red = cv2.inRange(hsv, (0,80,80), (8,255,255)) | cv2.inRange(hsv, (170,80,80), (180,255,255))
    margin = 60  # 边缘宽度
    # 只取边缘的中间段（避开底部血条和顶部菜单）
    top_start = int(h * 0.15)
    top_end = int(h * 0.85)
    
    left_zone = red[top_start:top_end, 0:margin]
    right_zone = red[top_start:top_end, w-margin:w]
    top_zone = red[int(h*0.05):int(h*0.15), int(w*0.2):int(w*0.8)]
    bot_zone = red[int(h*0.85):int(h*0.95), int(w*0.2):int(w*0.8)]
    
    left = cv2.countNonZero(left_zone)
    right = cv2.countNonZero(right_zone)
    top = cv2.countNonZero(top_zone)
    bot_edge = cv2.countNonZero(bot_zone)
    
    # 更高的阈值（真正受击的红色指示器很亮很明显）
    threshold = 1500
    if left > threshold and left > right * 2:  # 左侧明显多于右侧才是左侧受击
        return 'left'
    if right > threshold and right > left * 2:
        return 'right'
    if top > 500:
        return 'front'
    if bot_edge > 500:
        return 'back'
    return None

def check_dead(img):
    """死亡检测：画面灰暗+无血条"""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = g.mean()
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    avg_sat = hsv[:,:,1].mean()
    # 死亡特征：饱和度极低 + 中度亮度（不是黑屏也不是亮画面）
    if avg_sat < 30 and 30 < m < 80:
        return True
    # 或者黑屏（m<30）+长时间没血条
    if m < 25:
        return True
    return False

# ===== 游戏内操作 =====
def walk_front(duration=1500):
    """摇杆前推走路"""
    swipe(JOY_X, JOY_Y, JOY_FRONT_X, JOY_FRONT_Y, duration)

def turn_right(t=150):
    """右转视角"""
    swipe(TURN_CENTER_X, TURN_CENTER_Y, TURN_CENTER_X+400, TURN_CENTER_Y, t)

def turn_left(t=150):
    """左转视角"""
    swipe(TURN_CENTER_X, TURN_CENTER_Y, TURN_CENTER_X-400, TURN_CENTER_Y, t)

def look_up(t=100):
    """抬头"""
    swipe(TURN_CENTER_X, TURN_CENTER_Y, TURN_CENTER_X, TURN_CENTER_Y-200, t)

def shoot(count=3, delay=0.08):
    """连射"""
    for _ in range(count):
        tap(FIRE_X, FIRE_Y)
        time.sleep(delay)

def reload_weapon():
    """换弹R"""
    keyevent(23)  # R
    time.sleep(0.3)

def switch_melee():
    """切近战刀"""
    keyevent(3)  # 3键
    time.sleep(0.3)

def switch_primary():
    """切主武器"""
    keyevent(1)  # 1键
    time.sleep(0.3)

def heal():
    """自我治疗"""
    # 点治疗区域（药品/治疗按钮）
    tap(HEAL_X, HEAL_Y)
    time.sleep(0.2)
    tap(HEAL_X, HEAL_Y)
    time.sleep(1)

def interact():
    """交互/拾取/开门"""
    tap(INTERACT_X, INTERACT_Y)
    time.sleep(0.2)

def call_help():
    """倒地呼救"""
    for _ in range(3):
        tap(1500, 600)
        time.sleep(0.2)
        tap(2000, 900)
        time.sleep(0.2)
        tap(1170, 540)
        time.sleep(0.3)

# ===== 主战斗循环 =====
def battle_loop():
    """战斗主循环"""
    print("========== 战斗循环开始 ==========")
    step = 0
    no_ingame_count = 0
    heal_cooldown = 0  # 治疗冷却
    
    while True:
        step += 1
        img = screenshot()
        if img is None:
            print(f"[{step}] 截图失败")
            time.sleep(1)
            continue
        
        # 判断是否在游戏内
        if not check_ingame(img):
            no_ingame_count += 1
            print(f"[{step}] 不在游戏中 {no_ingame_count}")
            if no_ingame_count > 10:
                print("  连续10次不在游戏，退出战斗循环")
                return "exit_game"
            time.sleep(1)
            continue
        no_ingame_count = 0
        
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = g.mean()
        hp = check_health(img)
        ap = check_armor(img)
        
        # 血条闪烁提示
        bot_hsv = cv2.cvtColor(img[int(0.88*img.shape[0]):img.shape[0], :], cv2.COLOR_BGR2HSV)
        red_bot = cv2.inRange(bot_hsv, (0,50,50), (10,255,255)) | cv2.inRange(bot_hsv, (160,50,50), (180,255,255))
        hp_raw = cv2.countNonZero(red_bot)
        
        print(f"[{step}] m={m:.0f} hp={hp_raw}")
        
        # --- 血量低/没血了 ---
        if hp_raw < 200:
            print(f"  ⚠️ 快没血了！hp_raw={hp_raw}")
            # 有可能是死亡结算界面，检查
            if check_dead(img):
                print("  💀 死亡结算")
                tap(2060, 1003)
                time.sleep(1)
                return "dead"
            heal()
            heal_cooldown = 5
            time.sleep(1)
            continue
        
        # --- 治疗（血量低于25%） ---
        if 0 < hp < 25 and heal_cooldown <= 0:
            print(f"  💊 血量{hp:.0f}%，治疗")
            heal()
            heal_cooldown = 10
            time.sleep(1.5)
        
        if heal_cooldown > 0:
            heal_cooldown -= 1
        
        # --- 受击检测 ---
        hit_dir = check_hit(img)
        if hit_dir:
            print(f"  🔴 受击！方向:{hit_dir}")
            if hit_dir == 'left':
                turn_right(200)
            elif hit_dir == 'right':
                turn_left(200)
            elif hit_dir == 'front':
                turn_right(200)
            elif hit_dir == 'back':
                turn_right(350)
            time.sleep(0.1)
            # 回头开火
            shoot(3)
            time.sleep(0.3)
        
        # --- 正常战斗动作 ---
        # 每4步换方向走路
        if step % 4 == 0:
            print("  🚶 前进")
            walk_front(1200)
        elif step % 4 == 1:
            print("  🔄 右转")
            turn_right(200)
            shoot(3)
        elif step % 4 == 2:
            print("  🚶 前进")
            walk_front(800)
        elif step % 4 == 3:
            print("  🔄 左转扫射")
            turn_left(200)
            shoot(5)
        
        # 打完切刀/换弹
        if step % 6 == 0:
            reload_weapon()
        
        if step > 500:
            print("  超过500步，休息一下")
            return "max_steps"
        
        # 检查是否死亡（每3步检查一次完整画面特征）
        if step % 3 == 0:
            if check_dead(img):
                print("  💀 死亡！尝试呼救")
                call_help()
                time.sleep(0.5)
                # 等死/结算
                time.sleep(1)
                # 点击下一步
                tap(2060, 1003)
                time.sleep(1)
                return "dead"

# ===== 大厅操作 =====
def lobby_loop():
    """大厅判断+点出发"""
    print("========== 大厅/匹配循环 ==========")
    step = 0
    while step < 30:
        step += 1
        img = screenshot()
        if img is None:
            time.sleep(1)
            continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = g.mean()
        print(f"[大厅] mean={m:.0f}")
        
        if check_ingame(img):
            print("  已经进游戏了，切到战斗")
            return "goto_battle"
        
        if m < 30:
            print("  黑屏/加载中")
            time.sleep(2)
            continue
        
        if m > 50:
            # 可能是大厅，点"出发" 
            print("  尝试点出发...")
            tap(1969, 973)  # 出发按钮
            time.sleep(2)
        
        time.sleep(1)
    
    return "timeout"

# ===== 主入口 =====
def main():
    print("=== 三角洲行动 v13 ===")
    cycle = 0
    
    while True:
        cycle += 1
        img = screenshot()
        if img is None:
            print("截图失败，重试")
            time.sleep(2)
            continue
        
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        m = g.mean()
        
        if check_ingame(img):
            print(f"\n--- 第{cycle}局: 检测到游戏中 ---")
            result = battle_loop()
            print(f"  战斗结束: {result}")
        elif m > 50:
            print(f"\n--- 第{cycle}局: 大厅 ---")
            result = lobby_loop()
            print(f"  大厅结束: {result}")
        else:
            print(f"等待... mean={m:.0f}")
            time.sleep(2)

if __name__ == '__main__':
    main()
