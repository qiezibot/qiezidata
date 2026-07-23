#!/usr/bin/env python3
"""
Final attempt: GrabCut + aggressive mask + weighted blending
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter

def final_attempt(input_path, output_path):
    print("Loading...")
    img = cv2.imread(input_path)
    if img is None:
        img = cv2.cvtColor(np.array(Image.open(input_path).convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # GrabCut
    mask = np.zeros((h,w), np.uint8)
    bgd = np.zeros((1,65), np.float64)
    fgd = np.zeros((1,65), np.float64)
    rect = (5, 5, w-10, h-10)
    cv2.grabCut(img, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    
    person = np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    
    # Center dark analysis
    cy1, cy2 = h//5, h*4//5
    cx1, cx2 = w//5, w*4//5
    
    center_gray = gray[cy1:cy2, cx1:cx2]
    _, center_dark = cv2.threshold(center_gray, 100, 255, cv2.THRESH_BINARY_INV)
    
    # Find center clothing: dark + in person
    center_clothes = center_dark & (person[cy1:cy2, cx1:cx2] * 255).astype(np.uint8)
    
    # Use this to estimate clothing brightness threshold
    if center_clothes.sum() > 100:
        clothes_px = center_gray[center_clothes > 0]
        max_clothes_bright = clothes_px.max()
        mean_clothes_bright = clothes_px.mean()
        print(f"Center clothing: mean={mean_clothes_bright:.0f}, max={max_clothes_bright:.0f}")
        
        # Threshold: anything darker than mid-range in center is probably clothes
        threshold = min(mean_clothes_bright + 40, 160)
    else:
        threshold = 130
    
    # STEP 1: Create clothes mask
    _, dark_all = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    
    # Exclude the corners (likely background shadows)
    corner_mask = np.zeros((h,w), np.uint8)
    cv2.rectangle(corner_mask, (w//8, h//8), (w*7//8, h*7//8), 255, -1)
    
    clothes = cv2.bitwise_and(dark_all, corner_mask)
    
    # Keep only the main body of clothes (connected component)
    kernel = np.ones((5,5), np.uint8)
    clothes = cv2.morphologyEx(clothes, cv2.MORPH_CLOSE, kernel)
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clothes)
    
    # Score by center overlap
    scores = [(stats[i,cv2.CC_STAT_AREA], i, (labels==i)) for i in range(1, num_labels)]
    scores.sort(key=lambda x: x[0], reverse=True)
    
    # Keep the main body of clothing
    final_clothes = np.zeros((h,w), dtype=np.uint8)
    for area, i, comp in scores:
        if area > 1000:
            final_clothes[comp] = 255
    
    # Fill holes
    final_clothes = 255 - final_clothes
    dt = cv2.distanceTransform(final_clothes, cv2.DIST_L2, 5)
    dt_norm = cv2.normalize(dt, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, holes_filled = cv2.threshold(dt_norm, 5, 255, cv2.THRESH_BINARY)
    final_clothes = 255 - holes_filled
    
    # Clean up
    final_clothes = cv2.morphologyEx(final_clothes, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
    final_clothes = cv2.erode(final_clothes, np.ones((3,3), np.uint8), iterations=2)
    
    cnt = (final_clothes > 0).sum()
    print(f"Clothes mask: {cnt} ({100*cnt/(h*w):.1f}%)")
    
    if cnt < 1000:
        print("Too small, fallback to brute threshold...")
        _, final_clothes = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)
        final_clothes = cv2.erode(final_clothes, np.ones((3,3), np.uint8), iterations=1)
    
    # STEP 2: Feather
    fr = 30
    feather_map = cv2.GaussianBlur(final_clothes.astype(np.float32), (fr*2+1, fr*2+1), fr//2) / 255.0
    
    # STEP 3: Create bright white for clothing
    result = img.copy().astype(np.float32)
    
    # White: use original brightness mapped to 200-255 range
    light = gray.astype(np.float32) / 255.0
    bright_white = 200 + light * 55  # Range 200-255
    
    white = np.zeros_like(result)
    white[:,:,2] = np.clip(bright_white, 0, 255)  # R
    white[:,:,1] = np.clip(bright_white * 0.96, 0, 255)  # G
    white[:,:,0] = np.clip(bright_white * 0.92, 0, 255)  # B
    
    # Aggressive but smooth transition
    trans = feather_map  # Smooth transition from 0 to 1
    
    for c in range(3):
        result[:,:,c] = white[:,:,c] * trans + result[:,:,c] * (1 - trans)
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # STEP 4: Final polish - apply a light median filter on the clothing area
    # to remove any noise at edges
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    result_pil = Image.fromarray(result_rgb)
    
    # Light smoothing
    result_pil = result_pil.filter(ImageFilter.MedianFilter(3))
    
    result_pil.save(output_path, quality=95)
    
    # Stats
    res_np = np.array(result_pil)
    diff = np.abs(cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(float) - res_np.astype(float))
    changed = diff.mean(axis=2) > 15
    print(f"Changed (>15 diff): {changed.sum()} ({100*changed.sum()/(h*w):.1f}%)")
    center_new = res_np[h//4:h*3//4, w//4:w*3//4]
    print(f"Center RGB: {center_new.mean(axis=(0,1))}")
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    final_attempt(r"C:\temp\original_source.png", r"C:\temp\clothes_white_v8.jpg")
