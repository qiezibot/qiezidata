"""Detect moles/spots on face and remove them precisely"""
import cv2
import numpy as np

img = cv2.imread("C:/ComfyUI/output/wedding_codeformer_test__00001_.png")
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

# Face detection
net = cv2.dnn.readNetFromCaffe(
    "C:/u-claw/portable/data/.openclaw/workspace/deploy.prototxt",
    "C:/u-claw/portable/data/.openclaw/workspace/res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104, 177, 123))
net.setInput(blob)
detections = net.forward()

result = img.copy()
spots_found = 0

for i in range(detections.shape[2]):
    confidence = detections[0, 0, i, 2]
    if confidence > 0.7:
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (x, y, x2, y2) = box.astype("int")
        # Expand to cover full face
        cx, cy = (x + x2) // 2, (y + y2) // 2
        face_size = max(x2 - x, y2 - y)
        margin = int(face_size * 0.6)
        fx = max(0, cx - face_size // 2 - margin)
        fy = max(0, cy - face_size // 2 - margin // 2)
        fx2 = min(w, cx + face_size // 2 + margin)
        fy2 = min(h, cy + face_size // 2 + margin)
        
        face = img[fy:fy2, fx:fx2].copy()
        print(f"Face region: ({fx},{fy})-({fx2},{fy2}), size: {face.shape[1]}x{face.shape[0]}")
        
        # Analyze face for dark spots
        # Method: look for local dark areas in multiple color spaces
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        
        # Normalize lighting
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray_eq = clahe.apply(gray)
        
        # Detect spots: difference between fine detail and coarse detail
        fine_blur = cv2.GaussianBlur(gray_eq, (0, 0), 1)
        coarse_blur = cv2.GaussianBlur(gray_eq, (0, 0), 9)
        diff = cv2.absdiff(fine_blur, coarse_blur)
        
        # Also look at L channel in LAB for dark spot detection
        lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
        l = lab[:,:,0]
        l_eq = clahe.apply(l)
        
        # Combined detection
        # 1. Dark spots: pixel is significantly darker than local neighborhood
        local_mean = cv2.GaussianBlur(gray_eq, (0, 0), 5)
        dark_mask = cv2.subtract(local_mean, gray_eq)
        _, dark_thresh = cv2.threshold(dark_mask, 20, 255, cv2.THRESH_BINARY)
        
        # 2. High frequency detail (edges, spots)  
        _, detail_thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
        
        # Combine: dark + detailed = potential spot
        combined = cv2.bitwise_and(dark_thresh, detail_thresh)
        
        # Filter by size (moles are small)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(combined, 8)
        
        spot_mask = np.zeros_like(gray)
        face_area = face.shape[0] * face.shape[1]
        
        for j in range(1, num_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            s_x, s_y, s_w, s_h = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
            # Moles are typically 10-200 pixels area in this resolution
            if 8 < area < min(400, face_area * 0.01):
                # Check aspect ratio (moles are roughly circular)
                aspect = max(s_w, s_h) / max(1, min(s_w, s_h))
                if aspect < 3:  # Not too elongated
                    spots_found += 1
                    spot_mask[labels == j] = 255
                    print(f"  Spot #{spots_found}: pos=({s_x},{s_y}), size={s_w}x{s_h}, area={area}")
        
        if spots_found > 0:
            # Dilate for inpainting
            kernel = np.ones((5,5), np.uint8)
            spot_mask_dilated = cv2.dilate(spot_mask, kernel, iterations=2)
            spot_mask_dilated = cv2.GaussianBlur(spot_mask_dilated.astype(np.float32), (5,5), 0)
            spot_mask_dilated = np.clip(spot_mask_dilated * 2, 0, 255).astype(np.uint8)
            
            # Inpaint
            inpainted = cv2.inpaint(face, spot_mask_dilated, 3, cv2.INPAINT_TELEA)
            
            # Soft blend
            m_float = spot_mask_dilated.astype(np.float32) / 255.0
            m_float = cv2.GaussianBlur(m_float, (7,7), 0)
            m_3ch = cv2.merge([m_float] * 3)
            
            blended = inpainted.astype(np.float32) * m_3ch + face.astype(np.float32) * (1 - m_3ch)
            result[fy:fy2, fx:fx2] = blended.astype(np.uint8)
            
            # Visualize detected spots for debugging
            debug = face.copy()
            debug[spot_mask > 0] = [0, 0, 255]  # Red dots on face
            cv2.imwrite("C:/temp/tts/spot_detection_debug.jpg", debug)
            print(f"Spots visualization saved to C:/temp/tts/spot_detection_debug.jpg")

print(f"Total spots found and removed: {spots_found}")

if spots_found > 0:
    cv2.imwrite("C:/ComfyUI/output/wedding_output_final.png", result)
    preview = cv2.resize(result, (1280, int(1280 * h / w)))
    cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("Final result saved!")
else:
    print("No spots detected - trying alternative method...")
    # Fallback: use aggressive local thresholding on whole image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_eq = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)
    local_mean = cv2.GaussianBlur(gray_eq, (0, 0), 7)
    dark = cv2.subtract(local_mean, gray_eq)
    _, mask = cv2.threshold(dark, 18, 255, cv2.THRESH_BINARY)
    # Apply to face region only
    if fy > 0 and fy2 > 0:
        face_mask = mask[fy:fy2, fx:fx2].copy()
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(face_mask, 8)
        spot_mask2 = np.zeros_like(face_mask)
        for j in range(1, num_labels):
            area = stats[j, cv2.CC_STAT_AREA]
            if 5 < area < 200:
                spot_mask2[labels == j] = 255
        if cv2.countNonZero(spot_mask2) > 0:
            face_region = img[fy:fy2, fx:fx2]
            inpainted = cv2.inpaint(face_region, spot_mask2, 3, cv2.INPAINT_TELEA)
            result[fy:fy2, fx:fx2] = inpainted
            print(f"Fallback: removed {cv2.countNonZero(spot_mask2)} spot pixels")
            cv2.imwrite("C:/ComfyUI/output/wedding_output_final.png", result)
            preview = cv2.resize(result, (1280, int(1280 * h / w)))
            cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
