# -*- coding: utf-8 -*-
"""
Delta Force 画面识别模块 v1
完全基于特征向量 + OCR，不依赖坐标
"""
import cv2, numpy as np, subprocess, os, time
import warnings; warnings.filterwarnings('ignore')

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = os.environ.get('PHONE_ID', '1aabaaeb')

# ---------- 截图 ----------
def screenshot():
    r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=15)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > img.shape[1]:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def tap(x, y):
    subprocess.run([ADB, '-s', PHONE, 'shell', 'input', 'tap', str(int(x)), str(int(y))], capture_output=True, timeout=5)

# ---------- OCR ----------
_reader = None
def ocr(img):
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    results = _reader.readtext(img, paragraph=False)
    items = []
    for bbox, text, conf in results:
        if conf < 0.3: continue
        tl,tr,br,bl = bbox
        cx,cy = int((tl[0]+br[0])/2), int((tl[1]+br[1])/2)
        items.append((text.strip(), conf, (cx,cy)))
    return items

# ========== 特征提取 ==========
def extract_features(img):
    """返回所有画面特征，用于页面分类"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = gray.shape[:2]
    
    feat = {
        'mean': float(gray.mean()),
        'std': float(gray.std()),
        'orientation': 'landscape' if w > h else 'portrait',
    }
    
    # 分区
    for name, (y1,y2,x1,x2) in {
        'top':     (0,     h//4, 0,     w),
        'bottom':  (3*h//4, h,   0,     w),
        'center':  (h//3, 2*h//3, w//3, 2*w//3),
        'right':   (0,     h,   3*w//4, w),
        'left':    (0,     h,   0,     w//4),
        'tlcorner':(20,  220, 20,   220),
    }.items():
        roi = gray[y1:y2, x1:x2]
        if roi.size > 0:
            feat[f'{name}_mean'] = float(roi.mean())
            feat[f'{name}_std'] = float(roi.std())
    
    # 颜色
    bottom = hsv[int(0.85*h):h, :] if w > h else hsv[int(0.85*h):h, :]
    full_red = cv2.inRange(hsv, (0,50,50), (10,255,255)) | cv2.inRange(hsv, (160,50,50), (180,255,255))
    full_blue = cv2.inRange(hsv, (80,50,50), (130,255,255))
    bot_red = cv2.inRange(bottom, (0,50,50), (10,255,255)) | cv2.inRange(bottom, (160,50,50), (180,255,255))
    bot_blue = cv2.inRange(bottom, (80,50,50), (130,255,255))
    
    feat['red_total'] = int(cv2.countNonZero(full_red))
    feat['blue_total'] = int(cv2.countNonZero(full_blue))
    feat['bottom_red'] = int(cv2.countNonZero(bot_red))
    feat['bottom_blue'] = int(cv2.countNonZero(bot_blue))
    
    # 小地图圆检测
    mm = gray[20:220, 20:220] if w > h else gray[20:220, 20:220]
    feat['mm_circle'] = False
    if mm.mean() > 30 and mm.std() > 20:
        bl = cv2.medianBlur(mm, 5)
        circles = cv2.HoughCircles(bl, cv2.HOUGH_GRADIENT, 1, 100, param1=80, param2=30, minRadius=60, maxRadius=110)
        feat['mm_circle'] = circles is not None
    
    return feat

# ========== 页面判断（只靠特征+OCR）==========
# 游戏内关键词
GAME_UI_KWS = ['距离', '烟幕', '弹药', '治疗', '自我治疗', '急救', '点击地图',
               '3/3', '2/2', '米', '医疗箱', '开镜']
# 大厅关键词
LOBBY_KWS = ['藏品', '市场', '商城', '通行证', '活动', '社交', '邮件', '设置',
             '出发', '仓库', '部门', '交易', '特战', '特勤', '改枪', '全面战场',
             '开始行动', '烽火']
# 结算关键词
RESULT_KWS = ['大吉大利', '胜利', '失败', '本局', '排名', '撤离', '战绩',
              '返回大厅', '继续']
# 匹配关键词
MATCH_KWS = ['搜索中', '等待']

def detect_page(img, items=None):
    """可靠的多维度页面判断"""
    feat = extract_features(img)
    
    if items is None:
        items = ocr(img)
    
    all_text = ' '.join([t for t,_,_ in items])
    
    # 1. OCR关键词匹配（最可靠）
    # 游戏内
    for kw in GAME_UI_KWS:
        if kw in all_text:
            return 'ingame', feat
    
    # 结算
    for kw in RESULT_KWS:
        if kw in all_text:
            return 'result', feat
    
    # 大厅
    for kw in LOBBY_KWS:
        if kw in all_text:
            return 'lobby', feat
    
    # 匹配
    for kw in MATCH_KWS:
        if kw in all_text:
            return 'match', feat
    
    # 2. 无OCR或OCR不确定 -> 图像特征
    m = feat['mean']
    b_r = feat['bottom_red']
    b_b = feat['bottom_blue']
    
    # 游戏内: 底部有大量红蓝色（血条+护甲）
    if b_r > 500 and b_b > 300 and m > 30:
        return 'ingame', feat
    
    # 结算: 很亮且底部没有红蓝色
    if m > 100 and b_r < 200 and b_b < 200:
        return 'result', feat
    
    # 大厅: 中等亮度，底部有UI但没红蓝色
    if 40 < m < 100 and b_r < 400 and b_b < 200:
        return 'lobby', feat
    
    # 3. 特征判断不了 -> 黑屏或未知
    if m < 40:
        return 'black', feat
    
    return 'unknown', feat


# ========== 主函数（采集+调试） ==========
if __name__ == '__main__':
    print("=== 画面识别模块 诊断 ===")
    img = screenshot()
    if img is None:
        print("截图失败")
        exit()
    
    feat = extract_features(img)
    print(f"尺寸: {img.shape[1]}x{img.shape[0]} ({feat['orientation']})")
    print(f"亮度: mean={feat['mean']:.1f} std={feat['std']:.1f}")
    print(f"颜色: 红={feat['red_total']} 蓝={feat['blue_total']}")
    print(f"底部: 红={feat['bottom_red']} 蓝={feat['bottom_blue']}")
    print(f"小地图圆: {feat['mm_circle']}")
    
    items = ocr(img)
    page, feat = detect_page(img, items)
    print(f"\n=== 判定: {page} ===")
    
    # 列出OCR结果
    print(f"OCR ({len(items)}项):")
    for text, conf, pos in items[:20]:
        print(f"  [{text}] ({pos[0]},{pos[1]})")
