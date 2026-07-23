"""Targeted mole removal v2 - stricter detection, only real moles"""
import cv2
import numpy as np

img = cv2.imread("C:/ComfyUI/output/wedding_codeformer_test__00001_.png")
h, w = img.shape[:2]

# Face detection
net = cv2.dnn.readNetFromCaffe(
    "C:/u-claw/portable/data/.openclaw/workspace/deploy.prototxt",
    "C:/u-claw/portable/data/.openclaw/workspace/res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104, 177, 123))
net.setInput(blob)
detections = net.forward()

result = img.copy()

for i in range(detections.shape[2]):
    confidence = detections[0, 0, i, 2]
    if confidence > 0.7:
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (fx, fy, fx2, fy2) = box.astype("int")
        cx, cy = (fx + fx2) // 2, (fy + fy2) // 2
        face_size = max(fx2 - fx, fy2 - fy)
        margin = int(face_size * 0.4)
        x1 = max(0, cx - face_size // 2 - margin)
        y1 = max(0, cy - face_size // 2 - margin // 2)
        x2 = min(w, cx + face_size // 2 + margin)
        y2 = min(h, cy + face_size // 2 + margin // 2)
        
        face = img[y1:y2, x1:x2].copy()
        print(f"Face: ({x1},{y1})-({x2},{y2})")
        
        # Convert to LAB for better color analysis
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Normalize
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l_eq = clahe.apply(l)
        
        # Key: moles are DARK spots that are also ROUND and ISOLATED
        # Use top-hat transform to find dark spots
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
        tophat = cv2.morphologyEx(l_eq, cv2.MORPH_BLACKHAT, kernel)
        
        # Threshold
        _, spots = cv2.threshold(tophat, 25, 255, cv2.THRESH_BINARY)
        
        # Filter by circularity and size
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(spots, 8)
        
        mask = np.zeros_like(l_eq)
        
        for j in range(1, num_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            sx, sy, sw, sh = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
            
            # Size range for moles at this resolution (4284x5712)
            # A real mole would be roughly 20-200 pixels
            if area < 20 or area > 400:
                continue
            
            # Circularity check
            perimeter = cv2.arcLength(
                np.array([[sx, sy], [sx+sw, sy], [sx+sw, sy+sh], [sx, sy+sh]]), True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            # Moles are roughly circular (circularity > 0.5)
            if circularity < 0.3:
                continue
            
            # Also check aspect ratio
            aspect = max(sw, sh) / max(1, min(sw, sh))
            if aspect > 2.5:
                continue
            
            # Check if it's actually dark (not hair, not texture)
            roi_l = l_eq[sy:sy+sh, sx:sx+sw]
            mean_l = np.mean(roi_l)
            
            # Moles are significantly darker than local area
            local_region = l_eq[max(0,sy-20):min(l_eq.shape[0],sy+sh+20), max(0,sx-20):min(l_eq.shape[1],sx+sw+20)]
            local_mean = np.mean(local_region)
            
            if mean_l > local_mean - 10:  # Not dark enough relative to surroundings
                continue
            
            mask[labels == j] = 255
            print(f"  Mole: pos=({sx+x1},{sy+y1}), size={sw}x{sh}, area={area}, circ={circularity:.2f}")
        
        if cv2.countNonZero(mask) > 0:
            # Dilate slightly
            kernel_d = np.ones((7,7), np.uint8)
            mask_d = cv2.dilate(mask, kernel_d, iterations=1)
            mask_f = cv2.GaussianBlur(mask_d.astype(np.float32), (7,7), 0)
            mask_f = np.clip(mask_f, 0, 255).astype(np.uint8)
            
            # Inpaint
            inpainted = cv2.inpaint(face, mask_f, 3, cv2.INPAINT_TELEA)
            
            # Soft blend
            m_float = mask_f.astype(np.float32) / 255.0
            m_3ch = cv2.merge([m_float] * 3)
            
            blended = inpainted.astype(np.float32) * m_3ch + face.astype(np.float32) * (1 - m_3ch)
            result[y1:y2, x1:x2] = blended.astype(np.uint8)
            print(f"Removed {cv2.countNonZero(mask)} spot pixels")
        else:
            print("No moles detected with strict criteria")
            # Fallback: just find the darkest significant spots
            _, spots2 = cv2.threshold(tophat, 35, 255, cv2.THRESH_BINARY)
            num2, labels2, stats2, _ = cv2.connectedComponentsWithStats(spots2, 8)
            mask2 = np.zeros_like(l_eq)
            for j in range(1, num2):
                area = stats2[j, cv2.CC_STAT_AREA]
                if 30 < area < 300:
                    sx, sy = stats2[j, cv2.CC_STAT_LEFT], stats2[j, cv2.CC_STAT_TOP]
                    sw, sh = stats2[j, cv2.CC_STAT_WIDTH], stats2[j, cv2.CC_STAT_HEIGHT]
                    aspect = max(sw, sh) / max(1, min(sw, sh))
                    if aspect < 2:
                        mask2[labels2 == j] = 255
                        print(f"  Fallback spot: ({sx+x1},{sy+y1}) area={area}")
            if cv2.countNonZero(mask2) > 0:
                md = cv2.dilate(mask2, np.ones((7,7),np.uint8), iterations=1)
                mf = cv2.GaussianBlur(md.astype(np.float32), (7,7), 0)
                mf = np.clip(mf, 0, 255).astype(np.uint8)
                inp = cv2.inpaint(face, mf, 3, cv2.INPAINT_TELEA)
                mf3 = cv2.merge([mf.astype(np.float32)/255.0]*3)
                result[y1:y2, x1:x2] = (inp.astype(np.float32)*mf3 + face.astype(np.float32)*(1-mf3)).astype(np.uint8)

cv2.imwrite("C:/ComfyUI/output/wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Done!")
