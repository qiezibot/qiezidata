# -*- coding: utf-8 -*-
"""SMART mole detection - remove only REAL moles on facial skin"""
import cv2
import numpy as np
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]
print("Image size: {}x{}".format(w, h))

# Face detection
net = cv2.dnn.readNetFromCaffe(
    r"C:\u-claw\portable\data\.openclaw\workspace\deploy.prototxt",
    r"C:\u-claw\portable\data\.openclaw\workspace\res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300,300)), 1.0, (300,300), (104,177,123))
net.setInput(blob)
dets = net.forward()

result = img.copy()

for i in range(dets.shape[2]):
    conf = dets[0,0,i,2]
    if conf > 0.7:
        box = dets[0,0,i,3:7] * np.array([w,h,w,h])
        fx, fy, fx2, fy2 = box.astype("int")
        cx, cy = (fx+fx2)//2, (fy+fy2)//2
        fs = max(fx2-fx, fy2-fy)
        margin = int(fs * 0.4)
        x1 = max(0, cx - fs//2 - margin)
        y1 = max(0, cy - fs//2 - margin)
        x2 = min(w, cx + fs//2 + margin)
        y2 = min(h, cy + fs//2 + margin)
        
        face = img[y1:y2, x1:x2].copy()
        fh, fw = face.shape[:2]
        print("Face region: ({},{})-({},{}), size={}x{}".format(x1,y1,x2,y2,fw,fh))
        
        # === Step 1: Detect skin-colored regions ===
        # Convert to YCrCb for skin detection
        ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
        
        # Also use HSV
        hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
        skin_mask2 = cv2.inRange(hsv, np.array([0, 20, 70]), np.array([20, 150, 255]))
        
        # Combine skin masks
        skin = cv2.bitwise_or(skin_mask, skin_mask2)
        
        # Morphological cleanup
        kernel_m = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel_m)
        skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, kernel_m)
        
        # Eyes/Nose/Mouth mask - we should NOT touch these!
        # Use face landmarks approach: detect eyes approximate region
        eye_hair_upper = max(0, int(fh * 0.15))  # Upper 15% is hair/forehead
        eye_region_bottom = int(fh * 0.45)  # Bottom of eyes
        mouth_region_top = int(fh * 0.65)   # Top of mouth
        mouth_region_bottom = int(fh * 0.85)  # Bottom of mouth
        
        # Create protection mask: don't touch eyes area and mouth
        protect = np.zeros((fh, fw), dtype=np.uint8)
        # Eyes area (center region ~20-45% height)
        eye_band = int(fh * 0.20)
        protect[eye_band:eye_region_bottom, :] = 255
        
        # === Step 2: Find dark spots ONLY on skin (not hair, not clothes) ===
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(15,15))
        l_eq = clahe.apply(l)
        
        # Blackhat for dark spots
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))
        bh = cv2.morphologyEx(l_eq, cv2.MORPH_BLACKHAT, kernel)
        
        # Threshold - moderate
        _, spots_raw = cv2.threshold(bh, 20, 255, cv2.THRESH_BINARY)
        
        # Keep only spots on SKIN (not on hair/eyes/clothes)
        spots_on_skin = cv2.bitwise_and(spots_raw, spots_raw, mask=skin)
        
        # Also remove from protected areas (eyes area)
        spots_on_skin = cv2.bitwise_and(spots_on_skin, spots_on_skin, mask=cv2.bitwise_not(protect))
        
        # === Step 3: Filter by size and circularity ===
        n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(spots_on_skin, 8)
        
        # Only keep the MOST significant spots (large and circular)
        candidates = []
        for j in range(1, n_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            sx, sy, sw, sh = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
            
            if area < 30 or area > 400:
                continue
            
            # Circularity
            cnt_pts = np.array([[sx, sy], [sx+sw, sy], [sx+sw, sy+sh], [sx, sy+sh]], dtype=np.float32)
            perimeter = cv2.arcLength(cnt_pts, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            aspect = max(sw, sh) / max(1, min(sw, sh))
            
            # Moles: circular, not too elongated
            if circularity > 0.25 and aspect < 2.5:
                candidates.append((j, area, circularity, sx, sy, sw, sh))
        
        # Sort by area (largest first) and take top 10
        candidates.sort(key=lambda c: c[1], reverse=True)
        candidates = candidates[:15]  # Max 15 spots
        
        if not candidates:
            print("No cosmetic spots found!")
        else:
            final_mask = np.zeros_like(l_eq)
            for c_idx, (j, area, circ, sx, sy, sw, sh) in enumerate(candidates):
                final_mask[labels == j] = 255
                print("  Spot #{}: abs=({},{}), area={}, circ={:.2f}".format(
                    c_idx+1, sx+x1, sy+y1, area, circ))
            
            # Dilate and blur for smooth inpaint
            kernel_d = np.ones((11,11), np.uint8)
            mask_d = cv2.dilate(final_mask, kernel_d, iterations=1)
            mask_f = cv2.GaussianBlur(mask_d.astype(np.float32), (7,7), 0)
            mask_f = np.clip(mask_f, 0, 255).astype(np.uint8)
            
            # Inpaint
            inpainted = cv2.inpaint(face, mask_f, 3, cv2.INPAINT_TELEA)
            
            # Soft blend at edges
            m_float = mask_f.astype(np.float32) / 255.0
            m_blur = cv2.GaussianBlur(m_float, (21,21), 5)
            m_3ch = cv2.merge([m_blur]*3)
            
            blended = inpainted.astype(np.float32) * m_3ch + face.astype(np.float32) * (1 - m_3ch)
            result[y1:y2, x1:x2] = blended.astype(np.uint8)
            print("Done: {} spots treated".format(len(candidates)))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Saved!")
