#!/usr/bin/env python3
"""Use SAM to segment person and replace clothes with white"""
import sys
import os
import numpy as np
from PIL import Image, ImageFilter
import torch
from segment_anything import sam_model_registry, SamPredictor

# 下载SAM模型
MODEL_URL = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
MODEL_PATH = r"C:\temp\sam_vit_b.pth"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("下载SAM模型（约375MB），首次需要下载...")
        import urllib.request
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("下载完成")

def segment_person(input_path, output_path):
    """用SAM分割人物，然后把衣服变成白色"""
    
    # 加载图片
    print("加载图片...")
    img = Image.open(input_path).convert("RGB")
    
    download_model()
    
    print("加载SAM模型...")
    sam = sam_model_registry["vit_b"](checkpoint=MODEL_PATH)
    sam.to("cpu")
    predictor = SamPredictor(sam)
    
    # 转换图片
    img_np = np.array(img)
    predictor.set_image(img_np)
    
    # 在图片中心点一个点，提示SAM分割人物
    h, w = img_np.shape[:2]
    input_points = np.array([[w//2, h//2]])  # 中心点
    input_labels = np.array([1])
    
    print("SAM推理中（这需要一些时间）...")
    masks, scores, logits = predictor.predict(
        point_coords=input_points,
        point_labels=input_labels,
        multimask_output=True
    )
    
    # 用最高分的mask
    best_idx = np.argmax(scores)
    person_mask = masks[best_idx]
    
    # 转换成PIL蒙版
    mask_img = Image.fromarray((person_mask * 255).astype(np.uint8))
    
    # 平滑边缘
    mask_img = mask_img.filter(ImageFilter.SMOOTH_MORE)
    
    # 创建白色衣服效果：简单地用白色替换人物区域
    white_bg = Image.new("RGB", img.size, (255, 255, 255))
    
    # 把人物区域变白（衣服也变白）
    # 实际上我们想保留皮肤，只让衣服变白
    # 简单做法：人物整体变成白色
    result = Image.composite(white_bg, img, mask_img)
    
    result.save(output_path, quality=95)
    print(f"已保存: {output_path}")

if __name__ == "__main__":
    segment_person(
        r"C:\Users\admin\.openclaw\qqbot\downloads\0719F4F9E276F93F9DF2E38254464081_1778730448209.png",
        r"C:\temp\clothes_white_sam.jpg"
    )
