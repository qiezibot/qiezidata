# -*- coding: utf-8 -*-
import cv2
import numpy as np

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

# Face detection
net = cv2.dnn.readNetFromCaffe(
    r"C:\u-claw\portable\data\.openclaw\workspace\deploy.prototxt",
    r"C:\u-claw\portable\data\.openclaw\workspace\res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300,300)), 1.0, (300,300), (104,177,123))
net.setInput(blob)
dets = net.forward()

# Draw markers on a copy
marked = img.copy()

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
        
        face = img[y1:y2, x1:x2]
        fh, fw = face.shape[:2]
        
        # LAB analysis
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, _, _ = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(15,15))
        l_eq = clahe.apply(l)
        
        # Multiple threshold levels to find spots
        spots_mask = np.zeros((fh, fw), dtype=np.uint8)
        
        for th in [12, 15, 18, 20, 25]:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
            bh = cv2.morphologyEx(l_eq, cv2.MORPH_BLACKHAT, kernel)
            _, binary = cv2.threshold(bh, th, 255, cv2.THRESH_BINARY)
            
            n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
            for j in range(1, n_labels):
                area = stats[j, cv2.CC_STAT_AREA]
                if area < 15 or area > 500:
                    continue
                sx, sy, sw, sh = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
                asp = max(sw, sh) / max(1, min(sw, sh))
                if asp < 3:
                    spots_mask[labels == j] = 255
        
        # Find contours of spots
        contours, _ = cv2.findContours(spots_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"Total spots found on face: {len(contours)}")
        
        # Draw on the face region of the marked image
        for idx, cnt in enumerate(contours):
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cx_s = int(M["m10"] / M["m00"]) + x1
                cy_s = int(M["m01"] / M["m00"]) + y1
                area = cv2.contourArea(cnt)
                
                # Draw circle around spot
                radius = max(3, int(np.sqrt(area / np.pi)))
                cv2.circle(marked, (cx_s, cy_s), radius, (0, 0, 255), 2)  # Red circle
                cv2.circle(marked, (cx_s, cy_s), 1, (255, 255, 255), 2)   # White center dot
                
                if idx < 20:  # Print first 20
                    print(f"  Spot {idx+1}: ({cx_s}, {cy_s}) area={area:.0f}")

# Save marked version
marked_small = cv2.resize(marked, (0,0), fx=0.3, fy=0.3)
cv2.imwrite(r"C:\temp\tts\spotted_result.jpg", marked_small, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Saved marked image")
