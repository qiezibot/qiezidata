# -*- coding: utf-8 -*-
"""
频率分离去斑 - 商业修图标准技法
低频层（颜色/大斑点）→ 模糊处理
高频层（皮肤纹理）→ 保留不动
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

for i in range(dets.shape[2]):
    conf = dets[0,0,i,2]
    if conf > 0.7:
        box = dets[0,0,i,3:7] * np.array([w, h, w, h])
        fx, fy, fx2, fy2 = box.astype("int")
        cx, cy = (fx+fx2)//2, (fy+fy2)//2
        fs = max(fx2-fx, fy2-fy)
        margin = int(fs * 0.3)
        x1 = max(0, cx - fs//2 - margin)
        y1 = max(0, cy - fs//2 - margin)
        x2 = min(w, cx + fs//2 + margin)
        y2 = min(h, cy + fs//2 + margin)
        
        face = img[y1:y2, x1:x2].copy()
        fh, fw = face.shape[:2]
        print("Face: ({},{})-({},{}), {}x{}".format(x1,y1,x2,y2,fw,fh))
        
        # === FREQUENCY SEPARATION ===
        # 1. Convert to float
        face_f = face.astype(np.float32) / 255.0
        
        # 2. Create low frequency (blurred version) - GaussianBlur
        # Bigger sigma = more spots removed but more smoothing
        low_freq = cv2.GaussianBlur(face_f, (0, 0), 15)  # Sigma 15 for big spot removal
        
        # 3. High frequency = original - low frequency (texture details)
        high_freq = face_f - low_freq
        
        # 4. Second pass - bilateral filter on low frequency to remove spots
        # while preserving edges
        low_denoised = cv2.bilateralFilter(low_freq, d=15, sigmaColor=50, sigmaSpace=15)
        
        # 5. Also try median filter on LAB channels for color spot removal
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, a_c, b_c = cv2.split(lab)
        
        # Median filter on L channel (lightness) to remove spots
        l_med = cv2.medianBlur(l, 9)
        
        # Simple edge-aware blur using bilateral on L
        l_bilateral = cv2.bilateralFilter(l_med, d=9, sigmaColor=30, sigmaSpace=9)
        
        lab_clean = cv2.merge([l_bilateral, a_c, b_c])
        color_corrected = cv2.cvtColor(lab_clean, cv2.COLOR_LAB2BGR)
        
        # Blend: use LAB correction for color consistency, 
        # then re-add high frequency for texture
        color_f = color_corrected.astype(np.float32) / 255.0
        reconstructed = color_f + high_freq * 0.8  # Slightly reduce high freq to smooth
        
        # Clip
        reconstructed = np.clip(reconstructed, 0, 1)
        
        # Blend with original face (80% retouched, 20% original)
        blended = reconstructed * 1.0
        
        # Save face back
        result[y1:y2, x1:x2] = (blended * 255).astype(np.uint8)
        
        print("Frequency separation done. Sigma=15")
        break

print("Time: {:.1f}s".format(time.time() - t0))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Saved!")
