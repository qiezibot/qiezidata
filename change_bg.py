# -*- coding: utf-8 -*-
"""
一站式换背景工具
用法: python change_bg.py <输入图片路径> [背景描述]
背景描述: 默认"海边沙滩"
"""

import sys
import os
from PIL import Image
from rembg import remove
import io
import warnings
warnings.filterwarnings("ignore")

# 设置控制台编码
if sys.stdout.encoding.lower() == 'gbk':
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def change_background(input_path, bg_description="海边沙滩"):
    """抠图 + 换背景"""
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # 1. 读图 + 抠图
    print("[1/4] 读取图片: " + input_path)
    with open(input_path, 'rb') as f:
        img_data = f.read()
    
    print("[2/4] AI抠图中... (rembg)")
    output_data = remove(img_data)
    
    # 保存抠好的图（透明PNG）
    cutout_path = os.path.join(output_dir, base_name + "_cutout.png")
    with open(cutout_path, 'wb') as f:
        f.write(output_data)
    print("     抠图结果: " + cutout_path)
    
    # 2. 预置背景颜色
    backgrounds = {
        "海边":     ((135, 206, 235), (255, 228, 196)),
        "沙滩":     ((135, 206, 235), (255, 228, 196)),
        "海边沙滩": ((135, 206, 235), (255, 228, 196)),
        "大海":     ((0, 119, 190), (135, 206, 250)),
        "森林":     ((34, 139, 34), (0, 100, 0)),
        "草原":     ((124, 252, 0), (0, 128, 0)),
        "城市":     ((169, 169, 169), (105, 105, 105)),
        "室内":     ((255, 248, 220), (245, 245, 220)),
        "日落":     ((255, 99, 71), (255, 218, 185)),
        "夜晚":     ((25, 25, 112), (0, 0, 0)),
    }
    
    print("[3/4] 生成背景: " + bg_description)
    
    top_colors = backgrounds.get("海边沙滩")
    for key, colors in backgrounds.items():
        if key in bg_description:
            top_colors = colors
            break
    
    # 3. 用PIL生成渐变背景
    cutout = Image.open(cutout_path).convert("RGBA")
    w, h = cutout.size
    
    bg = Image.new("RGBA", (w, h), top_colors[0])
    
    for y in range(h):
        ratio = y / h
        r = int(top_colors[0][0] * (1-ratio) + top_colors[1][0] * ratio)
        g = int(top_colors[0][1] * (1-ratio) + top_colors[1][1] * ratio)
        b = int(top_colors[0][2] * (1-ratio) + top_colors[1][2] * ratio)
        for x in range(w):
            bg.putpixel((x, y), (r, g, b, 255))
    
    # 4. 合成
    print("[4/4] 合成图片...")
    result = Image.alpha_composite(bg, cutout)
    
    result_path = os.path.join(output_dir, base_name + "_" + bg_description[:4] + ".png")
    result.save(result_path)
    print("完成! 输出: " + result_path)
    
    return result_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python change_bg.py <图片路径> [背景描述]")
        print("背景描述例子: 海边沙滩, 森林, 城市, 日落, 草原...")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print("文件不存在: " + input_file)
        sys.exit(1)
    
    bg_desc = sys.argv[2] if len(sys.argv) > 2 else "海边沙滩"
    change_background(input_file, bg_desc)
