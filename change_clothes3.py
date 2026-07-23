#!/usr/bin/env python3
"""用 rembg 抠图 + 替换衣物颜色为白色"""
from PIL import Image, ImageFilter

def simple_rembg_and_recolor(input_path, output_path):
    print(f"读取图片: {input_path}")
    img = Image.open(input_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    
    # 用颜色检测来识别"衣服"区域（非肤色区域且饱和度较高）
    # 创建衣服蒙版
    clothes_mask = Image.new("L", img.size, 0)
    cm = clothes_mask.load()
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 10:
                cm[x, y] = 0
                continue
            
            # 归一化RGB
            total = r + g + b + 0.001
            rr, gg, bb = r/total, g/total, b/total
            
            # 简单肤色检测（约简）
            # 如果R>95且G>40且B>20且max-min>15且R>G且R>B -> 可能是肤色
            is_skin = (r > 95 and g > 40 and b > 20 and 
                       max(r,g,b) - min(r,g,b) > 15 and
                       abs(r-g) > 15 and r > g and r > b)
            
            if is_skin:
                cm[x, y] = 0  # 保留肤色
            else:
                # 检测是否为衣服（不是太暗或太亮）
                brightness = (r + g + b) / 3
                if 30 < brightness < 240:
                    cm[x, y] = 255  # 标记为衣服
    
    # 平滑蒙版
    clothes_mask = clothes_mask.filter(ImageFilter.MedianFilter(7))
    clothes_mask = clothes_mask.filter(ImageFilter.SMOOTH_MORE)
    
    # 创建白色衣服图像
    white_clothes = Image.new("RGBA", img.size, (255, 255, 255, 255))
    
    # 合成：衣服区域用白色，其他保持原样
    result = Image.composite(white_clothes, img, clothes_mask)
    
    result = result.convert("RGB")
    result.save(output_path, quality=95)
    print(f"已保存: {output_path}")
    print("请查看效果，可能需要调整参数")

if __name__ == "__main__":
    simple_rembg_and_recolor(
        r"C:\Users\admin\.openclaw\qqbot\downloads\0719F4F9E276F93F9DF2E38254464081_1778730448209.png",
        r"C:\temp\clothes_white_v2.jpg"
    )
