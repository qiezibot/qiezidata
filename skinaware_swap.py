#!/usr/bin/env python3
"""
Skin-aware black-to-white clothes changer.
Strategy: 
1. Find all dark pixels (brightness < threshold)
2. Exclude skin-colored pixels
3. Keep only the largest connected dark region in center
4. Replace with white
"""
import cv2
import numpy as np
from PIL import Image

def change_black_to_white_skinaware(input_path, output_path):
    """Replace black clothes with white, avoiding skin areas"""
    print("Loading image...")
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        pil = Image.open(input_path).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    
    h, w = img_bgr.shape[:2]
    print(f"Size: {w}x{h}")
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    
    # Step 1: Find ALL dark pixels (broad threshold)
    _, dark_all = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)
    
    # Step 2: Detect skin pixels to exclude them
    # Skin in HSV: H 0-20 or 170-180, S > 20, V > 40
    h_ch = hsv[:,:,0].astype(np.float32)
    s_ch = hsv[:,:,1]
    v_ch = hsv[:,:,2]
    
    is_skin_1 = (h_ch < 20) | (h_ch > 160)
    is_skin_2 = s_ch > 30
    is_skin_3 = v_ch > 50
    
    skin_mask = (is_skin_1 & is_skin_2 & is_skin_3).astype(np.uint8) * 255
    
    # Also exclude very bright areas (likely background)
    _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Step 3: Dark but NOT skin and NOT very bright
    preliminary = dark_all.astype(np.uint8) & (~skin_mask.astype(bool)).astype(np.uint8)
    preliminary = preliminary & (~bright_mask.astype(bool)).astype(np.uint8)
    preliminary = preliminary * 255
    
    # Step 4: Keep only the main body-connected dark region
    # Dilate to connect nearby dark pixels
    kernel = np.ones((7,7), np.uint8)
    dilated = cv2.dilate(preliminary, kernel, iterations=2)
    
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
    
    # Find which component(s) overlap with the center area (where clothes are)
    center_y1, center_y2 = h//4, h*3//4
    center_x1, center_x2 = w//4, w*3//4
    
    # Score each component by center dark coverage
    component_scores = []
    for i in range(1, num_labels):
        comp_mask = (labels == i)
        # Check overlap with preliminary dark mask (not the dilated one)
        dark_overlap = comp_mask & (preliminary > 0)
        center_overlap = dark_overlap[center_y1:center_y2, center_x1:center_x2].sum()
        total_dark = dark_overlap.sum()
        component_scores.append((i, center_overlap, total_dark, comp_mask))
    
    # Sort by center overlap (descending)
    component_scores.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Found {num_labels-1} dark components")
    for comp_id, center_score, total_score, _ in component_scores[:5]:
        print(f"  Component {comp_id}: center_dark={center_score}, total_dark={total_score}")
    
    # Build clothing mask from top components that have significant center overlap
    clothing_mask = np.zeros((h, w), dtype=np.uint8)
    
    # Must have at least some center overlap
    min_center = 500
    for comp_id, center_score, _, comp_mask in component_scores:
        if center_score >= min_center:
            clothing_mask[comp_mask & (preliminary > 0)] = 255
        elif len(component_scores) <= 2 and center_score > 100:
            # If very few components, be more permissive
            clothing_mask[comp_mask & (preliminary > 0)] = 255
    
    # Step 5: Clean up mask
    clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_CLOSE, np.ones((9,9), np.uint8))
    
    # Fill holes in the mask
    contour_mask = clothing_mask.copy()
    contours, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(clothing_mask)
    cv2.drawContours(filled, contours, -1, 255, -1)
    clothing_mask = filled
    
    # Erode slightly to avoid skin edges
    clothing_mask = cv2.erode(clothing_mask, np.ones((3,3), np.uint8), iterations=1)
    
    clothing_pixels = (clothing_mask > 0).sum()
    print(f"Final clothing pixels: {clothing_pixels} ({100*clothing_pixels/(h*w):.1f}%)")
    
    if clothing_pixels == 0:
        print("ERROR: No clothing detected! Aborting.")
        Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).save(output_path, quality=95)
        return
    
    # Step 6: Feather edges (large radius)
    feather_radius = min(35, min(h, w) // 10)
    feather_mask = cv2.GaussianBlur(clothing_mask.astype(np.float32),
                                     (feather_radius*2+1, feather_radius*2+1),
                                     feather_radius//2)
    feather_mask = feather_mask / 255.0
    
    # Step 7: Create white clothes with lighting
    result = img_bgr.copy().astype(np.float32)
    light = gray.astype(np.float32) / 255.0
    light = np.clip(light * 1.5, 0, 1)  # Boost for white clothes
    
    # Warm white
    white_bgr = np.zeros_like(result)
    white_bgr[:,:,0] = np.clip(248 * light, 0, 255)
    white_bgr[:,:,1] = np.clip(252 * light, 0, 255)
    white_bgr[:,:,2] = np.clip(255 * light, 0, 255)
    
    # Use a steeper transition for the feathered area
    # This makes the edge transition sharper = less "foggy" edge
    transition = np.clip((feather_mask - 0.15) / 0.7, 0, 1)
    
    for c in range(3):
        result[:,:,c] = result[:,:,c] * (1 - transition) + white_bgr[:,:,c] * transition
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # Convert and save
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    Image.fromarray(result_rgb).save(output_path, quality=95)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    change_black_to_white_skinaware(
        r"C:\temp\original_source.png",
        r"C:\temp\clothes_white_v6.jpg"
    )
