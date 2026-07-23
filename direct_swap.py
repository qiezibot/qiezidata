#!/usr/bin/env python3
"""
Precise black-to-white clothes changer using OpenCV.
Direct approach: threshold dark colors → refine → feather.
"""
import cv2
import numpy as np
from PIL import Image

def change_black_to_white(input_path, output_path):
    """Replace black clothing with white using direct color thresholding"""
    print("Loading image...")
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        pil = Image.open(input_path).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    
    h, w = img_bgr.shape[:2]
    print(f"Size: {w}x{h}")
    
    # Convert to various color spaces
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    
    # === Strategy: Find dark clothing area ===
    # Black clothes are: low value (HSV-V), low L (LAB-L), dark in grayscale
    
    # 1. Darkness threshold - use very aggressive threshold for black clothing
    _, dark_thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    
    # 2. Also use HSV value channel (more robust)
    v_channel = hsv[:,:,2]
    _, dark_v = cv2.threshold(v_channel, 180, 255, cv2.THRESH_BINARY_INV)
    
    # 3. LAB L-channel (perceptual brightness)
    l_channel = lab[:,:,0]
    _, dark_l = cv2.threshold(l_channel, 180, 255, cv2.THRESH_BINARY_INV)
    
    # Combine: pixels that are dark in at least 1 of 3 measures (aggressive)
    dark_combined = (dark_thresh > 0).astype(np.uint8) | (dark_v > 0).astype(np.uint8) | (dark_l > 0).astype(np.uint8)
    clothing_mask = dark_combined.astype(np.uint8) * 255
    
    # === Refine: keep only the largest connected component (the clothing) ===
    kernel = np.ones((7,7), np.uint8)
    clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_CLOSE, kernel)
    
    # Find connected components, keep the largest one in the center area
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clothing_mask, connectivity=8)
    
    # Filter: keep only components that touch the center area
    center_y1, center_y2 = h//4, h*3//4
    center_x1, center_x2 = w//4, w*3//4
    
    best_label = None
    best_center_overlap = 0
    
    for i in range(1, num_labels):
        # Check if this component overlaps with center
        component_mask = (labels == i)
        center_overlap = component_mask[center_y1:center_y2, center_x1:center_x2].sum()
        if center_overlap > best_center_overlap:
            best_center_overlap = center_overlap
            best_label = i
    
    if best_label is not None and best_center_overlap > 500:
        # Create mask from the best center-overlapping component
        comp_mask = (labels == best_label).astype(np.uint8) * 255
        # Also include any other significant dark components
        clothing_mask = comp_mask.copy()
        for i in range(1, num_labels):
            if i != best_label and stats[i, cv2.CC_STAT_AREA] > 1000:
                clothing_mask[labels == i] = 255
    else:
        # Keep all significant components
        clothing_mask = np.zeros((h, w), dtype=np.uint8)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] > 500:
                clothing_mask[labels == i] = 255
    
    # Morphological cleanup
    clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
    clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    
    clothing_pixels = (clothing_mask > 0).sum()
    print(f"Clothing pixels: {clothing_pixels} ({100*clothing_pixels/(h*w):.1f}%)")
    
    # Double-check: ensure the clothes area in center is covered
    center_dark = (gray[center_y1:center_y2, center_x1:center_x2] < 120).sum()
    mask_center = (clothing_mask[center_y1:center_y2, center_x1:center_x2] > 0).sum()
    if mask_center < center_dark * 0.5 and center_dark > 5000:
        print(f"Warning: Mask misses dark areas in center ({mask_center} vs {center_dark} dark pixels)")
        # Expand mask to cover more dark center area
        _, extra_dark = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        extra_mask = extra_dark.astype(np.uint8) * 255
        clothing_mask = cv2.bitwise_or(clothing_mask, extra_mask)
        clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_CLOSE, np.ones((10,10), np.uint8))
    
    if clothing_pixels < 2000:
        print("WARNING: Too few clothing pixels, adjust threshold...")
        # Try more aggressive threshold
        _, dark_thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)
        clothing_mask = cv2.morphologyEx(dark_thresh, cv2.MORPH_CLOSE, np.ones((10,10), np.uint8))
        clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    
    # === Edge feathering ===
    feather_radius = 35
    feather_mask = cv2.GaussianBlur(clothing_mask.astype(np.float32), 
                                     (feather_radius*2+1, feather_radius*2+1), 
                                     feather_radius//2)
    feather_mask = feather_mask / 255.0
    
    # === Create white clothing with lighting ===
    result = img_bgr.copy().astype(np.float32)
    
    # Use original brightness for texture preservation
    light = gray.astype(np.float32) / 255.0
    # Boost brightness for white clothes
    light = np.clip(light * 1.3, 0, 1)
    
    # Warm white RGB: (255, 250, 245) in BGR is (245, 250, 255)
    white_bgr = np.zeros_like(result)
    white_bgr[:,:,0] = np.clip(245 * light, 0, 255)  # B
    white_bgr[:,:,1] = np.clip(250 * light, 0, 255)  # G
    white_bgr[:,:,2] = np.clip(255 * light, 0, 255)  # R
    
    # Blend with feathered mask
    # Use a more gradual transition: mask values close to 1 → full white
    # mask values near 0.5 → partial transition
    # mask values near 0 → keep original
    
    # Apply the transition more aggressively
    transition = np.clip((feather_mask - 0.2) * 1.5, 0, 1)  # Sharper transition
    
    for c in range(3):
        result[:,:,c] = result[:,:,c] * (1 - transition) + white_bgr[:,:,c] * transition
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # Convert BGR to RGB
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    result_pil = Image.fromarray(result_rgb)
    result_pil.save(output_path, quality=95)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    change_black_to_white(
        r"C:\temp\original_source.png",
        r"C:\temp\clothes_white_v5.jpg"
    )
