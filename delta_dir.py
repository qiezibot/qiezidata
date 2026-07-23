"""
三角洲行动 - 方向辨别工具
通过多次截图对比顶部坐标变化，判断实际走路方向
用于校准摇杆滑动方向与游戏内移动方向的关系
"""
import subprocess
import time
import json
import sys

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = '1aabaaeb'


def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=10)
    return r.stdout


def get_top_text(img_bytes):
    """用最简方法快速读取顶部坐标文字"""
    import cv2, numpy as np
    
    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    if img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    
    # 顶部区域
    top = img[28:72, 770:1300]
    
    # 增强对比度
    gray = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 用简单模板匹配找数字 - 实际用EasyOCR
    import easyocr
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    results = reader.readtext(enhanced, paragraph=False)
    
    # 纯数字串
    numbers = []
    for bbox, text, conf in results:
        if conf > 0.3:
            # 过滤纯数字或带逗号的坐标值
            cleaned = ''.join(c for c in text if c.isdigit() or c == ',' or c == '.')
            if cleaned:
                cx = int((bbox[0][0] + bbox[2][0]) / 2)
                cy = int((bbox[0][1] + bbox[2][1]) / 2)
                numbers.append((cleaned, cx, cy, conf))
    
    return numbers


def get_full_ocr(img_bytes):
    """完整画面OCR"""
    import cv2, numpy as np, easyocr
    
    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return []
    if img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    results = reader.readtext(img, paragraph=False)
    
    items = []
    for bbox, text, conf in results:
        if conf > 0.3:
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            items.append((text.strip(), cx, cy, conf))
    return items


def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(x), str(y)], capture_output=True, timeout=5)


def swipe(x1, y1, x2, y2, dur=800):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2), str(dur)], capture_output=True, timeout=5)


def calibrate_direction(steps=5, duration=1500):
    """
    朝一个方向滑动摇杆，每次截图记录坐标变化
    steps: 走几步
    duration: 每次滑动毫秒
    """
    print(f"=== 摇杆方向校准 === 走{steps}步，每步{duration}ms")
    print("摇杆中心: (265, 793)\n")
    
    results = {}
    
    # 方向测试列表
    directions = [
        ("前上推", 265, 400),
        ("后下拉", 265, 900),
        ("左推", 100, 793),
        ("右推", 600, 793),
        ("左上推", 150, 450),
        ("右上推", 500, 450),
    ]
    
    for name, tx, ty in directions:
        print(f"\n--- {name} ({265},{793})→({tx},{ty}) ---")
        
        # 截取基准坐标
        tap(1171, 540)  # 先关掉可能打开的地图
        time.sleep(0.5)
        base_img = screenshot()
        
        # 往前滑动
        swipe(265, 793, tx, ty, duration)
        time.sleep(duration/1000 + 0.5)
        
        # 截图
        moved_img = screenshot()
        
        # OCR提取坐标
        base_texts = get_top_text(base_img)
        moved_texts = get_top_text(moved_img)
        
        print(f"  滑动前: {base_texts}")
        print(f"  滑动后: {moved_texts}")
        
        # 保存图像
        import cv2, numpy as np
        for name2, data in [("before", base_img), ("after", moved_img)]:
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if img is not None and img.shape[0] > img.shape[1]:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(f'C:\\temp\\delta_cal_{name}_{name2}.png', img)
    
    return results


def live_navigate():
    """实时导航：每步截图→读坐标→找撤离点方向→走"""
    print("=== 实时导航模式 ===")
    print("每走一步截图读坐标，记录变化\n")
    
    positions = []
    
    for step in range(10):
        # 截图
        img_bytes = screenshot()
        items = get_full_ocr(img_bytes)
        
        # 提取坐标数字 (从顶部)
        top_items = get_top_text(img_bytes)
        
        # 提取所有文字
        all_texts = [t for t, _, _, _ in items]
        
        print(f"步{step}:")
        for t, cx, cy, c in items[:8]:
            print(f"  [{t}] ({cx},{cy})")
        
        if top_items:
            nums = [n[0] for n in top_items]
            print(f"  坐标数字: {nums}")
        
        # 往前走
        swipe(265, 793, 265, 400, 1500)
        time.sleep(1.8)
        
        # 检查死亡
        all_text = ' '.join(all_texts)
        if '等待救援' in all_text or '呼救' in all_text or '淘汰' in all_text:
            print("!!! 死亡了 !!!")
            break
    
    return positions


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "nav":
        live_navigate()
    elif len(sys.argv) > 1 and sys.argv[1] == "cal":
        calibrate_direction()
    else:
        # 默认：只做一次截图+坐标读
        print("单次坐标读取:")
        items = get_full_ocr(screenshot())
        for t, cx, cy, c in items:
            print(f"  [{t}] ({cx},{cy}) [{c:.2f}]")
