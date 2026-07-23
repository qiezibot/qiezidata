import json

# 只放大的工作流 — 不入CodeFormer
wf = {
    "3": {
        "inputs": {"image": "", "upload": "image"},
        "class_type": "LoadImage",
        "_meta": {"title": "输入图片"}
    },
    "4": {
        "inputs": {"model_name": "RealESRGAN_x4plus.pth"},
        "class_type": "UpscaleModelLoader",
        "_meta": {"title": "放大模型"}
    },
    "5": {
        "inputs": {
            "upscale_model": ["4", 0],
            "image": ["3", 0]
        },
        "class_type": "ImageUpscaleWithModel",
        "_meta": {"title": "放大4x"}
    },
    "6": {
        "inputs": {
            "images": ["5", 0],
            "filename_prefix": "upscaled_"
        },
        "class_type": "SaveImage",
        "_meta": {"title": "保存"}
    }
}

with open(r'C:\ComfyUI\workflows\upscale_only.json', 'w') as f:
    json.dump(wf, f, indent=2)

print("✅ upscale_only.json 已创建")
