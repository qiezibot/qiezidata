# -*- coding: utf-8 -*-
"""
Direct ONNX inference for skin retouching - face region only
"""
import os, time
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import cv2
import numpy as np
import onnxruntime as ort

t0 = time.time()

# Load full image
img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

# Face box (Caffe SSD)
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
sess = ort.InferenceSession(model_path, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
print("ONNX model loaded")

# Preprocess face for model
# Model expects: 512x512 or similar, BGR, float32 [0-1]
face_resized = cv2.resize(face, (512, 512))
face_input = face_resized.astype(np.float32) / 255.0
face_input = np.transpose(face_input, (2, 0, 1))  # HWC -> CHW
face_input = np.expand_dims(face_input, axis=0)  # add batch

# Run inference
input_name = sess.get_inputs()[0].name
output_name = sess.get_outputs()[0].name
print("Inferring...")
output = sess.run([output_name], {input_name: face_input})
print("Inference done")

# Postprocess
result_face = output[0][0]  # (C, H, W)
result_face = np.transpose(result_face, (1, 2, 0))  # HWC
result_face = np.clip(result_face, 0, 1)
result_face = (result_face * 255).astype(np.uint8)

# Resize back to face size
result_face = cv2.resize(result_face, (fw, fh))

# Blend with skin mask (only replace skin pixels)
face_f = face.astype(np.float32)
repair_f = result_face.astype(np.float32)
blended = (repair_f * skin_3ch + face_f * (1 - skin_3ch)).astype(np.uint8)

result = img.copy()
result[y1:y2, x1:x2] = blended

print("Time: {:.1f}s".format(time.time() - t0))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done!")
