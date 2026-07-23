#!/usr/bin/env python3
"""更加精细的换衣方案 - 使用PIL进行色彩范围选择和蒙版处理"""
from PIL import Image, ImageFilter, ImageEnhance
import colorsys

def hsl_change_clothes(input_path, output_path):
    """基于HSL色彩空间的衣服区域检测和替换"""
    img = Image.open(input_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    
    # 先模糊，减少噪点
    blurred = img.filter(ImageFilter.GaussianBlur(2))
    bp = blurred.load()
    
    mask = Image.new("L", img.size, 0)
    mp = mask.load()
    
    # 统计颜色分布来猜测衣服颜色
    color_samples = {}
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            r, g, b, a = bp[x, y]
            if a < 10: continue
            # 量化颜色
            qr, qg, qb = r//32*32, g//32*32, b//32*32
            key = (qr, qg, qb)
            color_samples[key] = color_samples.get(key, 0) + 1
    
    # 找到最常出现的非肤色非背景颜色 = 衣服
    # 排序最常出现的颜色
    sorted_colors = sorted(color_samples.items(), key=lambda x: -x[1])
    
    # 排除最可能的主色（背景/皮肤）
    total_pixels = (w//4) * (h//4)
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = blurred.getpixel((x, y))
            if a < 10:
                mp[x, y] = 0
                continue
            
            # HSL转换
            h_val, s_val, v_val = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            # 检测非肤色（H在0-0.1和0.9-1之间是红色调=肤色范围）
            # 非肤色且非纯黑纯白，饱和度适中
            is_skin = (0 < h_val < 0.12) and (s_val > 0.15) and (v_val > 0.3)
            is_bg = (s_val < 0.1) or (v_val > 0.95) or (v_val < 0.05)
            
            if not is_skin and not is_bg and s_val > 0.12:
                mp[x, y] = 255  # 衣服区域
            else:
                mp[x, y] = 0
    
    # 形态学操作：扩张+侵蚀来填充空洞
    mask = mask.filter(ImageFilter.MaxFilter(5))  # 扩张
    mask = mask.filter(ImageFilter.MinFilter(7))  # 侵蚀去掉噪点
    mask = mask.filter(ImageFilter.MaxFilter(3))  # 再扩张一点
    mask = mask.filter(ImageFilter.SMOOTH_MORE)
    
    # 创建白色衣服
    white_outfit = Image.new("RGBA", img.size, (255, 255, 255, 255))
    
    # 合成
    result = Image.composite(white_outfit, img, mask)
    
    # 边缘羽化
    result = result.convert("RGB")
    result.save(output_path, quality=95)
    print(f"已保存: {output_path}")
    print("提示：如果效果不理想，请告知我调整参数")

if __name__ == "__main__":
    hsl_change_clothes(
        r"C:\Users\admin\.openclaw\qqbot\downloads\0719F4F9E276F93F9DF2E38254464081_1778730448209.png",
        r"C:\temp\clothes_white_final.jpg"
    )
