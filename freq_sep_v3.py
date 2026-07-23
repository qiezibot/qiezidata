# -*- coding: utf-8 -*-
"""
频率分离去斑 V3 - 精准人脸框 (1395,1313)-(2392,2635)
只修皮肤区域，保留眼睛/眉毛/嘴巴/头发
"""
import cv2
import numpy as np
import time

t0 = time.time()
img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

# Accurate face box from Caffe SSD
x1, y1, x2, y2 = 1395, 1313, 2392, 2635
face = img[y1:y2, x1:x2].copy()
fh, fw = face.shape[:2]
print("Face: {}x{}".format(fw, fh))

# === SKIN MASK ===
# YCrCb skin detection
ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
skin = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))

# HSV skin detection  
hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
skin2 = cv2.inRange(hsv, np.array([0, 20, 70]), np.array([20, 150, 255]))
skin = cv2.bitwise_and(skin, skin2)

# Clean up
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, kernel)
skin = cv2.dilate(skin, kernel, iterations=2)

skin_pct = 100 * np.sum(skin > 0) / (fh * fw)
print("Skin: {:.1f}%".format(skin_pct))

# === MULTI-LEVEL SPOT REMOVAL ===
# Level 1: LAB median filter for color spots
lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)
l_med = cv2.medianBlur(l, 9)
lab_clean = cv2.merge([l_med, a, b])
color_fixed = cv2.cvtColor(lab_clean, cv2.COLOR_LAB2BGR)

# Level 2: Frequency separation
face_f = face.astype(np.float32) / 255.0
low_freq = cv2.GaussianBlur(face_f, (0, 0), 12)
high_freq = face_f - low_freq

color_fixed_f = color_fixed.astype(np.float32) / 255.0

# Reduce spots more aggressively on color layer
low2 = cv2.GaussianBlur(color_fixed_f, (0, 0), 8)
high2 = color_fixed_f - low2

# Reconstruct with reduced spot layer
reconstructed = low_freq + high_freq * 0.6
reconstructed = np.clip(reconstructed, 0, 1)
repaired = (reconstructed * 255).astype(np.uint8)

# === BLEND with skin mask ===
skin_f = skin.astype(np.float32) / 255.0
skin_f = cv2.GaussianBlur(skin_f, (11, 11), 4)
skin_3ch = cv2.merge([skin_f] * 3)

result = img.copy()
blended = (repaired.astype(np.float32) * skin_3ch + 
           face.astype(np.float32) * (1 - skin_3ch)).astype(np.uint8)
result[y1:y2, x1:x2] = blended

elapsed = time.time() - t0
print("Time: {:.1f}s".format(elapsed))

# Save
cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Saved!")
