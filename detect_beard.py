"""测试ModelScope卸妆/美颜模型 — 去胡子"""
import os, sys, uuid, cv2, numpy as np

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

img_path = r'C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\ebc873ea-5136-42ce-9155-e62e21d2d988.png'

# 先试试用dlib/insightface检测人脸关键点，定位胡须区域
print("检测人脸关键点...")
try:
    import insightface
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    # 缩到合适大小检测
    scale = 1200 / max(w, h)
    small = cv2.resize(img, (int(w*scale), int(h*scale)))
    
    faces = app.get(small)
    if faces:
        face = faces[0]
        print(f"检测到人脸，landmarks: {face.landmark.shape}")
        # 关键点索引: 下巴(8), 嘴(48-67), 鼻子(27-35)
        landmarks = face.landmark * (1/scale)  # 映射回原图坐标
        
        # 定位胡须区域：人中+下巴+嘴周围
        l = landmarks.astype(np.int32)
        
        # 嘴的关键点
        mouth_pts = l[48:68]
        # 下巴关键点  
        chin_pts = l[0:17]
        
        # 创建遮罩：嘴以下到下巴的区域
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # 嘴区域
        cv2.fillPoly(mask, [mouth_pts], 255)
        
        # 嘴到下巴的区域
        upper_lip = mouth_pts.min(axis=0)[1]
        lower_chin = chin_pts.max(axis=0)[1]
        
        # 扩展遮罩到嘴上部（人中）+ 嘴下部到下巴
        mouth_center_y = mouth_pts.mean(axis=0)[1]
        mouth_center_x = mouth_pts.mean(axis=0)[0]
        
        # 椭圆遮罩：人中+下巴区域
        # 宽度取嘴宽度的1.5倍
        mouth_w = mouth_pts.max(axis=0)[0] - mouth_pts.min(axis=0)[0]
        ellipse_w = int(mouth_w * 1.8)
        ellipse_h = int((lower_chin - mouth_center_y) * 1.6)
        
        cv2.ellipse(mask, (mouth_center_x, mouth_center_y + int(ellipse_h*0.15)), 
                    (ellipse_w, ellipse_h), 0, 0, 360, 255, -1)
        
        # 羽化遮罩
        mask = cv2.GaussianBlur(mask, (31, 31), 10)
        
        # 保存遮罩可视化
        debug_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        overlay = img.copy()
        overlay[mask > 0] = overlay[mask > 0] * 0.6 + np.array([0, 255, 0], dtype=np.uint8) * 0.4
        
        ds = min(1.0, 1200 / max(w, h))
        debug_out = os.path.join(OUTPUT_DIR, f"beard_mask_{uuid.uuid4().hex[:8]}.jpg")
        cv2.imwrite(cv2.resize(overlay, (int(w*ds), int(h*ds))), debug_out, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        print(f"✅ 胡须区域检测完成")
        print(f"标记图: {debug_out}")
        print(f"遮罩中心: ({mouth_center_x}, {mouth_center_y}), 大小: {ellipse_w}x{ellipse_h}")
        
        # 输出mask路径供后续使用
        mask_path = os.path.join(OUTPUT_DIR, f"beard_mask_{uuid.uuid4().hex[:8]}.png")
        cv2.imwrite(mask_path, mask)
        print(f"遮罩: {mask_path}")
        
    else:
        print("❌ 未检测到人脸")
except Exception as e:
    print(f"❌ 人脸检测失败: {e}")
    import traceback
    traceback.print_exc()
