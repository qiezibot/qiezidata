"""
去胡子 — 用OpenCV检测人脸区域 + 智能Inpaint
不依赖任何第三方人脸检测库
"""

import cv2
import numpy as np
import os
import sys
import uuid

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def detect_face_region(img):
    """用Haar Cascade检测人脸，几何定位胡须区域"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    
    # 加载人脸Cascade
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
    
    # 缩到800左右加速检测
    scale = min(800 / max(h, w), 1.0)
    small = cv2.resize(gray, (int(w*scale), int(h*scale))) if scale < 1 else gray
    
    faces = face_cascade.detectMultiScale(small, 1.15, 4, minSize=(80, 80))
    
    if len(faces) == 0:
        # 试试更宽松的参数
        faces = face_cascade.detectMultiScale(small, 1.08, 3, minSize=(60, 60))
        print(f"宽松检测: {len(faces)} 个人脸")
    
    if len(faces) == 0:
        print("❌ 未检测到人脸")
        return None, None
    
    # 取最大人脸
    face = max(faces, key=lambda r: r[2]*r[3])
    fx, fy, fw, fh = [int(v / scale) for v in face]
    
    print(f"人脸区域: ({fx},{fy}) {fw}x{fh}")
    
    # 胡须遮罩：几何定位
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # 嘴部区域估算（人脸下半部分 55%-85%）
    mouth_y1 = fy + int(fh * 0.55)
    mouth_y2 = fy + int(fh * 0.80)
    mouth_x1 = fx + int(fw * 0.20)
    mouth_x2 = fx + int(fw * 0.80)
    mouth_cx = (mouth_x1 + mouth_x2) // 2
    mouth_cy = (mouth_y1 + mouth_y2) // 2
    mouth_w = mouth_x2 - mouth_x1
    mouth_h = mouth_y2 - mouth_y1
    
    # 人中区域（嘴上到鼻子）
    nose_y = fy + int(fh * 0.35)
    upper_top = nose_y
    upper_bottom = mouth_y1
    if upper_bottom > upper_top:
        cv2.ellipse(mask,
                    ((mouth_x1 + mouth_x2)//2, (upper_top + upper_bottom)//2),
                    (mouth_w//2 + 5, (upper_bottom - upper_top)//2 + 5),
                    0, 0, 360, 255, -1)
    
    # 下巴区域（嘴下到脸底部）
    chin_top = mouth_y2
    chin_bottom = fy + fh
    if chin_bottom > chin_top:
        cv2.ellipse(mask,
                    ((mouth_x1 + mouth_x2)//2, (chin_top + chin_bottom)//2),
                    (mouth_w//2 + 10, (chin_bottom - chin_top)//2 + 10),
                    0, 0, 360, 255, -1)
    
    # 去掉嘴内部（保留唇形）
    cv2.ellipse(mask, (mouth_cx, mouth_cy), 
                (mouth_w//2 - 5, mouth_h//2 - 5), 0, 0, 360, 0, -1)
    
    # 羽化遮罩
    mask = cv2.GaussianBlur(mask, (31, 31), 10)
    
    print(f"胡须区域: 人中(upper)+嘴+下巴(lower)")
    print(f"嘴中心: ({mouth_cx}, {mouth_cy}), 嘴大小: {mouth_w}x{mouth_h}")
    
    return mask, (fx, fy, fw, fh, mouth_cx, mouth_cy, mouth_w, mouth_h)


def inpaint_beard(img, mask):
    """用inpaint去除胡须"""
    # 多轮修补
    r1 = cv2.inpaint(img, (mask * 0.6).astype(np.uint8), 3, cv2.INPAINT_TELEA)
    r2 = cv2.inpaint(r1, mask.astype(np.uint8), 2, cv2.INPAINT_NS)
    return r2


def process(input_path):
    print(f"处理: {os.path.basename(input_path)}")
    
    img = cv2.imread(input_path)
    if img is None:
        print("❌ 读取失败")
        return None
    
    h, w = img.shape[:2]
    print(f"尺寸: {w}x{h}")
    
    print("步骤1: 检测人脸/嘴部位置...")
    mask, regions = detect_face_region(img)
    
    if mask is None:
        return None
    
    print("步骤2: Inpaint去胡子...")
    result = inpaint_beard(img, mask)
    
    # 再和原图做皮肤区域混合
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    skin = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
    skin_f = cv2.GaussianBlur(skin.astype(np.float32), (31, 31), 15) / 255.0
    
    final = (img.astype(np.float32) * (1.0 - skin_f[:, :, np.newaxis] * 0.3) +
             result.astype(np.float32) * skin_f[:, :, np.newaxis] * 0.3)
    final = np.clip(final, 0, 255).astype(np.uint8)
    
    # 保存
    uid = uuid.uuid4().hex[:8]
    out_png = os.path.join(OUTPUT_DIR, f"beard_removed_{uid}.png")
    cv2.imwrite(out_png, final, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    
    # 预览
    scale = min(1.0, 2000 / max(w, h))
    preview = cv2.resize(final, (int(w*scale), int(h*scale))) if scale < 1 else final
    out_jpg = os.path.join(OUTPUT_DIR, f"beard_preview_{uid}.jpg")
    cv2.imwrite(out_jpg, preview, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    # 标记图
    if regions:
        debug = img.copy()
        fx, fy, fw, fh, mx, my, mw, mh = regions
        cv2.rectangle(debug, (fx, fy), (fx+fw, fy+fh), (0, 255, 0), 3)
        cv2.rectangle(debug, (mx, my), (mx+mw, my+mh), (0, 0, 255), 2)
        ds = min(1.0, 1200 / max(w, h))
        debug_out = os.path.join(OUTPUT_DIR, f"beard_debug_{uid}.jpg")
        debug_small = cv2.resize(debug, (int(w*ds), int(h*ds)))
        cv2.imwrite(debug_out, debug_small, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"标记图: {debug_out}")
    
    print(f"✅ 完成")
    print(f"预览: {out_jpg}")
    return out_jpg, out_png


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python beard_remover.py <图片路径>")
        sys.exit(1)
    
    result = process(sys.argv[1])
    if result:
        print(f"\n结果: {result[0]}")
