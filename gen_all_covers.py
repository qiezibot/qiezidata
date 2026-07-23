"""
生成8个商品 x 2个模板 = 16张封面
使用之前定稿的设计风格生成，替换掉之前乱搞的canvas简易版
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

OUTPUT_DIR = r"C:\Users\lfy20\Downloads\covers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 字体
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"  # 微软雅黑粗体
FONT_REG = "C:/Windows/Fonts/msyh.ttc"     # 微软雅黑常规

# 商品列表（标题, 副标题, 列表项1, 列表项2, 列表项3, 列表项4）
PRODUCTS = [
    ("AI入门实战", "零基础到赚钱", "DeepSeek·ChatGPT实战", "AI写作·AI绘画·AI办公", "日赚100+实战案例", "拍下发网盘·永久有效"),
    ("AI绘画提示词", "5000+精选", "Midjourney·SD全风格", "人物·风景·插画·3D", "输入即出大片", "拍下发网盘·永久有效"),
    ("小红书运营", "从0到博主变现", "爆款笔记·快速涨粉", "接广谈判·变现攻略", "全流程拆解", "拍下发网盘·永久有效"),
    ("小红书运营", "0基础做博主", "爆款·涨粉·接广", "变现全流程拆解", "手把手教学", "拍下发网盘·永久有效"),
    ("视频剪辑教程", "剪映+PR入门到精通", "剪辑·特效·调色", "卡点视频·字幕制作", "自媒体必备技能", "拍下发网盘·永久有效"),
    ("简历PPT模板", "500套精选通用", "简历模板·PPT模板", "全行业覆盖", "职场求职必备", "拍下发网盘·永久有效"),
    ("AI副业赚钱", "10种赚钱方法", "零基础也能做", "AI变现案例合集", "日赚100+不是梦", "拍下发网盘·永久有效"),
    ("学习资料素材包", "超值学习大礼包", "AI·运营·剪辑全覆盖", "一次搞定所有技能", "持续更新中", "拍下发网盘·永久有效"),
]

SIZE = 800

def make_tech_blue_canvas():
    """科技蓝简洁版背景"""
    img = Image.new('RGB', (SIZE, SIZE), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 深蓝渐变背景 - 从左上到右下
    colors = [(10, 20, 60), (20, 40, 100), (30, 60, 140), (15, 30, 80)]
    for y in range(SIZE):
        progress = y / SIZE
        r = int(10 + progress * 20)
        g = int(20 + progress * 40)
        b = int(60 + progress * 80)
        draw.line([(0, y), (SIZE, y)], fill=(r, g, b))
    
    # 左上角柔和光晕
    for r in range(200, 0, -1):
        alpha = int(30 * (1 - r/200))
        cx, cy = 150, 150
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(100, 150, 255, alpha) if alpha > 0 else None)
    
    # 右下角暖色光晕
    for r in range(250, 0, -1):
        alpha = int(20 * (1 - r/250))
        cx, cy = 650, 650
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 200, 100, alpha) if alpha > 0 else None)
    
    # 优雅弧线装饰
    draw.arc([-100, 100, 300, 500], 180, 270, fill=(80, 120, 220, 100), width=3)
    draw.arc([400, -50, 900, 400], 0, 90, fill=(80, 120, 220, 100), width=3)
    
    return img, draw

def make_purple_canvas():
    """紫底鲜艳版背景"""
    img = Image.new('RGB', (SIZE, SIZE), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 紫色渐变背景
    for y in range(SIZE):
        progress = y / SIZE
        r = int(100 + progress * 30)
        g = int(30 + progress * 20)
        b = int(140 + progress * 20)
        draw.line([(0, y), (SIZE, y)], fill=(r, g, b))
    
    # 左上蓝色光晕
    for r in range(250, 0, -1):
        alpha = int(25 * (1 - r/250))
        cx, cy = 100, 100
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(80, 180, 255, alpha) if alpha > 0 else None)
    
    # 右下橙色光晕
    for r in range(300, 0, -1):
        alpha = int(20 * (1 - r/300))
        cx, cy = 700, 700
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 180, 80, alpha) if alpha > 0 else None)
    
    # 右上粉色光晕
    for r in range(200, 0, -1):
        alpha = int(20 * (1 - r/200))
        cx, cy = 650, 150
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 100, 200, alpha) if alpha > 0 else None)
    
    return img, draw

def draw_tech_card(draw, title, subtitle, items):
    """科技蓝版：半透明卡片+简洁科技感"""
    # 半透明白色卡片
    cx, cy = SIZE//2, SIZE//2
    card_w, card_h = 600, 500
    card_x1 = cx - card_w//2
    card_y1 = cy - card_h//2 + 20
    card_x2 = cx + card_w//2
    card_y2 = cy + card_h//2 + 20
    
    # 画圆角矩形卡片
    try:
        from PIL import ImageDraw as ID
        card_layer = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
        card_draw = ImageDraw.Draw(card_layer)
        card_draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=20, fill=(255,255,255,20), outline=(255,255,255,60), width=2)
        # 合并
        bg = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
        bg.paste(card_layer, (0,0), card_layer)
        return bg
    except:
        draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=(40, 50, 90, 180), outline=(100, 150, 255), width=2)

def draw_purple_card(draw, title, subtitle, items):
    """紫底版：毛玻璃效果卡片"""
    cx, cy = SIZE//2, SIZE//2
    card_w, card_h = 600, 500
    card_x1 = cx - card_w//2
    card_y1 = cy - card_h//2 + 20
    card_x2 = cx + card_w//2
    card_y2 = cy + card_h//2 + 20
    
    try:
        card_layer = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
        card_draw = ImageDraw.Draw(card_layer)
        # 毛玻璃效果卡片 (半透明白)
        card_draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=20, fill=(255,255,255,30), outline=(255,200,255,80), width=2)
        bg = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
        bg.paste(card_layer, (0,0), card_layer)
        return bg
    except:
        draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=(80, 30, 120, 180), outline=(200, 150, 255), width=2)

def render_text(draw, title, subtitle, items, style="purple"):
    """在draw上渲染文字"""
    try:
        title_font = ImageFont.truetype(FONT_BOLD, 56)
        sub_font = ImageFont.truetype(FONT_REG, 28)
        item_font = ImageFont.truetype(FONT_REG, 32)
        small_font = ImageFont.truetype(FONT_REG, 20)
    except:
        title_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 56)
        sub_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 28)
        item_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 32)
        small_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
    
    cx = SIZE // 2
    
    # 标题颜色
    if style == "purple":
        title_color = (255, 255, 255)
        sub_color = (200, 180, 255)
        item_color = (255, 255, 255)
        tag_color = (255, 200, 100)
    else:
        title_color = (180, 220, 255)
        sub_color = (150, 200, 255)
        item_color = (200, 220, 240)
        tag_color = (100, 200, 255)
    
    # 标题
    draw.text((cx, 200), title, fill=title_color, font=title_font, anchor="mm")
    
    # 副标题 - 标题下方
    draw.text((cx, 270), subtitle, fill=sub_color, font=sub_font, anchor="mm")
    
    # 分割线
    draw.line([(cx-150, 300), (cx+150, 300)], fill=tag_color, width=2)
    
    # 列表项
    y_start = 340
    for i, item in enumerate(items):
        y = y_start + i * 55
        # 小圆点
        draw.ellipse([cx-120, y-6, cx-108, y+6], fill=tag_color)
        # 文字
        draw.text((cx-95, y), item, fill=item_color, font=item_font, anchor="lm")
    
    # 底部装饰文字
    draw.text((cx, 700), "橘子网游", fill=tag_color, font=small_font, anchor="mm")

def make_tech_card_overlay():
    """生成科技蓝卡片叠加层带毛玻璃效果"""
    layer = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
    card_draw = ImageDraw.Draw(layer)
    
    cx, cy = SIZE//2, SIZE//2
    card_w, card_h = 600, 500
    card_x1 = cx - card_w//2
    card_y1 = cy - card_h//2 + 20
    card_x2 = cx + card_w//2
    card_y2 = cy + card_h//2 + 20
    
    # 毛玻璃效果：半透明白底 + 边框发蓝光
    card_draw.rounded_rectangle([card_x1-1, card_y1-1, card_x2+1, card_y2+1], radius=22, fill=(255,255,255,15), outline=(100,180,255,120), width=2)
    
    return layer

def make_purple_card_overlay():
    """生成紫底卡片叠加层带毛玻璃效果"""
    layer = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
    card_draw = ImageDraw.Draw(layer)
    
    cx, cy = SIZE//2, SIZE//2
    card_w, card_h = 600, 500
    card_x1 = cx - card_w//2
    card_y1 = cy - card_h//2 + 20
    card_x2 = cx + card_w//2
    card_y2 = cy + card_h//2 + 20
    
    # 毛玻璃效果卡片
    card_draw.rounded_rectangle([card_x1-1, card_y1-1, card_x2+1, card_y2+1], radius=22, fill=(255,255,255,18), outline=(200,150,255,100), width=2)
    
    return layer

def generate_cover(title, subtitle, items, style="purple"):
    """生成单张封面"""
    if style == "purple":
        bg, draw = make_purple_canvas()
        overlay = make_purple_card_overlay()
    else:
        bg, draw = make_tech_blue_canvas()
        overlay = make_tech_card_overlay()
    
    # Convert bg to RGBA for composition
    bg_rgba = bg.convert('RGBA')
    # Overlay the card
    final = Image.alpha_composite(bg_rgba, overlay)
    
    # Render text on final
    final_rgb = Image.new('RGB', final.size, (0,0,0))
    final_rgb.paste(final, (0,0), final)
    draw = ImageDraw.Draw(final_rgb)
    
    # 字体
    try:
        title_font = ImageFont.truetype(FONT_BOLD, 56)
        sub_font = ImageFont.truetype(FONT_REG, 28)
        item_font = ImageFont.truetype(FONT_REG, 32)
        small_font = ImageFont.truetype(FONT_REG, 20)
    except:
        title_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 56)
        sub_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 28)
        item_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 32)
        small_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
    
    cx = SIZE // 2
    
    if style == "purple":
        title_color = (255, 255, 255)
        sub_color = (200, 180, 255)
        item_color = (255, 255, 255)
        tag_color = (255, 200, 100)
    else:
        title_color = (180, 220, 255)
        sub_color = (150, 200, 255)
        item_color = (200, 220, 240)
        tag_color = (100, 200, 255)
    
    # 标题
    draw.text((cx, 200), title, fill=title_color, font=title_font, anchor="mm")
    # 副标题
    draw.text((cx, 270), subtitle, fill=sub_color, font=sub_font, anchor="mm")
    # 分割线
    draw.line([(cx-150, 300), (cx+150, 300)], fill=tag_color, width=2)
    # 列表项
    y_start = 340
    for i, item in enumerate(items):
        y = y_start + i * 55
        draw.ellipse([cx-120, y-6, cx-108, y+6], fill=tag_color)
        draw.text((cx-95, y), item, fill=item_color, font=item_font, anchor="lm")
    # 底部
    draw.text((cx, 700), "橘子网游", fill=tag_color, font=small_font, anchor="mm")
    
    return final_rgb

# 生成封面
for idx, (title, subtitle, *items) in enumerate(PRODUCTS):
    # 紫底版
    img_zidi = generate_cover(title, subtitle, items, style="purple")
    fname_zidi = f"{idx+1:02d}_{title}_紫底.jpg"
    img_zidi.save(os.path.join(OUTPUT_DIR, fname_zidi), quality=95)
    print(f"✅ {fname_zidi}")
    
    # 科技蓝版
    img_keji = generate_cover(title, subtitle, items, style="tech")
    fname_keji = f"{idx+1:02d}_{title}_科技蓝.jpg"
    img_keji.save(os.path.join(OUTPUT_DIR, fname_keji), quality=95)
    print(f"✅ {fname_keji}")

print(f"\n✅ 全部生成完毕！共{len(PRODUCTS)*2}张封面")
print(f"📁 输出目录：{OUTPUT_DIR}")
