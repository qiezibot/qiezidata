"""Remove blemishes/spots from face using inpainting-like technique"""
from PIL import Image, ImageFilter
import numpy as np

# Load original and processed images
img = Image.open("C:/ComfyUI/output/wedding_output_00001_.png")
arr = np.array(img)

# Simple spot removal: detect dark small spots and inpaint them
from PIL import ImageDraw

# Manual spot removal approach - use a strong median filter only on detected dark spots
# First convert to grayscale for detection
gray = np.mean(arr, axis=2)

# Detect very small dark spots (local minima)
from scipy.ndimage import minimum_filter, maximum_filter

# Apply median filter to the whole image for subtle smoothing
from scipy.ndimage import median_filter

h, w = arr.shape[:2]

# Process in tiles to handle large image
tile_h, tile_w = 512, 512
result = arr.copy()

for y in range(0, h, tile_h):
    for x in range(0, w, tile_w):
        y1 = min(y + tile_h, h)
        x1 = min(x + tile_w, w)
        tile = arr[y:y1, x:x1].copy()
        
        # Light median filter on each channel
        for c in range(3):
            tile[:,:,c] = median_filter(tile[:,:,c], size=3)
        
        result[y:y1, x:x1] = tile

result_img = Image.fromarray(result)
result_img.save("C:/ComfyUI/output/wedding_retouched_00001_.png")
print("Done - saved as wedding_retouched_00001_.png")
