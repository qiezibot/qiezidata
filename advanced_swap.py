#!/usr/bin/env python3
"""
Advanced clothes color change using OpenCV and GrabCut.
No GPU required, no SAM needed.
Uses GrabCut + color thresholding for precise clothing segmentation.
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter

def precise_clothes_change(input_path, output_path, target_color=(255, 252, 248)):
    """Precise clothes color replacement using GrabCut + adaptive threshold"""
    print("Loading image...")
    img = cv2.imread(input_path)
    if img is None:
        # Try PIL fallback
        pil_img = Image.open(input_path).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    h, w = img.shape[:2]
    print(f"Image size: {w}x{h}")
    
    # Step 1: GrabCut for initial person segmentation
    print("Running GrabCut segmentation...")
    mask = np.zeros(img.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    # Rectangle covering most of the image (leave border for background)
    rect = (10, 10, w-20, h-20)
    cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    
    # Create person mask (foreground + probable foreground)
    person_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    
    # Step 2: Refine with center points (assume center is clothing for portrait)
    print("Refining clothing region...")
    
    # Convert to HSV for better color analysis
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Center region (likely clothing for a portrait)
    center_roi = img[h//4:h*3//4, w//4:w*3//4]
    center_hsv = hsv[h//4:h*3//4, w//4:w*3//4]
    
    # Find the dominant color in center (this should be the clothing)
    # Cluster center pixels
    z = center_roi.reshape((-1, 3))
    z = np.float32(z)
    
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    k = 3
    _, labels, centers = cv2.kmeans(z, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Find the darkest cluster (likely the black clothing)
    centers_brightness = centers.sum(axis=1)
    # Sort: darkest first
    center_order = np.argsort(centers_brightness)
    
    # The clothing cluster should be the dominant one in center
    unique, counts = np.unique(labels, return_counts=True)
    # Find the most common dark cluster
    dark_cluster_idx = None
    for idx in center_order:
        if idx in unique:
            count = counts[list(unique).index(idx)]
            if count > 1000:  # Significant cluster
                dark_cluster_idx = idx
                break
    
    if dark_cluster_idx is not None:
        clothing_color = centers[dark_cluster_idx]
        print(f"Detected clothing color (BGR): {clothing_color}")
        
        # Create clothing mask based on color similarity
        img_flat = img.reshape((-1, 3)).astype(np.float32)
        
        # Distance to clothing color
        diff = np.abs(img_flat - clothing_color).sum(axis=1)
        
        # Adaptive threshold
        color_threshold = 150  # BGR sum difference
        clothing_by_color = (diff < color_threshold).reshape(h, w).astype(np.uint8)
        
        # Combine with person mask (both must agree)
        clothing_mask = clothing_by_color & person_mask
    else:
        # Fallback: just use dark areas within person
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, clothing_mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
        clothing_mask = cv2.bitwise_and(clothing_mask, person_mask * 255)
        clothing_mask = (clothing_mask > 0).astype(np.uint8)
    
    # Step 3: Clean up clothing mask
    kernel = np.ones((5,5), np.uint8)
    clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_CLOSE, kernel)
    clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
    
    # Remove small regions
    num_labels, labels_im = cv2.connectedComponents(clothing_mask)
    min_size = 500
    for i in range(1, num_labels):
        if np.sum(labels_im == i) < min_size:
            clothing_mask[labels_im == i] = 0
    
    clothing_pixels = clothing_mask.sum()
    print(f"Clothing pixels: {clothing_pixels} ({100*clothing_pixels/(h*w):.1f}%)")
    
    if clothing_pixels < 500:
        print("WARNING: Very small clothing region! Expanding...")
        # Use more aggressive threshold
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, clothing_mask = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
        clothing_mask = cv2.bitwise_and(clothing_mask, person_mask * 255)
        clothing_mask = (clothing_mask > 0).astype(np.uint8)
        clothing_mask = cv2.morphologyEx(clothing_mask, cv2.MORPH_CLOSE, np.ones((10,10), np.uint8))
    
    # Step 4: Edge refinement with distance transform
    dist = cv2.distanceTransform(clothing_mask.astype(np.uint8), cv2.DIST_L2, 5)
    dist = cv2.normalize(dist, None, 0, 1.0, cv2.NORM_MINMAX)
    
    # Feathered mask
    feather_radius = 20
    feather_kernel = cv2.getGaussianKernel(feather_radius * 2 + 1, feather_radius // 2)
    feather_2d = feather_kernel @ feather_kernel.T
    
    # Apply Gaussian blur to the mask for feathering
    feather_mask = cv2.GaussianBlur(clothing_mask.astype(np.float32), (feather_radius*2+1, feather_radius*2+1), feather_radius//2)
    
    # Step 5: Create white clothing
    result = img.copy().astype(np.float32)
    
    # Use original brightness for lighting
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Create white color with lighting preservation
    light = gray / 255.0
    target_r, target_g, target_b = target_color  # RGB format
    
    white_clothes = np.zeros_like(result)
    white_clothes[:,:,2] = np.clip(target_r * light, 0, 255)
    white_clothes[:,:,1] = np.clip(target_g * light, 0, 255)
    white_clothes[:,:,0] = np.clip(target_b * light, 0, 255)
    
    # Blend with feathering
    for c in range(3):
        result[:,:,c] = result[:,:,c] * (1 - feather_mask) + white_clothes[:,:,c] * feather_mask
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # Step 6: Light post-processing for natural look
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    result_pil = Image.fromarray(result_rgb)
    
    # Save
    result_pil.save(output_path, quality=95)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    precise_clothes_change(
        r"C:\temp\original_source.png",
        r"C:\temp\clothes_white_v4.jpg"
    )
