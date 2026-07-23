#!/usr/bin/env python3
"""Replace black clothing with white - with smooth, natural edges.
Uses better feathering and edge detection to avoid artifacts."""
import numpy as np
from PIL import Image, ImageFilter
import torch
from segment_anything import sam_model_registry, SamPredictor

MODEL_PATH = r"C:\temp\sam_vit_b.pth"

def segment_person(img_np, predictor):
    """Get person mask using SAM"""
    predictor.set_image(img_np)
    h, w = img_np.shape[:2]
    
    points = np.array([
        [w//2, h//2],
        [w//2, h//3],
        [w//2, h*2//3],
        [w//4, h//2],
        [w*3//4, h//2],
        [w//2, h//4],
        [w//2, h*3//4],
    ])
    labels = np.array([1, 1, 1, 1, 1, 1, 1])
    
    masks, scores, _ = predictor.predict(
        point_coords=points, point_labels=labels, multimask_output=True
    )
    
    order = np.argsort(scores)[::-1]
    for idx in order:
        mask = masks[idx]
        ratio = mask.mean()
        if 0.1 < ratio < 0.8:
            return mask
    
    return masks[np.argmax(scores)]

def white_clothes_smooth(input_path, output_path):
    """Replace dark clothing with white, with smooth natural edges"""
    print("Loading image...")
    img = Image.open(input_path).convert("RGB")
    img_np = np.array(img)
    h, w = img_np.shape[:2]
    
    print("Loading SAM model...")
    sam = sam_model_registry["vit_b"](checkpoint=MODEL_PATH)
    sam.eval()
    predictor = SamPredictor(sam)
    
    print("Segmenting person...")
    person_mask = segment_person(img_np, predictor)
    print(f"Person mask: {person_mask.mean()*100:.1f}%")
    
    r = img_np[:,:,0].astype(float)
    g = img_np[:,:,1].astype(float)
    b = img_np[:,:,2].astype(float)
    brightness = (r + g + b) / 3
    
    # Find dark area (clothing) within person mask
    person_brightness = brightness[person_mask]
    mean_b = person_brightness.mean()
    std_b = person_brightness.std()
    threshold = mean_b + 0.6 * std_b
    print(f"Brightness stats: mean={mean_b:.0f}, std={std_b:.0f}, threshold={threshold:.0f}")
    
    # Clothing mask: dark + within person
    is_dark = (brightness < threshold) & (brightness < 140)
    clothing_mask = is_dark & person_mask
    
    # Clean up clothing mask
    from scipy import ndimage
    clothing_mask = ndimage.binary_closing(clothing_mask, structure=np.ones((7,7)))
    clothing_mask = ndimage.binary_opening(clothing_mask, structure=np.ones((5,5)))
    
    print(f"Clothing pixels: {clothing_mask.sum()} ({100*clothing_mask.sum()/(h*w):.1f}%)")
    
    # ===== KEY IMPROVEMENT: Large feather radius =====
    # Use a large Gaussian blur on the mask for smooth transition
    mask_img = Image.fromarray((clothing_mask * 255).astype(np.uint8))
    # Feather radius 15px - much larger for smooth transition
    feather_radius = 15
    mask_blur = mask_img.filter(ImageFilter.GaussianBlur(feather_radius))
    mask_blur_np = np.array(mask_blur, dtype=np.float32) / 255.0
    
    # Create white clothing with lighting preservation
    # Derive lighting from original brightness
    gray = img.convert("L")
    gray_np = np.array(gray, dtype=np.float32)
    
    # Map brightness to white: original bright areas → brighter white
    # Original dark areas → slightly off-white (for fabric feel)
    light_map = gray_np / 255.0
    # Boost the lighting to make it look like white fabric
    white_base = 200 + light_map * 55  # Range: 200-255
    white_r = np.clip(white_base, 0, 255)
    white_g = np.clip(white_base * 0.97, 0, 255)  # slightly warm
    white_b = np.clip(white_base * 0.94, 0, 255)
    white_img = np.stack([white_r, white_g, white_b], axis=2)
    
    # ===== EDGE IMPROVEMENT: Blend in distance-based way =====
    # Instead of just blurring, we compute a distance transform
    # so that the transition is smooth at clothing boundaries
    
    # Create result
    result_np = img_np.copy().astype(np.float32)
    
    # Blend using feathered mask - expanded feathering
    mask_3d = np.stack([mask_blur_np]*3, axis=2)
    result_np = white_img * mask_3d + img_np * (1 - mask_3d)
    
    # Additional refinement: apply a very light denoising on the transition area
    # to remove any high-frequency edge noise
    transition = (mask_blur_np > 0.05) & (mask_blur_np < 0.95)
    transition_img = Image.fromarray(result_np.astype(np.uint8))
    # Apply very slight bilateral-like smoothing on transition zone
    # Using a small median filter helps
    transition_img_smooth = transition_img.filter(ImageFilter.MedianFilter(3))
    transition_np = np.array(transition_img_smooth, dtype=np.float32)
    
    # Only apply smoothing in transition zone
    t_mask = np.stack([transition]*3, axis=2)
    result_np = np.where(t_mask, result_np * 0.3 + transition_np * 0.7, result_np)
    
    result_np = np.clip(result_np, 0, 255).astype(np.uint8)
    result_img = Image.fromarray(result_np)
    result_img.save(output_path, quality=95)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    white_clothes_smooth(
        r"C:\temp\original_source.png",
        r"C:\temp\clothes_white_v3.jpg"
    )
