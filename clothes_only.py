#!/usr/bin/env python3
"""SAM + color masking: only change detected clothing area to white, keep skin/background."""
import numpy as np
from PIL import Image, ImageFilter
import torch
from segment_anything import sam_model_registry, SamPredictor
import colorsys

MODEL_PATH = r"C:\temp\sam_vit_b.pth"

def get_clothing_mask(img_np, predictor):
    """Get mask of just the clothing area"""
    predictor.set_image(img_np)
    h, w = img_np.shape[:2]
    
    # Points on upper body (where clothes usually are)
    pts = [
        (w//2, h//2 - h//6),   # chest area
        (w//2, h//2 + h//8),   # belly area
        (w//2 - w//5, h//2),   # left shoulder
        (w//2 + w//5, h//2),   # right shoulder
        (w//2, h//2 - h//4),   # neckline area
    ]
    points = np.array(pts)
    labels = np.array([1, 1, 1, 1, 1])
    
    masks, scores, _ = predictor.predict(
        point_coords=points, point_labels=labels, multimask_output=True
    )
    
    # Try different masks, find the one that covers upper body clothing area
    best_idx = 0
    best_upper_ratio = 0
    
    for i, mask in enumerate(masks):
        # Count pixels in upper body region (where clothes should be)
        upper_region = mask[int(h*0.25):int(h*0.65), :]
        ratio = np.mean(upper_region)
        if ratio > best_upper_ratio:
            best_upper_ratio = ratio
            best_idx = i
    
    return masks[best_idx]

def change_clothes_only(input_path, output_path):
    """Only change the clothing area to white, keep everything else"""
    print("Loading image...")
    img = Image.open(input_path).convert("RGB")
    img_np = np.array(img)
    h, w = img_np.shape[:2]
    
    print("Loading SAM model...")
    sam = sam_model_registry["vit_b"](checkpoint=MODEL_PATH)
    sam.to("cpu")
    predictor = SamPredictor(sam)
    
    print("Finding person...")
    person_mask = get_clothing_mask(img_np, predictor)
    
    # Now within the person area, find the clothes (not skin, not background)
    # Use color info to refine
    refined = np.zeros_like(person_mask, dtype=np.float32)
    
    for y in range(h):
        for x in range(w):
            if not person_mask[y, x]:
                continue
            r, g, b = img_np[y, x]
            
            # Convert to HSV for skin detection
            h_val, s_val, v_val = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            # Skin detection (rough): 
            # Hue in red-yellow range, not too dark, not too bright, some saturation
            is_skin = (h_val < 0.08 or h_val > 0.92) and s_val > 0.08 and v_val > 0.2 and v_val < 0.95
            
            # Very dark or very bright = likely not clothing
            is_bg_like = v_val < 0.08 or v_val > 0.95
            
            if not is_skin and not is_bg_like:
                refined[y, x] = 1.0  # clothing
    
    # Clean up the mask
    mask_img = Image.fromarray((refined * 255).astype(np.uint8))
    mask_img = mask_img.filter(ImageFilter.MaxFilter(3))
    mask_img = mask_img.filter(ImageFilter.MinFilter(5))
    mask_img = mask_img.filter(ImageFilter.MaxFilter(3))
    
    # Feather edges
    mask_blur = mask_img.filter(ImageFilter.GaussianBlur(5))
    mask_np = np.array(mask_img, dtype=np.float32) / 255.0
    mask_blur_np = np.array(mask_blur, dtype=np.float32) / 255.0
    
    # Create white clothing - preserve lighting from original image
    gray = img.convert("L")
    gray_np = np.array(gray, dtype=np.float32)
    light = gray_np / 255.0
    light = np.clip(light * 1.1, 0, 1)  # brighten slightly for white
    
    white_clothes = np.stack([
        np.clip(255 * light, 0, 255),
        np.clip(252 * light, 0, 255),
        np.clip(248 * light, 0, 255)
    ], axis=2).astype(np.uint8)
    
    # Blend with feathering
    mask_3d = np.stack([mask_blur_np]*3, axis=2)
    result = (white_clothes * mask_3d + img_np * (1 - mask_3d)).astype(np.uint8)
    
    result_img = Image.fromarray(result)
    result_img.save(output_path, quality=95)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    change_clothes_only(
        r"C:\Users\admin\.openclaw\qqbot\downloads\0719F4F9E276F93F9DF2E38254464081_1778730448209.png",
        r"C:\temp\clothes_only_white.jpg"
    )
