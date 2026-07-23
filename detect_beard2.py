"""用dlib检测人脸关键点 → 定位胡须区域"""
import os, sys, uuid, cv2, numpy as np

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

img_path = r'C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\ebc873ea-5136-42ce-9155-e62e21d2d988.png'

# 试试用facexlib（之前装过）
print("用facexlib检测人脸关键点...")
try:
    from facexlib.detection import init_detection_model
    from facexlib.alignment import init_alignment_model
    
    det = init_detection_model('retinaface_resnet50', half=False)
    
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    
    # 检测人脸
    scale = 1200 / max(w, h)
    small = cv2.resize(img, (int(w*scale), int(h*scale)))
    img_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    
    import torch
    with torch.no_grad():
        bboxes, scores = det.detect_faces(img_rgb, img_rgb.shape[0])
    if bboxes is not None and len(bboxes) > 0:
        print(f"检测到 {len(bboxes)} 个人脸")
        bbox = bboxes[0]
        landmarks = ali.get_landmarks(small, bbox)
        print(f"Landmarks shape: {landmarks.shape}")
        
        # landmark是68个点，映射回原图
        if len(landmarks.shape) == 3:
            landmarks = landmarks[0]
        l = (landmarks * (1/scale)).astype(np.int32)
        
        # 68点模型关键点索引：
        # jaw: 0-16,  eyebrow: 17-26,  nose: 27-35, 
        # eye: 36-47,  mouth: 48-67
        mouth_pts = l[48:68]
        jaw_pts = l[0:17]
        
        # 嘴中心
        mouth_center = mouth_pts.mean(axis=0).astype(np.int32)
        # 下巴最下点
        chin_bottom = jaw_pts.max(axis=0)
        # 嘴宽度
        mouth_w = int(mouth_pts[:, 0].max() - mouth_pts[:, 0].min())
        
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # 胡须区域 = 嘴下部到下巴
        # 用椭圆覆盖
        cx, cy = mouth_center
        ellipse_w = int(mouth_w * 1.8)
        ellipse_h = int((chin_bottom[1] - cy) * 1.5 + mouth_w * 0.5)
        
        cv2.ellipse(mask, (cx, cy + int(ellipse_h*0.2)), 
                    (ellipse_w, ellipse_h), 0, 0, 360, 255, -1)
        
        # 去掉嘴内部（保留唇形）
        cv2.fillPoly(mask, [mouth_pts], 0)
        
        # 羽化
        mask = cv2.GaussianBlur(mask, (31, 31), 10)
        
        # 可视化
        overlay = img.copy()
        green = np.zeros_like(overlay)
        green[:, :] = [0, 200, 0]
        overlay = cv2.addWeighted(overlay, 0.7, green, 0.3, 0)
        overlay = cv2.bitwise_and(overlay, overlay, mask=mask)
        overlay = cv2.add(img, overlay)
        
        ds = min(1.0, 1200 / max(w, h))
        debug_out = os.path.join(OUTPUT_DIR, f"beard_mask_{uuid.uuid4().hex[:8]}.jpg")
        cv2.imwrite(cv2.resize(overlay, (int(w*ds), int(h*ds))), debug_out, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        mask_path = os.path.join(OUTPUT_DIR, f"beard_mask_{uuid.uuid4().hex[:8]}.png")
        cv2.imwrite(mask_path, mask)
        
        print(f"✅ 胡须区域检测完成")
        print(f"标记图: {debug_out}")
        print(f"遮罩: {mask_path}")
        
    else:
        print("❌ 未检测到人脸")
        
except Exception as e:
    print(f"{type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
