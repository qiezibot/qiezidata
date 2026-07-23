"""
生成一张附图样图：紫底背景+内容展示
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = r"E:\openclaw压缩包及启动教程\u-claw\portable\data\.openclaw\workspace\covers_en"
W, H = 800, 800

# 紫底背景
img = Image.new('RGB', (W, H), (0,0,0))
draw = ImageDraw.Draw(img)

# 渐变紫色背景
for y in range(H):
    progress = y / H
    r = int(100 + progress * 30)
    g = int(30 + progress * 20)
    b = int(140 + progress * 20)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# 左上蓝色光晕
for r2 in range(250, 0, -1):
    alpha = int(25 * (1 - r2/250))
    cx2, cy2 = 100, 100
    draw.ellipse([cx2-r2, cy2-r2, cx2+r2, cy2+r2], fill=(80, 180, 255, alpha) if alpha > 0 else None)

# 右下橙色光晕
for r2 in range(300, 0, -1):
    alpha = int(20 * (1 - r2/300))
    cx2, cy2 = 700, 700
    draw.ellipse([cx2-r2, cy2-r2, cx2+r2, cy2+r2], fill=(255, 180, 80, alpha) if alpha > 0 else None)

# 毛玻璃卡片层
card_layer = Image.new('RGBA', (W, H), (0,0,0,0))
card_draw = ImageDraw.Draw(card_layer)
card_draw.rounded_rectangle([50, 50, 750, 750], radius=22, fill=(255,255,255,18), outline=(200,150,255,100), width=2)
img_rgba = img.convert('RGBA')
final = Image.alpha_composite(img_rgba, card_layer)
final_rgb = Image.new('RGB', final.size, (0,0,0))
final_rgb.paste(final, (0,0), final)
draw = ImageDraw.Draw(final_rgb)

# 字体
try:
    title_font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 44)
    sub_font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 30)
    item_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
    small_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
except:
    title_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 44)
    sub_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 30)
    item_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 24)
    small_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)

# 标题
draw.text((W//2, 130), "📦 资料包内容清单", fill=(255,255,255), font=title_font, anchor="mm")

# 分割线1
draw.line([(W//2-200, 170), (W//2+200, 170)], fill=(255,200,100), width=2)

# 内容区域：模拟目录列表
content_items = [
    ("📕", "  《零基础入门》——70页图文教程"),
    ("📗", "  DeepSeek/ChatGPT实战案例"),
    ("📘", "  AI绘画提示词宝库（500条）"),
    ("📙", "  AI办公自动化模板合集"),
    ("📔", "  日赚100+实操案例详解"),
    ("", ""),
]

y = 210
for icon, text in content_items:
    if text == "":
        y += 10
        continue
    # 左侧图标区域
    draw.text((120, y), icon, fill=(255,200,100), font=item_font if "70" not in text else sub_font, anchor="lm")
    draw.text((170, y), text, fill=(220,220,240), font=item_font, anchor="lm")
    y += 45

# 分割线2
y += 10
draw.line([(W//2-200, y), (W//2+200, y)], fill=(255,200,100), width=2)

# 底部功能说明区
features = [
    "✅ 百度网盘发货，拍下自动发送",
    "✅ 资料永久有效，持续更新",
    "✅ 支持手机/电脑在线查看",
    "✅ 适合零基础到进阶全阶段",
]

y += 30
for feat in features:
    draw.text((W//2, y), feat, fill=(200,255,200), font=sub_font, anchor="mm")
    y += 50

# 底部标签
y += 10
draw.text((W//2, y), "—— 橘子网游 · 品质保证 ——", fill=(255,200,100), font=small_font, anchor="mm")

# 保存
fpath = os.path.join(OUTPUT_DIR, "sample_detail_Zidi.jpg")
final_rgb.save(fpath, quality=95)
print(f"Saved: {fpath}")
