"""
三角洲行动 - 撤离导航v2 (带卡住检测)
"""
import subprocess
import time
import cv2
import numpy as np
import easyocr
import sys

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = '1aabaaeb'

reader = None  # lazy init


def ensure_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return reader


def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(x), str(y)], capture_output=True, timeout=5)


def swipe(x1, y1, x2, y2, dur=1000):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2), str(dur)], capture_output=True, timeout=5)


def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=10)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def image_similarity(img1, img2):
    """对比两张图的相似度（用灰度直方图比较）"""
    if img1 is None or img2 is None:
        return 0
    g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    # 缩放到64x64再比
    s1 = cv2.resize(g1, (64, 64))
    s2 = cv2.resize(g2, (64, 64))
    # 均方误差
    diff = cv2.absdiff(s1, s2)
    mse = np.mean(diff ** 2)
    # 相似度：MSE越小越相似，反向映射到0-100
    sim = max(0, 100 - mse / 10)
    return sim


def ocr(img):
    """OCR识别"""
    r = ensure_reader()
    results = r.readtext(img, paragraph=False)
    items = [(text.strip(), int((bbox[0][0]+bbox[2][0])/2), int((bbox[0][1]+bbox[2][1])/2), conf) 
             for bbox, text, conf in results if conf > 0.3]
    return items


def check_dead(items):
    """检查死亡/结算页面"""
    all_text = ' '.join([t for t, _, _, _ in items])
    if any(kw in all_text for kw in ['等待救援', '呼救', '淘汰详情', '立即撤退', '撤离失败', '致命一击']):
        return True
    return False


def check_hp(img):
    """检测血量"""
    bot = img[int(0.88 * img.shape[0]):, :]
    hsv = cv2.cvtColor(bot, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
    return cv2.countNonZero(red)


def check_stuck(img_before, img_after, last_coords):
    """
    检测是否卡住
    条件：画面相似度>85 且 亮度变化小
    """
    if img_before is None or img_after is None:
        return False
    
    sim = image_similarity(img_before, img_after)
    m_before = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY).mean()
    m_after = cv2.cvtColor(img_after, cv2.COLOR_BGR2GRAY).mean()
    
    return sim > 85 and abs(m_before - m_after) < 5


def auto_navigate():
    """
    主导航循环：走→检测卡住→换方向→找撤离点
    """
    print("=== 撤离导航v2（带卡住检测）===")
    
    last_img = None
    stuck_count = 0
    step = 0
    turn_direction = 1  # 1=右转, -1=左转
    
    # 摇杆方向预设
    directions = [
        (265, 400),   # 前（北）
        (600, 450),   # 前右（东北）
        (800, 500),   # 右（东）
        (600, 650),   # 后右（东南）
        (265, 900),   # 后（南）
        (100, 650),   # 后左（西南）
        (100, 500),   # 左（西）
        (100, 450),   # 前左（西北）
    ]
    current_dir_idx = 0
    
    while step < 200:
        # 截图
        img = screenshot()
        if img is None:
            print("截图失败")
            break
        
        items = ocr(img)
        all_text = ' '.join([t for t, _, _, _ in items])
        
        # 检测死亡
        if check_dead(items):
            print(f"!!! 步{step}死亡/结算 !!!")
            for t, cx, cy, c in items:
                print(f"  [{t}] ({cx},{cy})")
            break
        
        # 检测血量
        hp = check_hp(img)
        
        # 检查是否卡住
        if last_img is not None:
            is_stuck = check_stuck(last_img, img, items)
        else:
            is_stuck = False
        
        # 移动方向
        if is_stuck or stuck_count > 0:
            stuck_count += 1
            # 卡住了！换方向
            if stuck_count == 1:
                # 第一次卡住，右转90度再走
                swipe(1400, 500, 2000, 500, 400)
                time.sleep(0.5)
                current_dir_idx = (current_dir_idx + 1) % 8
                sx, sy = directions[current_dir_idx]
                print(f"  卡住！右转→方向{current_dir_idx} ({sx},{sy})")
            elif stuck_count == 2:
                # 还卡，再转
                current_dir_idx = (current_dir_idx + 2) % 8
                sx, sy = directions[current_dir_idx]
                print(f"  还卡！大转→方向{current_dir_idx} ({sx},{sy})")
            else:
                # 多方向尝试
                current_dir_idx = (current_dir_idx + 3) % 8
                sx, sy = directions[current_dir_idx]
                print(f"  继续卡→方向{current_dir_idx} ({sx},{sy})")
            
            if stuck_count >= 4:
                stuck_count = 0  # 重置
            
            # 卡住后走短一点看看
            swipe(265, 793, sx, sy, 1200)
            time.sleep(1.5)
            last_img = img
            step += 1
            continue
        
        # 正常行走
        sx, sy = directions[current_dir_idx]
        
        m = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()
        
        # 提取坐标
        coords = [t for t, cx, cy, c in items if t.replace(',', '').replace('.', '').isdigit() or any(d in t for d in ['北', '东', '南', '西'])]
        
        print(f"步{step}: m={m:.0f} hp={hp} 方向{current_dir_idx} 卡住计数={stuck_count}")
        if coords:
            print(f"  坐标/方向: {coords}")
        
        # 往前走
        swipe(265, 793, sx, sy, 1500)
        time.sleep(1.8)
        
        # 检测血量治疗
        if hp < 100:
            tap(1800, 600)
            time.sleep(0.3)
            tap(1800, 600)
            time.sleep(1)
        
        last_img = img
        step += 1
    
    print("=== 导航结束 ===")


if __name__ == "__main__":
    auto_navigate()
