# -*- coding: utf-8 -*-
"""
频率分离去整脸色斑
- 只修面部皮肤区域
- 不修眼睛/眉毛/嘴巴/头发
- 保留皮肤纹理（不磨皮）
"""
import cv2
import numpy as np
import time

t0 = time.time()
img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]
print("Image: {}x{}".format(w, h))

result = img.copy()

# Face detection
net = cv2.dnn.readNetFromCaffe(
    r"C:\u-claw\portable\data\.openclaw\workspace\deploy.prototxt",
    r"C:\u-claw\portable\data\.openclaw\workspace\res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300,300)), 1.0, (300,300), (104,177,123))
net.setInput(blob)
dets = net.forward()

# Get face boxes
face_boxes = []
for i in range(dets.shape[2]):
    conf = dets[0,0,i,2]
    if conf > 0.7:
        box = dets[0,0,i,3:7] * np.array([w, h, w, h])
        fx, fy, fx2, fy2 = box.astype("int")
        cx, cy = (fx+fx2)//2, (fy+fy2)//2
        fs = max(fx2-fx, fy2-fy)
        margin = int(fs * 0.1)
        x1 = max(0, fx - margin)
        y1 = max(0, fy - margin)
        x2 = min(w, fx2 + margin)
        y2 = min(h, fy2 + margin)
        face_boxes.append((x1, y1, x2, y2))
        print("Face {}: ({},{})-({},{})".format(i, x1, y1, x2, y2))

for (x1, y1, x2, y2) in face_boxes:
    face = img[y1:y2, x1:x2].copy()
    fh, fw = face.shape[:2]
    print("Face size: {}x{}".format(fw, fh))
    
    # Create skin mask using YCrCb
    ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    
    # Skin color range in YCrCb (standard)
    skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
    
    # Also use HSV for additional skin detection
    hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
    hsv_lower = np.array([0, 20, 70])
    hsv_upper = np.array([20, 150, 255])
    skin_mask2 = cv2.inRange(hsv, hsv_lower, hsv_upper)
    
    # Combine skin masks
    skin = cv2.bitwise_and(skin_mask, skin_mask2)
    
    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
    skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, kernel)
    
    # Dilate skin mask slightly to cover edges
    skin = cv2.dilate(skin, kernel, iterations=1)
    
    skin_area = np.sum(skin > 0)
    total_area = fh * fw
    print("Skin area: {:.1f}% of face".format(100 * skin_area / total_area))
    
    # === FREQUENCY SEPARATION ===
    face_f = face.astype(np.float32) / 255.0
    
    # Low frequency - blur to remove spots
    low_freq = cv2.GaussianBlur(face_f, (0, 0), 15)
    
    # High frequency = original - low frequency
    high_freq = face_f - low_freq
    
    # LAB-based spot removal
    lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
    l, a_c, b_c = cv2.split(lab)
    
    # Bilateral filter on L to remove spots while keeping edges
    l_filter = cv2.medianBlur(l, 11)
    lab_clean = cv2.merge([l_filter, a_c, b_c])
    color_clean = cv2.cvtColor(lab_clean, cv2.COLOR_LAB2BGR).astype(np.float32) / 255.0
    
    # Add back high frequency (skin texture)
    reconstructed = color_clean + high_freq * 0.7
    reconstructed = np.clip(reconstructed, 0, 1)
    
    # Convert to 8-bit
    repaired = (reconstructed * 255).astype(np.uint8)
    
    # === BLEND using skin mask ===
    # Feather skin mask edges
    skin_float = skin.astype(np.float32) / 255.0
    skin_feather = cv2.GaussianBlur(skin_float, (15, 15), 5)
    skin_3ch = cv2.merge([skin_feather] * 3)
    
    # Blend: repaired on skin, original everywhere else
    blended = (repaired.astype(np.float32) * skin_3ch + 
               face.astype(np.float32) * (1 - skin_3ch)).astype(np.uint8)
    
    result[y1:y2, x1:x2] = blended
    print("Blended. Kept eyes/mouth/hair as original.")

elapsed = time.time() - t0
print("Time: {:.1f}s".format(elapsed))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Saved!")
