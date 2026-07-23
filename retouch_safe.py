# -*- coding: utf-8 -*-
"""
安全去斑 - 只修检测到的斑点，不动纹理
最小影响方案
"""
import cv2
import numpy as np
import time

t0 = time.time()
img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

x1, y1, x2, y2 = 1395, 1313, 2392, 2635
face = img[y1:y2, x1:x2].copy()
fh, fw = face.shape[:2]

# Skin mask
ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
skin1 = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
skin2 = cv2.inRange(hsv, np.array([0, 20, 70]), np.array([20, 150, 255]))
skin_mask = cv2.bitwise_and(skin1, skin2)
skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
skin_mask = cv2.erode(skin_mask, np.ones((3,3),np.uint8), iterations=1)

# Convert to LAB for analysis
lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)

# Adaptive threshold per local region
# Use blackhat to find small dark spots
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
bh = cv2.morphologyEx(l, cv2.MORPH_BLACKHAT, kernel)

# Adaptive threshold
spot_mask = cv2.adaptiveThreshold(bh, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 51, 5)

# Only keep spots on skin
spot_mask = cv2.bitwise_and(spot_mask, skin_mask)

# Remove noise - only keep spots > threshold
n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(spot_mask, 8)
clean_mask = np.zeros_like(spot_mask)
spot_count = 0
for j in range(1, n_labels):
    area = stats[j, cv2.CC_STAT_AREA]
    if 8 < area < 200:
        sx, sy, sw, sh = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
        asp = max(sw, sh) / max(1, min(sw, sh))
        if asp < 3:  # Not too elongated
            clean_mask[labels == j] = 255
            spot_count += 1

print("Found {} spots on skin".format(spot_count))

# VERY MINIMAL inpaint - just the spots
# Dilate just 1 pixel
md = cv2.dilate(clean_mask, np.ones((2,2),np.uint8), iterations=1)

# Inpaint with TELEA - preserves texture
inpainted = cv2.inpaint(face, md, 1, cv2.INPAINT_TELEA)

# Soft blend only at spot edges
mf = clean_mask.astype(np.float32) / 255.0
mf = cv2.GaussianBlur(mf, (3,3), 0.5)
mc = cv2.merge([mf]*3)

# Only replace spot pixels, keep everything else
face_f = face.astype(np.float32)
inp_f = inpainted.astype(np.float32)
blended = (inp_f * mc + face_f * (1 - mc)).astype(np.uint8)

result = img.copy()
result[y1:y2, x1:x2] = blended

print("Time: {:.1f}s".format(time.time() - t0))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done!")
