# -*- coding: utf-8 -*-
"""
Delta Force - 跑刀脚本 v7.2
核心：小地图圆检测 + 固定序列 + 自动循环
"""

import subprocess, time, os, sys, cv2, numpy as np

sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # win

ADB_PATH = r"D:\MuMuPlayer\nx_main\adb.exe"
DEVICE = "1aabaaeb"
W, H = 2340, 1080
JOY_C = (430, 780)
JOY_UP = (430, 350)
PICKUP = (1600, 280)

def adb(*a, bin=False, t=30):
    cmd = [ADB_PATH, "-s", DEVICE] + list(a)
    r = subprocess.run(cmd, capture_output=True, timeout=t)
    return r.stdout if bin else r.stdout.decode("utf-8","ignore")

def tap(x, y, w=1.2):
    adb("shell","input","tap",str(int(x)),str(int(y)))
    time.sleep(w)

def swipe(x1,y1,x2,y2,d=300):
    adb("shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(int(d)))

def move(s):
    swipe(JOY_C[0], JOY_C[1]+50, JOY_UP[0], JOY_UP[1], int(s*1000))

def ss():
    raw = adb("exec-out","screencap","-p", bin=True)
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR) if raw else None

def has_minimap(s=None):
    if s is None: s = ss()
    if s is None: return False
    roi = cv2.medianBlur(cv2.cvtColor(s[0:460, 0:500], cv2.COLOR_BGR2GRAY), 5)
    cs = cv2.HoughCircles(roi, cv2.HOUGH_GRADIENT, 1, 300, param1=100, param2=40, minRadius=130, maxRadius=220)
    return cs is not None

def ingame(s=None):
    c = has_minimap(s)
    if not c: return False
    if s is None: s = ss()
    if s is None: return False
    return cv2.cvtColor(s, cv2.COLOR_BGR2GRAY).mean() < 85

def lobby():
    print("[回大厅]")
    for _ in range(8):
        tap(80, 80, 1)
    time.sleep(2)

def do_match():
    # 多点几种可能的烽火地带位置
    for pos in [(1420,500), (1700,500), (1170,540)]:
        tap(pos[0], pos[1], 2)
    tap(975, 950, 3)
    tap(1000, 1053, 3)
    tap(1180, 770, 3)

def wait_enter(timeout=90):
    print("[等进场]")
    for i in range(timeout // 2):
        time.sleep(2)
        if ingame():
            print(f" OK 第{i*2}秒进场!")
            return True
        if i % 5 == 0:
            s = ss()
            if s is not None:
                print(f"  {i*2}s mean={cv2.cvtColor(s, cv2.COLOR_BGR2GRAY).mean():.0f}", end="\r")
    return False

def do_run():
    print("[跑刀] 降落...")
    for _ in range(30):
        move(1.0)
        time.sleep(0.2)
        if not ingame():
            print(" -> 退出战场")
            return
    print("[跑刀] 行进...")
    for step in range(100):
        move(1.5)
        time.sleep(0.3)
        tap(PICKUP[0], PICKUP[1], 0.5)
        if step % 10 == 0:
            swipe(1700, 500, 1700 + (120 if step % 20 == 0 else -120), 500, 350)
        if step % 20 == 0:
            print(f"  step {step}")
        if not ingame():
            print(" -> 退出战场")
            return

def do_result():
    print("[结算]")
    for _ in range(6):
        tap(1984, 989, 1.5)
        tap(300, 540, 1.5)

def main():
    print("="*40)
    print("Delta Force 跑刀 v7.2")
    print("="*40)
    
    rounds = 0
    lobby()
    
    while rounds < 50:
        print(f"\n=== 第{rounds+1}局 ===")
        do_match()
        if wait_enter():
            do_run()
            do_result()
            rounds += 1
            print(f"完成第{rounds}局!")
        else:
            print("超时重试")
            lobby()
    
    print(f"共{rounds}局")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[停止]")
