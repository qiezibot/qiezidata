"""Post-process CodeFormer output: detect and remove remaining spots on face"""
import cv2
import numpy as np

img = cv2.imread("C:/ComfyUI/output/wedding_codeformer_test__00001_.png")
h, w = img.shape[:2]

# Use DNN face detection
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
        (x, y, x2, y2) = box.astype("int")
        # Expand face area significantly to catch all spots
        mw = int((x2 - x) * 0.5)
        mh = int((y2 - y) * 0.4)
        x = max(0, x - mw)
        y = max(0, y - mh)
        x2 = min(w, x2 + mw)
        y2 = min(h, y2 + mh)
        
        face = img[y:y2, x:x2].copy()
        fh, fw = face.shape[:2]
        
        # Detect dark spots via color analysis
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE on L channel to normalize lighting
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l_eq = clahe.apply(l)
        
        # Dark spot detection: find local dark areas
        blur1 = cv2.GaussianBlur(l_eq, (0, 0), 2)
        blur2 = cv2.GaussianBlur(l_eq, (0, 0), 11)
        diff = blur1.astype(np.int16) - blur2.astype(np.int16) + 30
        diff = np.clip(diff, 0, 255).astype(np.uint8)
        
        # Threshold for spot detection
        _, mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # Filter by size - keep only small spots (area < 1% of face)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
        spot_mask = np.zeros_like(mask)
        face_area = fw * fh
        for j in range(1, num_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            if 5 < area < face_area * 0.015:  # Small spots only
                spot_mask[labels == j] = 255
        
        # Dilate slightly for better inpainting
        kernel = np.ones((5,5), np.uint8)
        spot_mask = cv2.dilate(spot_mask, kernel, iterations=1)
        
        if cv2.countNonZero(spot_mask) > 0:
            # Inpaint detected spots
            inpainted = cv2.inpaint(face, spot_mask, 3, cv2.INPAINT_TELEA)
            
            # Feather mask edges
            spot_mask_float = spot_mask.astype(np.float32) / 255.0
            spot_mask_float = cv2.GaussianBlur(spot_mask_float, (9, 9), 0)
            spot_mask_3ch = cv2.merge([spot_mask_float] * 3)
            
            # Blend inpainted spots back onto face
            blended = inpainted.astype(np.float32) * spot_mask_3ch + face.astype(np.float32) * (1 - spot_mask_3ch)
            
            # Composite back
            result[y:y2, x:x2] = blended.astype(np.uint8)
            print(f"Removed spots in face region ({x},{y})-({x2},{y2}), mask pixels: {cv2.countNonZero(spot_mask)}")
        else:
            print(f"No spots detected in face region ({x},{y})-({x2},{y2})")

cv2.imwrite("C:/ComfyUI/output/wedding_output_final.png", result)

# Preview
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Done! Output: wedding_output_final.png")
