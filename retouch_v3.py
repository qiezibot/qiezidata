"""Smart retouch v3 - selective smoothing with edge preservation"""
import cv2
import numpy as np

img = cv2.imread("C:/ComfyUI/output/wedding_output_00001_.png")
h, w = img.shape[:2]
print(f"Size: {w}x{h}")

# Use edge-preserving filter - smooths flat areas, keeps edges
result = cv2.edgePreservingFilter(img, flags=1, sigma_s=30, sigma_r=0.3)

# Now sharpen the result slightly to restore perceived sharpness
kernel = np.array([[-0.5,-0.5,-0.5],
                   [-0.5, 5.0,-0.5],
                   [-0.5,-0.5,-0.5]])
sharpened = cv2.filter2D(result, -1, kernel)
# Blend 70% sharpened + 30% original to avoid over-sharpening
result = cv2.addWeighted(sharpened, 0.7, img, 0.3, 0)

cv2.imwrite("C:/ComfyUI/output/wedding_retouched_00001_.png", result)

# Preview
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite("C:/temp/tts/wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Done!")
