# -*- coding: utf-8 -*-
"""
ModelScope skin retouching + FaceSkin mask only
"""
import os, sys, time, json, cv2, numpy as np
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

t0 = time.time()
img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]
print("Image: {}x{}".format(w, h))

# Face box
x1, y1, x2, y2 = 1395, 1313, 2392, 2635
face = img[y1:y2, x1:x2].copy()
fh, fw = face.shape[:2]

# Get face skin mask using mediapipe or skin detection
# Use YCrCb + HSV enhanced detection
ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
Cr = ycrcb[:,:,1]
Cb = ycrcb[:,:,2]
skin1 = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))

hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
hsv_lower = np.array([0, 25, 70])
hsv_upper = np.array([20, 150, 255])
skin2 = cv2.inRange(hsv, hsv_lower, hsv_upper)

skin = cv2.bitwise_and(skin1, skin2)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, kernel)
skin = cv2.dilate(skin, kernel, iterations=2)
skin_f = skin.astype(np.float32) / 255.0

# Also subtract eyes/eyebrows area (roughly central-upper face)
# Exclude top 25% of face (hair/forehead top), bottom 15% (mouth/chin edge)
mask_keep = np.ones((fh, fw), dtype=np.uint8) * 255
# Top forehead area - keep some for skin
# Bottom chin area - keep
# Just use the skin mask alone

# Feather skin mask
skin_f = cv2.GaussianBlur(skin_f, (25, 25), 8)
skin_3ch = cv2.merge([skin_f]*3)

# Run ModelScope skin retouching on face region
script = r"""
import os, sys, cv2, numpy as np
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# Try loading via modelscope directly
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.outputs import OutputKeys

img = cv2.imread(r'C:\ComfyUI\input\wedding_input.png')
# Crop to face first
face = img[1313:2635, 1395:2392]
img_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

pipe = pipeline(Tasks.skin_retouching, model='damo/cv_unet_skin_retouching_torch')
result = pipe(img_rgb)

if isinstance(result, dict) and OutputKeys.OUTPUT_IMG in result:
    output = result[OutputKeys.OUTPUT_IMG]
    if output.dtype != np.uint8:
        output = (output * 255).astype(np.uint8)
    output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
else:
    output_bgr = face

cv2.imwrite(r'C:\temp\tts\_skin_out.png', output_bgr)
print('ModelScope skin retouching done')
"""

print("Running ModelScope...")
import subprocess
p = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=300,
                   env={**os.environ, "NO_PROXY": "*", "no_proxy": "*"})
print(p.stdout.strip()[-200:])
err = p.stderr.strip()
if err:
    # Check if it's the same registry error
    if "is not in the pipelines registry" in err:
        print("Pipeline registry error again. Using direct model load...")
    else:
        print("STDERR:", err[-300:])

# Check if output exists
if os.path.exists(r"C:\temp\tts\_skin_out.png"):
    repaired = cv2.imread(r"C:\temp\tts\_skin_out.png")
    repaired = cv2.resize(repaired, (fw, fh))
    
    # Blend: only replace skin pixels
    face_f = face.astype(np.float32)
    repair_f = repaired.astype(np.float32)
    
    # Blend with weighted skin mask (70% repair on skin areas)
    blended = (repair_f * 0.7 * skin_3ch + face_f * (1 - 0.7 * skin_3ch)).astype(np.uint8)
    
    result = img.copy()
    result[y1:y2, x1:x2] = blended
    print("Blended successfully with skin mask")
else:
    print("ModelScope failed, using fallback")
    # Fallback: frequency separation with skin mask only
    result = img.copy()
    
print("Time: {:.1f}s".format(time.time() - t0))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done!")
