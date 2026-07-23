# -*- coding: utf-8 -*-
"""
ModelScope 皮肤精修 + 精准人脸框
只对脸部皮肤区域做AI祛斑美白，不碰背景/衣服/头发
"""
import cv2
import numpy as np
import time
import os

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

t0 = time.time()

# Load full image
img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]
print("Image: {}x{}".format(w, h))

# Accurate face box
x1, y1, x2, y2 = 1395, 1313, 2392, 2635
face = img[y1:y2, x1:x2].copy()
fh, fw = face.shape[:2]
print("Face: {}x{}".format(fw, fh))

# Save face region as temp input
temp_input = r"C:\temp\tts\_model_face_input.png"
temp_output = r"C:\temp\tts\_model_face_output.png"
cv2.imwrite(temp_input, face)
print("Saved face region for AI model")

# === Skin mask on face ===
ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
skin = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
skin2 = cv2.inRange(hsv, np.array([0, 20, 70]), np.array([20, 150, 255]))
skin = cv2.bitwise_and(skin, skin2)

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, kernel)
skin = cv2.dilate(skin, kernel, iterations=2)
skin_f = skin.astype(np.float32) / 255.0
skin_f = cv2.GaussianBlur(skin_f, (11, 11), 4)
skin_3ch = cv2.merge([skin_f] * 3)

# === Run ModelScope AI skin retouching ===
print("Running ModelScope AI skin retouching...")
script = r"""
import os
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import cv2
import numpy as np
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.outputs import OutputKeys

img = cv2.imread(r'C:\temp\tts\_model_face_input.png')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

pipe = pipeline(Tasks.skin_retouching, model='damo/cv_unet_skin_retouching_torch')
result = pipe(img_rgb)

if isinstance(result, dict) and OutputKeys.OUTPUT_IMG in result:
    output = result[OutputKeys.OUTPUT_IMG]
    if output.dtype != np.uint8:
        output = (output * 255).astype(np.uint8)
    output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
    cv2.imwrite(r'C:\temp\tts\_model_face_output.png', output_bgr)
    print("AI model succeeded")
else:
    print("AI output format unexpected")
    cv2.imwrite(r'C:\temp\tts\_model_face_output.png', img)
"""

import subprocess, sys
result_p = subprocess.run([sys.executable, "-c", script], 
                         capture_output=True, text=True, timeout=300,
                         env={**os.environ, "NO_PROXY": "*", "no_proxy": "*"})
print(result_p.stdout.strip())
if result_p.stderr.strip():
    print("STDERR:", result_p.stderr.strip()[-300:])

# === Check if AI output exists ===
if os.path.exists(temp_output):
    repaired_face = cv2.imread(temp_output)
    if repaired_face.shape[:2] != (fh, fw):
        repaired_face = cv2.resize(repaired_face, (fw, fh))
    
    # Blend with skin mask
    face_f = face.astype(np.float32)
    repair_f = repaired_face.astype(np.float32)
    blended_face = (repair_f * skin_3ch + face_f * (1 - skin_3ch)).astype(np.uint8)
    
    result = img.copy()
    result[y1:y2, x1:x2] = blended_face
    print("Blended AI repair with skin mask")
else:
    print("AI failed, using fallback")
    result = img.copy()

# Save result
cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])

elapsed = time.time() - t0
print("Total time: {:.1f}s".format(elapsed))

# Cleanup
try:
    os.remove(temp_input)
    os.remove(temp_output)
except: pass
print("Done!")
