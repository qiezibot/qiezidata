# -*- coding: utf-8 -*-
"""Try loading skin retouching model directly with PyTorch"""
import os, cv2, numpy as np, torch, time
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

t0 = time.time()

model_dir = os.path.expanduser(r"~\.cache\modelscope\hub\models\damo\cv_unet_skin_retouching_torch")
pt_path = os.path.join(model_dir, "pytorch_model.pt")

print("Loading model:", pt_path)

# Check state dict keys
state = torch.load(pt_path, map_location="cpu", weights_only=True)
if isinstance(state, dict):
    print("Keys:", list(state.keys())[:10])
    print("Total keys:", len(state.keys()))
    
    # Check if there's a nested model
    if 'model' in state:
        print("Has 'model' key with type:", type(state['model']))
    if 'state_dict' in state:
        print("Has 'state_dict' key")
else:
    print("Type:", type(state))
    print("Shape:", state.shape if hasattr(state, 'shape') else 'N/A')
