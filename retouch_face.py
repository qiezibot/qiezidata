"""Fast spot removal using OpenCV inpainting"""
import cv2
import numpy as np
from PIL import Image

img = cv2.imread("C:/ComfyUI/output/wedding_output_00001_.png")
h, w = img.shape[:2]
print(f"Image size: {w}x{h}")

# Create a mask - in real use you'd mark spots manually
# For now, use a face detection guided approach to smooth skin
# Convert to float for processing
img_float = img.astype(np.float32)

# Apply bilateral filter (preserves edges, smooths skin)
# Process in tiles for speed
tile_size = 512
result = img.copy()

for y in range(0, h, tile_size):
    for x in range(0, w, tile_size):
        y1 = min(y + tile_size, h)
        x1 = min(x + tile_size, w)
        tile = img[y:y1, x:x1]
        # Bilateral filter: d=5, sigmaColor=30, sigmaSpace=30
        result[y:y1, x:x1] = cv2.bilateralFilter(tile, 5, 30, 30)

cv2.imwrite("C:/ComfyUI/output/wedding_retouched_00001_.png", result)
print("Done! Saved wedding_retouched_00001_.png")

# Also make preview
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Preview saved")
