#!/usr/bin/env python3
"""Replace ONLY the dark/black clothing area with white, keeping skin/background intact.
Uses SAM to segment the person, then within the person mask, replaces 
pixels that are dark/black (clothing) with white while preserving lighting."""
import numpy as np
from PIL import Image, ImageFilter
import torch
from segment_anything import sam_model_registry, SamPredictor

MODEL_PATH = r"C:\temp\sam_vit_b.pth"

def segment_person(img_np, predictor):
    """Get full person mask using SAM"""
    predictor.set_image(img_np)
    h, w = img_np.shape[:2]
    
    # Points covering the full body
    points = np.array([
        [w//2, h//2],           # center
        [w//2, h//3],           # upper body (chest)
        [w//2, h*2//3],         # lower body
        [w//4, h//2],           
        [w*3//4, h//2],
        [w//2, h//4],           # head area
        [w//2, h*3//4],         # legs
    ])
    labels = np.array([1, 1, 1, 1, 1, 1, 1])
    
    masks, scores, _ = predictor.predict(
        point_coords=points, point_labels=labels, multimask_output=True
    )
    
    # Pick the mask with best score that also has good coverage
    # Sort by score, try each one
    order = np.argsort(scores)[::-1]
    
    for idx in order:
        mask = masks[idx]
        # Check if this mask covers a reasonable area (not too small, not too large)
        ratio = mask.mean()
        if 0.1 < ratio < 0.8:
            return mask
    
    # Fallback: best score
    return masks[np.argmax(scores)]

def black_to_white(input_path, output_path):
    """Replace dark/black clothing with white, preserving everything else"""
    print("Loading image...")
    img = Image.open(input_path).convert("RGB")
    img_np = np.array(img)
    h, w = img_np.shape[:2]
    
    print("Loading SAM model...")
    # Use CPU
    sam = sam_model_registry["vit_b"](checkpoint=MODEL_PATH)
    sam.eval()
    predictor = SamPredictor(sam)
    
    print("Segmenting person...")
    person_mask = segment_person(img_np, predictor)
    print(f"Person mask covers {person_mask.mean()*100:.1f}% of image")
    
    # Create grayscale for lighting info
    img_gray = img.convert("L")
    gray_np = np.array(img_gray, dtype=np.float32)
    
    # Create result image - start with original
    result_np = img_np.copy().astype(np.float32)
    
    # Within the person mask, identify clothing vs skin
    # Clothing is generally darker and less saturated than skin
    r, g, b = img_np[:,:,0].astype(float), img_np[:,:,1].astype(float), img_np[:,:,2].astype(float)
    
    # Brightness
    brightness = (r + g + b) / 3
    
    # For each pixel in person mask:
    # - If it's dark (brightness < threshold) → it's likely clothing → replace with white
    # - If it's bright → it's likely skin/hair → keep original
    
    # Adaptive threshold based on the person area
    person_brightness = brightness[person_mask]
    # Use mean + std to find the boundary between dark clothes and skin
    mean_bright = person_brightness.mean()
    std_bright = person_brightness.std()
    
    # Threshold: anything darker than (mean + 0.5*std) is likely clothing
    threshold = mean_bright + 0.5 * std_bright
    print(f"Person brightness: mean={mean_bright:.0f}, std={std_bright:.0f}, threshold={threshold:.0f}")
    
    # But also check saturation - skin has more red-yellow tone
    # Convert to HSV-like
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = np.where(mx > 0, (mx - mn) / mx * 255, 0)
    
    # Clothing tends to be: dark AND low-medium saturation
    # Skin tends to be: lighter AND warm-toned
    
    # Create clothing mask
    is_dark = brightness < threshold
    # Exclude very bright areas (likely skin)
    is_dark = is_dark & (brightness < 120)
    # Only within person
    clothing_mask = is_dark & person_mask
    
    # Refine: morphological cleanup
    from scipy import ndimage
    clothing_mask = ndimage.binary_closing(clothing_mask, structure=np.ones((5,5)))
    clothing_mask = ndimage.binary_opening(clothing_mask, structure=np.ones((3,3)))
    
    clothing_count = clothing_mask.sum()
    print(f"Clothing pixels identified: {clothing_count} ({100*clothing_count/(h*w):.1f}%)")
    
    if clothing_count < 1000:
        print("WARNING: Very few clothing pixels detected! Adjusting threshold...")
        # Aggressive mode: use lower threshold
        threshold = mean_bright + 0.2 * std_bright
        is_dark = brightness < threshold
        is_dark = is_dark & (brightness < 150)
        clothing_mask = is_dark & person_mask
        clothing_mask = ndimage.binary_closing(clothing_mask, structure=np.ones((5,5)))
        print(f"Adjusted clothing pixels: {clothing_mask.sum()}")
    
    # For clothing pixels, create white color that preserves the lighting/texture
    # Normalize brightness to get lighting map
    clothing_brightness = brightness[clothing_mask]
    if clothing_brightness.max() > 0:
        # Map the current lighting to a bright white range (200-255)
        lighting = (clothing_brightness - clothing_brightness.min()) / max(clothing_brightness.max() - clothing_brightness.min(), 1)
        # Scale to white range
        white_vals = 200 + lighting * 55  # Range: 200-255
    else:
        white_vals = np.full_like(clothing_brightness, 235)
    
    # Apply white color with slight warm tint
    white_r = np.clip(white_vals, 0, 255).astype(np.uint8)
    white_g = np.clip(white_vals * 0.97, 0, 255).astype(np.uint8)  # slightly warm
    white_b = np.clip(white_vals * 0.93, 0, 255).astype(np.uint8)
    
    # Apply to result
    result_np[clothing_mask, 0] = white_r
    result_np[clothing_mask, 1] = white_g
    result_np[clothing_mask, 2] = white_b
    
    # Feather edges of clothing mask
    mask_img = Image.fromarray((clothing_mask * 255).astype(np.uint8))
    mask_blur = mask_img.filter(ImageFilter.GaussianBlur(5))
    mask_blur_np = np.array(mask_blur, dtype=np.float32) / 255.0
    
    # Create white version with proper lighting
    white_full = np.stack([
        np.clip(200 + (gray_np / 255.0) * 55, 0, 255),
        np.clip((200 + (gray_np / 255.0) * 55) * 0.97, 0, 255),
        np.clip((200 + (gray_np / 255.0) * 55) * 0.93, 0, 255)
    ], axis=2)
    
    # Blend using feathered mask
    for c in range(3):
        result_np[:,:,c] = result_np[:,:,c] * (1 - mask_blur_np) + white_full[:,:,c] * mask_blur_np
    
    result_np = np.clip(result_np, 0, 255).astype(np.uint8)
    
    # Save result
    result_img = Image.fromarray(result_np)
    result_img.save(output_path, quality=95)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    black_to_white(
        r"C:\temp\original_source.png",
        r"C:\temp\clothes_white_new.jpg"
    )
