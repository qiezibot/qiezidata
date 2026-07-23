# -*- coding: utf-8 -*-
"""Zoom in on spot 7 area and analyze what's there"""
import cv2
import numpy as np

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

spot_x, spot_y = 741, 3161

# Crop a 200x200 region around the spot
crop_size = 200
x1 = max(0, spot_x - crop_size//2)
y1 = max(0, spot_y - crop_size//2)
x2 = min(w, spot_x + crop_size//2)
y2 = min(h, spot_y + crop_size//2)

crop = img[y1:y2, x1:x2].copy()
ch, cw = crop.shape[:2]

# Draw a crosshair at center
cv2.line(crop, (cw//2-15, ch//2), (cw//2+15, ch//2), (0, 255, 0), 2)
cv2.line(crop, (cw//2, ch//2-15), (cw//2, ch//2+15), (0, 255, 0), 2)
cv2.circle(crop, (cw//2, ch//2), 3, (0, 0, 255), -1)

# Also find all actual dark spots in this region
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
eq = clahe.apply(gray)

# Blackhat
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
bh = cv2.morphologyEx(eq, cv2.MORPH_BLACKHAT, k)
_, tw = cv2.threshold(bh, 10, 255, cv2.THRESH_BINARY)

# Find connected components
n, labels, stats, _ = cv2.connectedComponentsWithStats(tw, 8)
for j in range(1, n):
    area = stats[j, cv2.CC_STAT_AREA]
    if area > 5:
        sx, sy, sw, sh = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
        cx = sx + sw//2
        cy = sy + sh//2
        cv2.rectangle(crop, (sx, sy), (sx+sw, sy+sh), (255, 0, 0), 1)
        cv2.putText(crop, str(area), (sx, sy-2), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 255), 1)
        print("  Spot at local=({},{}), rel_abs=({},{}), area={}".format(sx, sy, sx+x1, sy+y1, area))

# Save zoomed image
cv2.imwrite(r"C:\temp\tts\spot7_zoom.png", crop)

# Also try to remove it with a MUCH larger area and different inpainting approach
result = img.copy()
mask = np.zeros((h, w), dtype=np.uint8)

# Bigger mask
cv2.circle(mask, (spot_x, spot_y), 60, 255, -1)
# NS algorithm (slower but better for texture)
mask_d = cv2.dilate(mask, np.ones((11,11), np.uint8), iterations=1)
inpainted = cv2.inpaint(result, mask_d, 10, cv2.INPAINT_NS)

# Blend
mf = mask_d.astype(np.float32) / 255.0
mf = cv2.GaussianBlur(mf, (21,21), 8)
m_3ch = cv2.merge([mf]*3)
result = (inpainted.astype(np.float32) * m_3ch + result.astype(np.float32) * (1 - m_3ch)).astype(np.uint8)

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])

print("Crop area: ({},{})-({},{})".format(x1,y1,x2,y2))
print("Sending preview...")
