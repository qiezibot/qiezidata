"""Smart retouch: only process face region, keep rest sharp"""
import cv2
import numpy as np
import os

img = cv2.imread("C:/ComfyUI/output/wedding_output_00001_.png")
h, w = img.shape[:2]
print(f"Size: {w}x{h}")

# Use OpenCV face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Detect faces on resized version for speed
small = cv2.resize(img, (w//4, h//4))
gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

print(f"Found {len(faces)} face(s)")

result = img.copy()

if len(faces) > 0:
    for (fx, fy, fw, fh) in faces:
        # Scale back to original coordinates
        fx, fy, fw, fh = fx*4, fy*4, fw*4, fh*4
        # Expand face region a bit
        margin_x = int(fw * 0.2)
        margin_y = int(fh * 0.2)
        x1 = max(0, fx - margin_x)
        y1 = max(0, fy - margin_y)
        x2 = min(w, fx + fw + margin_x)
        y2 = min(h, fy + fh + margin_y)
        
        face_region = img[y1:y2, x1:x2]
        
        # Only do light bilateral on skin part
        skin = face_region.copy()
        skin = cv2.bilateralFilter(skin, 5, 20, 20)
        
        # Create edge mask to preserve edges
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_face, 50, 150)
        edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
        
        # Blend: smoothed everywhere except edges
        edge_mask = cv2.cvtColor(255 - edges, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        edge_mask = cv2.GaussianBlur(edge_mask, (5,5), 0)
        
        blended = (skin.astype(np.float32) * edge_mask + 
                   face_region.astype(np.float32) * (1 - edge_mask))
        result[y1:y2, x1:x2] = blended.astype(np.uint8)
        
        print(f"Processed face at ({x1},{y1})-({x2},{y2})")
else:
    print("No face detected, using smart edge-preserving approach on whole image")
    # Edge-preserving filter
    result = cv2.edgePreservingFilter(img, flags=1, sigma_s=60, sigma_r=0.4)

cv2.imwrite("C:/ComfyUI/output/wedding_retouched_00001_.png", result)

# Preview
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Preview saved")
