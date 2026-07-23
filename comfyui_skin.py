# -*- coding: utf-8 -*-
"""
ComfyUI SkinRetouchingPM + FaceSkinPM skin mask
Only retouch skin area, keep original color/eyes/mouth
"""
import json, os, time, requests, sys, io, base64
from PIL import Image
import numpy as np

t0 = time.time()

# Load input image
img = Image.open(r"C:\ComfyUI\input\wedding_input.png").convert("RGB")
w, h = img.size
print("Image: {}x{}".format(w, h))

# Save as base64 for ComfyUI
buffered = io.BytesIO()
img.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

# Build workflow nodes
# Based on SkinRetouchingPM node taking (IMAGE,) and FaceSkinPM
workflow = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "wedding_input.png"}},
    "2": {"class_type": "FaceSkinPM", "inputs": {
        "image": ("1", 0),
        "blur_edge": 32,
        "blur_threshold": 32
    }},
    "3": {"class_type": "SkinRetouchingPM", "inputs": {
        "image": ("1", 0)
    }},
    # Blend: original * (1 - skin_mask) + retouched * skin_mask
    "4": {"class_type": "ImageBlend", "inputs": {
        "image1": ("1", 0),
        "image2": ("3", 0),
        "mask": ("2", 0),
        "blending_mode": "normal",
        "opacity": 100
    }},
    "5": {"class_type": "SaveImage", "inputs": {
        "images": ("4", 0),
        "filename_prefix": "wedding_skin"
    }}
}

prompt = {"prompt": workflow}
print("Sending to ComfyUI...")

try:
    r = requests.post("http://127.0.0.1:8188/prompt", json=prompt, 
                      proxies={"http": None, "https": None}, timeout=10)
    resp = r.json()
    pid = resp.get("prompt_id", "unknown")
    print("Prompt ID:", pid)
except Exception as e:
    print("ComfyUI API error:", e)
    sys.exit(1)

# Wait for completion
import time as ttime
for i in range(120):
    ttime.sleep(2)
    try:
        hr = requests.get("http://127.0.0.1:8188/history/{}".format(pid),
                         proxies={"http": None, "https": None}, timeout=5)
        if hr.status_code == 200 and hr.json().get(pid, {}).get("status", {}).get("completed") is True:
            print("Completed!")
            break
    except:
        pass
    if i % 10 == 0:
        print("Waiting... {}s".format(i*2))
else:
    print("Timeout!")

# Find output
output_dir = r"C:\ComfyUI\output"
output_files = [f for f in os.listdir(output_dir) if f.startswith("wedding_skin")]
if output_files:
    latest = max([os.path.join(output_dir, f) for f in output_files], key=os.path.getmtime)
    print("Output:", latest)
    
    # Copy to standard location
    import shutil
    shutil.copy(latest, r"C:\ComfyUI\output\wedding_output_final.png")
    
    # Preview
    preview = Image.open(latest)
    preview.thumbnail((1280, 1280))
    preview.save(r"C:\temp\tts\wedding_preview.jpg", "JPEG", quality=90)
    print("Preview saved")
else:
    print("No output found!")
    # List outputs
    print(os.listdir(output_dir))

print("Total time: {:.1f}s".format(time.time() - t0))
