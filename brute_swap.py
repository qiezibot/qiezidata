#!/usr/bin/env python3
"""
Brute-force black to white: replace ALL dark pixels with white,
then carefully feather the result against the original.
Simple, aggressive, then blend.
"""
import cv2
import numpy as np
from PIL import Image

def brute_white(input_path, output_path):
    print("Loading...")
    img = cv2.imread(input_path)
    if img is None:
        img = cv2.cvtColor(np.array(Image.open(input_path).convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Brute force: brightness < 190 → consider as clothes candidate
    _, dark_full = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY_INV)
    
    # Keep the largest component in the center area
    # But also keep smaller pieces that connect to it
    kernel = np.ones((15,15), np.uint8)
    dilated = cv2.dilate(dark_full, kernel, iterations=3)
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
    
    # Score: center overlap
    cy1, cy2 = h//6, h*5//6
    cx1, cx2 = w//6, w*5//6
    
    scores = []
    for i in range(1, num_labels):
        comp = (labels == i)
        overlap = comp[cy1:cy2, cx1:cx2].sum()
        scores.append((overlap, i, comp))
    
    scores.sort(key=lambda x: x[0], reverse=True)
    
    # Keep components linked to the main one (connected via dilation)
    main_idx = scores[0][1] if scores else None
    
    if main_idx is not None:
        main_comp = (labels == main_idx)
        # Get connected dark pixels from original (not dilated)
        main_dark = main_comp & (dark_full > 0)
        
        # The main mask: all dark pixels in the main component
        mask = main_dark.astype(np.uint8) * 255
    else:
        mask = dark_full
    
    # Fill holes
    mask = 255 - mask  # invert
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    mask = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
    mask = 255 - mask  # re-invert
    
    # Clean
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
    mask = cv2.erode(mask, np.ones((2,2), np.uint8), iterations=1)
    
    count = (mask > 0).sum()
    print(f"Mask size: {count} ({100*count/(h*w):.1f}%)")
    
    # Feather
    fr = 25
    feather = cv2.GaussianBlur(mask.astype(np.float32), (fr*2+1, fr*2+1), fr//2) / 255.0
    
    # Create white
    result = img.copy().astype(np.float32)
    light = gray.astype(np.float32) / 255.0
    light = np.clip(light * 1.4 + 0.1, 0, 1)
    
    white = np.zeros_like(result)
    white[:,:,0] = np.clip(245 * light, 0, 255)
    white[:,:,1] = np.clip(250 * light, 0, 255)
    white[:,:,2] = np.clip(255 * light, 0, 255)
    
    # Aggressive transition
    trans = np.clip((feather - 0.1) * 1.25, 0, 1)
    
    for c in range(3):
        result[:,:,c] = result[:,:,c] * (1 - trans) + white[:,:,c] * trans
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    res_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    Image.fromarray(res_rgb).save(output_path, quality=95)
    
    # Stats
    diff = np.abs(img.astype(float) - result.astype(float))
    changed = diff.mean(axis=2) > 20
    print(f"Changed: {changed.sum()} ({100*changed.sum()/(h*w):.1f}%)")
    print(f"Mean diff: {diff.mean():.1f}")
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    brute_white(r"C:\temp\original_source.png", r"C:\temp\clothes_white_v7.jpg")
