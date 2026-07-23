# -*- coding: utf-8 -*-
"""Load ModelScope skin retouching model directly"""
import cv2
import numpy as np
import os
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# Try loading the model directly
import torch
import json

model_dir = os.path.expanduser(r"~\.cache\modelscope\hub\models\damo\cv_unet_skin_retouching_torch")

# Check what's in the model directory
if os.path.exists(model_dir):
    print("Model dir contents:")
    for root, dirs, files in os.walk(model_dir):
        level = root.replace(model_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:30]:
            print(f"{subindent}{file}")
        if len(files) > 30:
            print(f"{subindent}... and {len(files)-30} more files")
            break
else:
    print("Model dir NOT FOUND at:", model_dir)
