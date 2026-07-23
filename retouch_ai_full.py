"""ModelScope皮肤精修 — 直接处理原图并保存全分辨率"""
import os, sys, uuid, json
os.environ.pop('HTTP_PROXY', None); os.environ.pop('HTTPS_PROXY', None); os.environ.pop('ALL_PROXY', None)
os.environ['MODELSCOPE_LOCK'] = 'false'

import cv2, torch
import numpy as np
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

IMG_PATH = r'C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\ebc873ea-5136-42ce-9155-e62e21d2d988.png'

print("加载模型...")
pipe = pipeline(Tasks.skin_retouching, model='damo/cv_unet_skin-retouching')
print("✅ 模型加载完成")

img = cv2.imread(IMG_PATH)
h, w = img.shape[:2]
print(f"原图: {w}x{h}")

# 缩到2000以内（模型限制）
target = 2000
scale = target / max(w, h)
resized = cv2.resize(img, (int(w*scale), int(h*scale)))
print(f"输入: {int(w*scale)}x{int(h*scale)}")

print("推理中...")
result = pipe(resized)
output = result['output_img']
print(f"输出: {output.shape[1]}x{output.shape[0]}")

uid = uuid.uuid4().hex[:8]
out_ai = os.path.join(OUTPUT_DIR, f"retouch_ai_{uid}.png")
cv2.imwrite(out_ai, output, [cv2.IMWRITE_PNG_COMPRESSION, 3])

# 也保存JPG预览
out_jpg = os.path.join(OUTPUT_DIR, f"retouch_ai_{uid}.jpg")
cv2.imwrite(out_jpg, output, [cv2.IMWRITE_JPEG_QUALITY, 95])

print(f"✅ 完成: {out_ai}")
print(f"路径: {out_ai}")
