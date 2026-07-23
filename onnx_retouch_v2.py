# -*- coding: utf-8 -*-
"""
ONNX skin retouching - with correct input dims
"""
import os, time
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import cv2
import numpy as np
import onnxruntime as ort

t0 = time.time()

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

x1, y1, x2, y2 = 1395, 1313, 2392, 2635
face = img[y1:y2, x1:x2].copy()
fh, fw = face.shape[:2]
print("Face: {}x{}".format(fw, fh))

# Skin mask
ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
skin1 = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
skin2 = cv2.inRange(hsv, np.array([0, 20, 70]), np.array([20, 150, 255]))
skin = cv2.bitwise_and(skin1, skin2)
sk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, sk)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, sk)
skin = cv2.dilate(skin, sk, iterations=2)
skin_f = skin.astype(np.float32) / 255.0
skin_f = cv2.GaussianBlur(skin_f, (11, 11), 4)
skin_3ch = cv2.merge([skin_f] * 3)

# Load ONNX model
model_path = os.path.expanduser(r"~\.cache\modelscope\hub\models\damo\cv_unet_skin_retouching_torch\model.onnx")
print("Loading ONNX model...")
sess = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])

# Check input details
inp = sess.get_inputs()[0]
out = sess.get_outputs()[0]
print("Input name:", inp.name, "shape:", inp.shape, "type:", inp.type)
print("Output name:", out.name, "shape:", out.shape, "type:", out.type)

# Preprocess face for model - try HWC (no batch dim)
# After export, some models expect HWC, some CHW
face_input = face.astype(np.float32) / 255.0
# Resize to model expected size
face_input = cv2.resize(face_input, (512, 512))

# Try inference directly
print("Inferring...")
# Try as HWC first (rank 3)
output = sess.run([out.name], {inp.name: face_input})
print("Inference done")

# Postprocess
result_face = output[0]
print("Output shape:", result_face.shape, "dtype:", result_face.dtype, "range:", result_face.min(), "-", result_face.max())

# If output is [1, C, H, W], squeeze
if len(result_face.shape) == 4:
    result_face = result_face[0]
# If CHW -> HWC
if result_face.shape[0] == 3 or result_face.shape[0] == 1:
    result_face = np.transpose(result_face, (1, 2, 0))
if result_face.shape[-1] == 1:
    result_face = np.repeat(result_face, 3, axis=-1)
result_face = np.clip(result_face, 0, 1)
result_face = (result_face * 255).astype(np.uint8)
result_face = cv2.resize(result_face, (fw, fh))

# Also do frequency separation for fallback
lab = cv2.cvtColor(face, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)
l_med = cv2.medianBlur(l, 9)
lab_clean = cv2.merge([l_med, a, b])
fs_result = cv2.cvtColor(lab_clean, cv2.COLOR_LAB2BGR)

# Blend ONNX result with skin mask + blend with FS for safety
face_f = face.astype(np.float32)
repair_f = result_face.astype(np.float32)
fs_f = fs_result.astype(np.float32)

# 70% ONNX + 30% FS
combined = repair_f * 0.7 + fs_f * 0.3
blended = (combined * skin_3ch + face_f * (1 - skin_3ch)).astype(np.uint8)

result_img = img.copy()
result_img[y1:y2, x1:x2] = blended

print("Time: {:.1f}s".format(time.time() - t0))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result_img)
preview = cv2.resize(result_img, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done!")
