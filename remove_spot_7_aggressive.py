# -*- coding: utf-8 -*-
"""Remove whatever is at position (741, 3161) - aggressive repair"""
import cv2
import numpy as np

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]
result = img.copy()

# The mole is around (741, 3161) - create a bigger mask
spot_x, spot_y = 741, 3161

# Create mask covering a larger area around the spot
mask = np.zeros((h, w), dtype=np.uint8)
cv2.circle(mask, (spot_x, spot_y), 40, 255, -1)  # radius 40

# Inpaint with larger radius for better texture fill
mask_d = cv2.dilate(mask, np.ones((7,7), np.uint8), iterations=1)
inpainted = cv2.inpaint(result, mask_d, 5, cv2.INPAINT_TELEA)

# Soft blend
mf = mask_d.astype(np.float32) / 255.0
mf = cv2.GaussianBlur(mf, (15,15), 5)
m_3ch = cv2.merge([mf]*3)
result = (inpainted.astype(np.float32) * m_3ch + result.astype(np.float32) * (1 - m_3ch)).astype(np.uint8)

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done - aggressively repaired area around (741,3161)")
