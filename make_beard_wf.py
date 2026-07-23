"""ComfyUI去胡子工作流：LoadImage → FaceRestoreCFWithModel(只遮罩区域) → SaveImage
用CodeFormer只修补胡须区域，保留其他部分不变
"""

import json
import os

wf = {
    "10": {  # 加载图片
        "inputs": {"image": "", "upload": "image"},
        "class_type": "LoadImage",
        "_meta": {"title": "输入图片"}
    },
    "11": {  # 加载模型
        "inputs": {"model_name": "codeformer-v0.1.0.pth"},
        "class_type": "FaceRestoreModelLoader",
        "_meta": {"title": "CodeFormer模型"}
    },
    "12": {  # CodeFormer修脸
        "inputs": {
            "facerestore_model": ["11", 0],
            "image": ["10", 0],
            "fidelity": 0.6,
            "codeformer_upscale": 1,
            "face_align": "original",
            "bg_upsampler": "None"
        },
        "class_type": "FaceRestoreCFWithModel",
        "_meta": {"title": "CodeFormer修脸"}
    },
    "13": {  # 保存修好的图
        "inputs": {
            "images": ["12", 0],
            "filename_prefix": "beard_codeformer_"
        },
        "class_type": "SaveImage",
        "_meta": {"title": "CodeFormer输出"}
    },
    # 以下是混合节点：原图和CodeFormer结果用遮罩混合
    "14": {  # 加载遮罩图
        "inputs": {"image": "", "upload": "image"},
        "class_type": "LoadImage",
        "_meta": {"title": "加载遮罩(白=胡子区域)"}
    },
    "15": {  # 遮罩取反或二值化
        "inputs": {
            "images": ["14", 0],
            "channel": "red"
        },
        "class_type": "ImageToMask",
        "_meta": {"title": "遮罩转mask"}
    },
    "16": {  # 用遮罩混合原图和修好图
        "inputs": {
            "sources": [["10", 0], ["12", 0]],
            "masks": ["15", 0]
        },
        "class_type": "JoinImageWithAlpha",
        "_meta": {"title": "混合原图和修图"}
    },
    "17": {  # 保存混合结果
        "inputs": {
            "images": ["16", 0],
            "filename_prefix": "beard_blend_"
        },
        "class_type": "SaveImage",
        "_meta": {"title": "混合输出"}
    }
}

path = r"C:\ComfyUI\workflows\beard_remove_codeformer.json"
with open(path, 'w') as f:
    json.dump(wf, f, indent=2)

print(f"✅ 工作流已创建: {path}")
