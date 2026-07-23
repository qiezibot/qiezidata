#!/usr/bin/env python3
"""换衣服颜色 - 抠图后替换为指定颜色"""
import sys
import os
from rembg import remove
from PIL import Image, ImageFilter

def change_clothes_color(input_path, output_path, target_color=(255,255,255)):
    """抠出人物，将衣服区域替换为目标颜色"""
    print(f"读取图片: {input_path}")
    
    # 打开原图
    img = Image.open(input_path).convert("RGBA")
    
    # 抠图 - 得到人物蒙版
    print("正在抠图...")
    result = remove(img)
    
    # 分离通道
    r, g, b, a = result.split()
    
    # 创建一个白色或目标颜色的背景
    bg = Image.new("RGBA", img.size, target_color + (255,))
    
    # 将人物合成到目标颜色背景上
    composite = Image.composite(result, bg, a)
    
    # 保存
    composite = composite.convert("RGB")
    composite.save(output_path, quality=95)
    print(f"已保存: {output_path}")

if __name__ == "__main__":
    input_img = r"C:\Users\admin\.openclaw\qqbot\downloads\0719F4F9E276F93F9DF2E38254464081_1778730448209.png"
    output_img = r"C:\temp\clothes_white.jpg"
    
    # 白色
    change_clothes_color(input_img, output_img, target_color=(255, 255, 255))
    print("搞定！")
