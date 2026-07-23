#!/usr/bin/env python3
"""Better clothes recolor - use SAM for segmentation + texture-aware white fill"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import torch
from segment_anything import sam_model_registry, SamPredictor

MODEL_PATH = r"C:\temp\sam_vit_b.pth"

def segment_person(img_np, predictor):
    """Segment the person from image"""
    predictor.set_image(img_np)
    h, w = img_np.shape[:2]
    
    # Multiple points to cover the person
    points = np.array([
        [w//2, h//2],           # center
        [w//2, h//3],           # upper body (clothes area)
        [w//2, h*2//3],         # lower body
        [w//4, h//2],
        [w*3//4, h//2],
    ])
    labels = np.array([1, 1, 1, 1, 1])
    
    masks, scores, _ = predictor.predict(
        point_coords=points, point_labels=labels, multimask_output=True
    )
    
    best_idx = np.argmax(scores)
    return masks[best_idx]

def natural_white_recolor(input_path, output_path):
    """Replace clothes with natural white, preserving lighting and texture"""
    print("Loading image...")
    img = Image.open(input_path).convert("RGB")
    img_np = np.array(img)
    
    print("Loading SAM model...")
    sam = sam_model_registry["vit_b"](checkpoint=MODEL_PATH)
    sam.to("cpu")
    predictor = SamPredictor(sam)
    
    print("Segmenting person...")
    person_mask = segment_person(img_np, predictor)
    
    # Convert to grayscale for lighting extraction
    gray = img.convert("L")
    gray_np = np.array(gray, dtype=np.float32)
    
    # Create base white with lighting
    # Normalize lighting to 0-1 range
    light = gray_np / 255.0
    
    # Apply gamma correction for more natural look
    light = np.power(light, 0.8)
    
    # Create white clothes image with proper lighting
    white_r = np.clip(255 * light, 0, 255).astype(np.uint8)
    white_g = np.clip(252 * light, 0, 255).astype(np.uint8)  # slightly warm white
    white_b = np.clip(248 * light, 0, 255).astype(np.uint8)
    
    white_img = np.stack([white_r, white_g, white_b], axis=2)
    
    # Apply slight texture (grain) for fabric look
    texture = np.random.randn(*gray_np.shape) * 3
    white_img = np.clip(white_img.astype(np.float32) + texture[:, :, np.newaxis], 0, 255).astype(np.uint8)
    
    # Smooth the texture
    white_pil = Image.fromarray(white_img)
    white_pil = white_pil.filter(ImageFilter.GaussianBlur(0.5))
    white_np = np.array(white_pil)
    
    # Blend with original image using mask
    mask_3d = np.stack([person_mask]*3, axis=2)
    result = np.where(mask_3d, white_np, img_np)
    
    # Edge refinement: blur mask edges
    mask_img = Image.fromarray((person_mask * 255).astype(np.uint8))
    mask_blur = mask_img.filter(ImageFilter.GaussianBlur(3))
    mask_blur_np = np.array(mask_blur, dtype=np.float32) / 255.0
    
    # Feather the edge transition
    for c in range(3):
        result[:,:,c] = (result[:,:,c] * mask_blur_np + 
                        img_np[:,:,c] * (1 - mask_blur_np))
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    result_img = Image.fromarray(result)
    result_img.save(output_path, quality=95)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    natural_white_recolor(
        r"C:\Users\admin\.openclaw\qqbot\downloads\0719F4F9E276F93F9DF2E38254464081_1778730448209.png",
        r"C:\temp\clothes_white_natural.jpg"
    )
