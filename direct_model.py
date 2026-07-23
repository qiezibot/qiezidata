# -*- coding: utf-8 -*-
"""Load skin retouching generator directly - fixed"""
import os, cv2, numpy as np, torch, time as ttime
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

t0 = ttime.time()
model_dir = os.path.expanduser(r"~\.cache\modelscope\hub\models\damo\cv_unet_skin_retouching_torch")

import sys
sys.path.insert(0, model_dir)
from modelscope.models.cv.skin_retouching.unet_deploy import UNet

state = torch.load(os.path.join(model_dir, "pytorch_model.pt"), map_location="cpu", weights_only=False)
generator_state = state['generator']

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

model = UNet(3, 3).to(device)
model.load_state_dict(generator_state, strict=False)
model.eval()
print("Model loaded in {:.1f}s".format(ttime.time()-t0))

# Load face
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
skin = cv2.bitwise_and(skin1, skin2)
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, k)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, k)
skin = cv2.dilate(skin, k, iterations=2)
skin_f = skin.astype(np.float32) / 255.0
skin_f = cv2.GaussianBlur(skin_f, (25, 25), 8)
skin_3ch = cv2.merge([skin_f]*3)

# Inference
face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
face_resized = cv2.resize(face_rgb, (512, 512))
face_tensor = torch.from_numpy(face_resized.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(device)

with torch.no_grad():
    output_tensor = model(face_tensor)

output = output_tensor[0].cpu().permute(1, 2, 0).numpy()
output = np.clip(output, 0, 1)
output = (output * 255).astype(np.uint8)
output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
output_bgr = cv2.resize(output_bgr, (fw, fh))

# Blend with skin mask (70% AI, 30% original on skin)
face_f = face.astype(np.float32)
out_f = output_bgr.astype(np.float32)
blended = (out_f * skin_3ch * 0.7 + face_f * (1 - skin_3ch * 0.7)).astype(np.uint8)

result = img.copy()
result[y1:y2, x1:x2] = blended

print("Total time: {:.1f}s".format(ttime.time() - t0))

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done!")
