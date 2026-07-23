"""Face detail retouch: detect face, aggressively remove spots using inpainting"""
import cv2
import numpy as np

img = cv2.imread("C:/ComfyUI/output/wedding_output_00001_.png")
h, w = img.shape[:2]

# Use DNN face detector for better detection
net = cv2.dnn.readNetFromCaffe(
    "C:/u-claw/portable/data/.openclaw/workspace/deploy.prototxt",
    "C:/u-claw/portable/data/.openclaw/workspace/res10_300x300_ssd_iter_140000.caffemodel"
)

# Try DNN detection
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104, 177, 123))
net.setInput(blob)
detections = net.forward()

result = img.copy()

found_face = False
for i in range(detections.shape[2]):
    confidence = detections[0, 0, i, 2]
    if confidence > 0.7:
        found_face = True
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (x, y, x2, y2) = box.astype("int")
        # Expand face area
        mw = int((x2 - x) * 0.3)
        mh = int((y2 - y) * 0.3)
        x = max(0, x - mw)
        y = max(0, y - mh)
        x2 = min(w, x2 + mw)
        y2 = min(h, y2 + mh)
        
        face = img[y:y2, x:x2].copy()
        fh, fw = face.shape[:2]
        
        # Strong inpainting approach:
        # 1. Detect dark spots as mask
        gray_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        
        # Use adaptive threshold to find spots (dark areas smaller than skin)
        blur = cv2.GaussianBlur(gray_face, (0, 0), 3)
        diff = blur.astype(np.int16) - cv2.GaussianBlur(gray_face, (0, 0), 15).astype(np.int16)
        diff = np.clip(diff, 0, 255).astype(np.uint8)
        
        # Threshold to find spots
        _, mask = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
        
        # Clean up mask - remove noise, keep only small spots
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        
        # Dilate mask slightly for better inpainting
        mask = cv2.dilate(mask, np.ones((5,5), np.uint8), iterations=1)
        
        # Inpaint with Telea method
        inpainted = cv2.inpaint(face, mask, 3, cv2.INPAINT_TELEA)
        
        # Also apply light bilateral filter on whole face
        smoothed = cv2.bilateralFilter(inpainted, 7, 40, 40)
        
        # Blend with original face (only where mask exists, keep rest sharp)
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        # Feather the mask
        mask_3ch = cv2.GaussianBlur(mask_3ch, (15, 15), 0)
        
        blended = (smoothed.astype(np.float32) * mask_3ch + 
                   face.astype(np.float32) * (1 - mask_3ch))
        
        # Also blend a tiny bit of smoothing everywhere on face for skin texture
        smooth_face = cv2.bilateralFilter(face, 5, 15, 15)
        skin_mask = np.ones_like(mask_3ch) * 0.15  # 15% everywhere
        skin_mask = cv2.GaussianBlur(skin_mask, (31, 31), 0)
        
        blended = (blended.astype(np.float32) * (1 - skin_mask) + 
                   smooth_face.astype(np.float32) * skin_mask)
        
        result[y:y2, x:x2] = blended.astype(np.uint8)
        print(f"Face processed at ({x},{y})-({x2},{y2})")

if not found_face:
    print("DNN face detection failed, trying cascade...")
    # Fallback to Haar cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    small = cv2.resize(img, (w//2, h//2))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
    print(f"Found {len(faces)} face(s) with cascade")
    
    for (fx, fy, fw, fh) in faces:
        fx, fy = fx*2, fy*2
        fw, fh = fw*2, fh*2
        # Expand
        mx, my = int(fw*0.5), int(fh*0.2)
        x1 = max(0, fx-mx)
        y1 = max(0, fy-my)
        x2 = min(w, fx+fw+mx)
        y2 = min(h, fy+fh+my)
        
        face = img[y1:y2, x1:x2].copy()
        
        # Apply bilateral filter for skin smoothing
        smoothed = cv2.bilateralFilter(face, 9, 50, 50)
        
        # Edge mask to preserve details
        gray_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_face, 30, 100)
        edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
        edges = cv2.GaussianBlur(edges.astype(np.float32), (5,5), 0)
        edge_mask = cv2.cvtColor((255 - edges).astype(np.uint8), cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        
        blended = (smoothed.astype(np.float32) * edge_mask + face.astype(np.float32) * (1 - edge_mask))
        result[y1:y2, x1:x2] = blended.astype(np.uint8)

# Final sharpen
kernel = np.array([[-0.3,-0.3,-0.3],
                   [-0.3, 3.4,-0.3],
                   [-0.3,-0.3,-0.3]])
result = cv2.filter2D(result, -1, kernel)

cv2.imwrite("C:/ComfyUI/output/wedding_retouched_00001_.png", result)

# Preview
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Done!")
