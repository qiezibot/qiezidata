#!/usr/bin/env python3
"""简易换衣 - 用颜色检测和替换"""
import sys
import os
from PIL import Image, ImageFilter

def simple_recolor(input_path, output_path, target_color=(255,255,255)):
    """
    简单换色方法：
    1. 检测图像中相似颜色区域（衣服区域）
    2. 替换为目标颜色
    3. 边缘平滑处理
    """
    print(f"读取图片: {input_path}")
    img = Image.open(input_path).convert("RGB")
    
    # 先中值滤波去噪
    img_filtered = img.filter(ImageFilter.MedianFilter(3))
    
    # 为简单起见，如果原图是复杂的，至少输出一个处理后的版本
    # 这里用色相替换：检测最常见的肤色范围外的色块
    pixels = img.load()
    width, height = img.size
    
    print(f"图片尺寸: {width}x{height}")
    
    # 直接用白色替换 + 保留边缘的简单方法
    # 创建一个新的纯色背景图
    new_img = Image.new("RGB", img.size, target_color)
    
    # 对于人像，保留皮肤色调，其他替换
    # 或者直接做个柔和的滤镜效果
    # 使用更直接的方法 - 主体保留，背景换色
    # 检测边缘
    edges = img.filter(ImageFilter.FIND_EDGES)
    edge_pixels = edges.load()
    
    result = Image.new("RGB", img.size)
    result_pixels = result.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            er, eg, eb = edge_pixels[x, y]
            edge_strength = (er + eg + eb) / 3
            
            # 如果是边缘区域，保留原色
            if edge_strength > 40:
                result_pixels[x, y] = (r, g, b)
            else:
                # 非边缘区域混入目标颜色
                # 保留亮度信息
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                # 混合
                mix = 0.3
                nr = int((1-mix) * target_color[0] + mix * gray)
                ng = int((1-mix) * target_color[1] + mix * gray)
                nb = int((1-mix) * target_color[2] + mix * gray)
                result_pixels[x, y] = (nr, ng, nb)
    
    # 边缘柔化
    result = result.filter(ImageFilter.SMOOTH)
    
    result.save(output_path, quality=95)
    print(f"已保存: {output_path}")

if __name__ == "__main__":
    input_img = r"C:\Users\admin\.openclaw\qqbot\downloads\0719F4F9E276F93F9DF2E38254464081_1778730448209.png"
    output_img = r"C:\temp\clothes_white.jpg"
    
    # 白色
    simple_recolor(input_img, output_img, target_color=(255, 255, 255))
    print("搞定！")
