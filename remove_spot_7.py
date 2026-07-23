# -*- coding: utf-8 -*-
"""Precise single spot removal at (741, 3161)"""
import cv2
import numpy as np

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

result = img.copy()

# The spot is at absolute coordinates (741, 3161)
spot_x, spot_y = 741, 3161
radius = 25  # reasonable radius for a mole

# Create mask for inpaint
mask = np.zeros((h, w), dtype=np.uint8)
cv2.circle(mask, (spot_x, spot_y), radius, 255, -1)

# Also add a few nearby spots from the list that were identified
nearby_spots = [
    (741, 3161, 7),
    (1155, 3161, 11),
    (1453, 3159, 9),
    # Bottom edge spots
    (1664, 3160, 6),
    (1914, 3161, 10),
    (2097, 3160, 30),
    (2119, 3159, 10),
    (2130, 3159, 14),
    (2305, 3160, 10),
    (2316, 3160, 12),
    (2343, 3160, 8),
    (2358, 3158, 8),
    (2420, 3160, 16),
    (2432, 3159, 10),
    (2444, 3159, 8),
    (2552, 3160, 9),
    (2582, 3160, 8),
    (2651, 3158, 12),
]

for (sx, sy, sa) in nearby_spots:
    cv2.circle(mask, (sx, sy), max(3, int(np.sqrt(sa / np.pi)) + 3), 255, -1)

# Dilate a bit for smooth transition
kernel = np.ones((5,5), np.uint8)
mask_d = cv2.dilate(mask, kernel, iterations=1)

# Inpaint with TELEA
inpainted = cv2.inpaint(result, mask_d, 2, cv2.INPAINT_TELEA)

# Soft blend at edges
mask_float = mask_d.astype(np.float32) / 255.0
mask_blur = cv2.GaussianBlur(mask_float, (7,7), 2)
mask_3ch = cv2.merge([mask_blur]*3)
result = (inpainted.astype(np.float32) * mask_3ch + result.astype(np.float32) * (1 - mask_3ch)).astype(np.uint8)

cv2.imwrite(r"C:\ComfyUI\output\wedding_output_final.png", result)
preview = cv2.resize(result, (1280, int(1280 * h / w)))
cv2.imwrite(r"C:\temp\tts\wedding_preview.jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Done! Spot at (741,3161) removed.")
