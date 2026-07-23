"""
三角洲行动 - 贴墙走出房间
逻辑：检测四周亮度→朝最亮的方向走
每走一步检测→亮就继续走这个方向，暗了/撞墙就转
"""
import subprocess, cv2, numpy as np, time, sys

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = '1aabaaeb'

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(x), str(y)], capture_output=True, timeout=5)

def swipe(x1,y1,x2,y2,ms=500):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(x1),str(y1),str(x2),str(y2),str(ms)], capture_output=True, timeout=5)

def screencap():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=10)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def analyze_scene(img):
    """分析画面，返回各方向亮度和纹理"""
    h,w = img.shape[:2]
    mid = w//2; half = h//2
    
    left_b = cv2.cvtColor(img[:,:mid], cv2.COLOR_BGR2GRAY).mean()
    right_b = cv2.cvtColor(img[:,mid:], cv2.COLOR_BGR2GRAY).mean()
    top_b = cv2.cvtColor(img[:half,:], cv2.COLOR_BGR2GRAY).mean()
    bot_b = cv2.cvtColor(img[half:,:], cv2.COLOR_BGR2GRAY).mean()
    
    # 正前方纹理（障碍物检测）
    front = img[int(h*0.4):int(h*0.8), int(w*0.25):int(w*0.75)]
    front_gray = cv2.cvtColor(front, cv2.COLOR_BGR2GRAY)
    texture = cv2.Laplacian(front_gray, cv2.CV_64F).var()
    
    # 正前方平均亮度
    front_b = front_gray.mean()
    
    return {
        "left": left_b, "right": right_b, "top": top_b, "bottom": bot_b,
        "front": front_b, "texture": texture
    }

def is_wall(scene, threshold=25):
    """纹理低于阈值=可能是墙"""
    return scene["texture"] < threshold

def brightest_direction(scene, exclude=None):
    """找最亮方向（排除指定方向）"""
    dirs = [("left", scene["left"]), ("right", scene["right"]), 
            ("top", scene["top"]), ("bottom", scene["bottom"])]
    if exclude:
        dirs = [(d,v) for d,v in dirs if d != exclude]
    dirs.sort(key=lambda x: x[1], reverse=True)
    return dirs[0]

def walk_one_step():
    """走一步（向前swipe）"""
    swipe(265, 793, 500, 400, 1000)

def turn(direction, amount=400):
    """朝指定方向转：left/right"""
    if direction == "left":
        swipe(1600, 540, 800, 540, amount)
    elif direction == "right":
        swipe(800, 540, 1600, 540, amount)

def wall_follow(steps=5):
    """贴墙走出：每步分析场景，朝亮的方向调整"""
    for i in range(steps):
        img = screencap()
        if img is None:
            break
        scene = analyze_scene(img)
        
        front_b = scene["front"]
        front_texture = scene["texture"]
        left_b = scene["left"]
        right_b = scene["right"]
        
        # 判断前方
        if front_texture < 25 and front_b < 100:
            # 面前是墙！保持左右交替转向
            turn_dir = "left" if i % 2 == 0 else "right"
            print(f"步{i}: 墙! 纹理={front_texture:.0f} 亮={front_b:.0f} 转向{turn_dir}")
            turn(turn_dir, 450)
            time.sleep(0.8)
            # 转完后走一步
            walk_one_step()
            time.sleep(1.5)
        else:
            # 没墙，往前走
            print(f"步{i}: 走! 纹理={front_texture:.0f} 亮={front_b:.0f} L={left_b:.0f} R={right_b:.0f}")
            walk_one_step()
            time.sleep(1.5)
    
    return screencap()

if __name__ == '__main__':
    print("=== 贴墙走 ===")
    final = wall_follow(int(sys.argv[1]) if len(sys.argv)>1 else 5)
    if final is not None:
        cv2.imwrite(r'C:\temp\delta_walk_final.png', final)
        print("完成")
