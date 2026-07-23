# -*- coding: utf-8 -*-
"""
强效频率分离祛斑 - 精准人脸框
多重模糊 + LAB + 双边滤波组合
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
print("Face: {}x{}".format(fw, fh))

# === SKIN MASK ===
ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
skin1 = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
skin2 = cv2.inRange(hsv, np.array([0, 20, 70]), np.array([20, 150, 255]))
skin = cv2.bitwise_and(skin1, skin2)
sk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, sk)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, sk)
skin = cv2.dilate(skin, sk, iterations=3)
skin_f = skin.astype(np.float32) / 255.0
skin_f = cv2.GaussianBlur(skin_f, (15, 15), 5)
skin_3ch = cv2.merge([skin_f] * 3)
print("Skin: {:.1f}%".format(100.0 * np.sum(skin>0) / (fh*fw)))

# === METHOD 1: Frequency Separation ===
face_f = face.astype(np.float32) / 255.0
# Very strong blur to remove all spots
low_freq = cv2.bilateralFilter(face_f, d=15, sigmaColor=50, sigmaSpace=30)
# Second pass
low_freq = cv2.bilateralFilter(low_freq, d=15, sigmaColor=40, sigmaSpace=25)
high_freq = face_f - low_freq
fs_result = low_freq + high_freq * 0.3  # Only 30% texture back
fs_result = np.clip(fs_result, 0, 1)
fs_result = (fs_result * 255).astype(np.uint8)

# === METHOD 2: LAB Median ===
lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)
# Strong median for spot removal
l1 = cv2.medianBlur(l, 15)
# Then bilateral on L to fix edges
l2 = cv2.bilateralFilter(l1, d=9, sigmaColor=30, sigmaSpace=9)
lab_result = cv2.merge([l2, a, b])
lab_result = cv2.cvtColor(lab_result, cv2.COLOR_LAB2BGR)

# === METHOD 3: Bilateral on BGR ===
bilateral = cv2.bilateralFilter(face, d=15, sigmaColor=60, sigmaSpace=30)
bilateral = cv2.bilateralFilter(bilateral, d=9, sigmaColor=40, sigmaSpace=20)

# === COMBINE: Weighted blend of all methods ===
combined_f = (
    fs_result.astype(np.float32) * 0.4 +
    lab_result.astype(np.float32) * 0.3 +
    bilateral.astype(np.float32) * 0.3
)

# Blend back with original using skin mask
face_f32 = face.astype(np.float32)
result_face = (combined_f * skin_3ch + face_f32 * (1 - skin_3ch * 0.3)).astype(np.uint8)
# ^ 30% original shows through skin for natural look

result = img.copy()
result[y1:y2, x1:x2] = result_face

# ADDITIONAL: Enhance brightness slightly
lab_full = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
l_full, a_full, b_full = cv2.split(lab_full)
l_full = cv2.add(l_full, 5)  # Slight brightening
lab_enhanced = cv2.merge([l_full, a_full, b_full])
result = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

print("Time: {:.1f}s".format(time.time() - t0))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Saved!")
