"""
批量生成全部8个商品：主图 + 2张附图 = 24张
全用紫底模板统一风格
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = r"C:\Users\lfy20\Downloads\covers_all"
os.makedirs(OUTPUT_DIR, exist_ok=True)

W, H = 800, 800

# ---- 商品数据 ----
PRODUCTS = [
    {
        "name": "AI入门实战",
        "title": "AI入门实战",
        "subtitle": "零基础到赚钱",
        "items": ["DeepSeek·ChatGPT实战", "AI写作·AI绘画·AI办公", "日赚100+实战案例", "拍下发网盘·永久有效"],
        "detail_title": "📦 资料包内容清单",
        "detail_items": [
            ("📕", "《零基础入门》70页图文教程"),
            ("📗", "DeepSeek/ChatGPT实战案例"),
            ("📘", "AI绘画提示词宝库500条"),
            ("📙", "AI办公自动化模板合集"),
            ("📔", "日赚100+实操案例详解"),
        ],
        "detail_features": [
            "✅ 百度网盘发货，拍下自动发送",
            "✅ 资料永久有效，持续更新",
            "✅ 支持手机/电脑在线查看",
        ],
        "detail_title2": "🔥 为什么选我们",
        "detail_items2": [
            ("💎", "持续更新，一次购买终身学习"),
            ("🎯", "从零基础到赚钱全流程"),
            ("🚀", "已帮助1000+学员入门AI"),
            ("⚡", "实战为主，拒绝空谈理论"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
    {
        "name": "AI绘画提示词",
        "title": "AI绘画提示词",
        "subtitle": "5000+精选",
        "items": ["Midjourney·SD全风格", "人物·风景·插画·3D", "输入即出大片", "拍下发网盘·永久有效"],
        "detail_title": "🎨 5000+精选提示词",
        "detail_items": [
            ("🎭", "人物肖像/写实/二次元"),
            ("🏔️", "风景/建筑/科幻场景"),
            ("🖼️", "插画/油画/水墨风格"),
            ("🎮", "3D/游戏/C4D渲染"),
            ("✏️", "艺术字体/Logo设计"),
        ],
        "detail_features": [
            "✅ Midjourney+S+D全平台通用",
            "✅ 输入即出大片效果",
            "✅ 持续更新最新风格",
        ],
        "detail_title2": "💡 使用方法",
        "detail_items2": [
            ("1️⃣", "收到网盘链接下载文件"),
            ("2️⃣", "打开提示词分类文件"),
            ("3️⃣", "复制提示词到AI绘画工具"),
            ("4️⃣", "调整参数生成大片"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
    {
        "name": "小红书运营",
        "title": "小红书运营",
        "subtitle": "从0到博主变现",
        "items": ["爆款笔记·快速涨粉", "接广谈判·变现攻略", "全流程拆解", "拍下发网盘·永久有效"],
        "detail_title": "📖 课程内容大纲",
        "detail_items": [
            ("📝", "账号定位+人设打造"),
            ("🔥", "爆款笔记写作公式"),
            ("📈", "快速涨粉技巧"),
            ("💰", "接广谈判+报价策略"),
            ("🛒", "开店带货变现流程"),
        ],
        "detail_features": [
            "✅ 从0到博主全套教程",
            "✅ 实际案例拆解分析",
            "✅ 零基础也能学会",
        ],
        "detail_title2": "🎯 适合人群",
        "detail_items2": [
            ("👤", "想通过小红书赚钱的新手"),
            ("👩‍💼", "已做账号但涨粉慢的博主"),
            ("💰", "想开拓副业收入的上班族"),
            ("🎓", "学生党想赚生活费"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
    {
        "name": "小红书运营02",
        "title": "小红书运营",
        "subtitle": "0基础做博主",
        "items": ["爆款·涨粉·接广", "变现全流程拆解", "手把手教学", "拍下发网盘·永久有效"],
        "detail_title": "📖 你将学到什么",
        "detail_items": [
            ("📝", "账号从0到1搭建"),
            ("🔥", "爆款笔记写作技巧"),
            ("📈", "粉丝增长核心方法"),
            ("💰", "变现渠道全攻略"),
            ("🏪", "小红书开店流程"),
        ],
        "detail_features": [
            "✅ 零基础也能做博主",
            "✅ 手把手实操教学",
            "✅ 看完就能开始做",
        ],
        "detail_title2": "🎯 课程亮点",
        "detail_items2": [
            ("💡", "真实案例拆解每个步骤"),
            ("⏱️", "每天30分钟就能操作"),
            ("📱", "手机就能完成全部操作"),
            ("💪", "不懂也能快速上手"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
    {
        "name": "视频剪辑教程",
        "title": "视频剪辑教程",
        "subtitle": "剪映+PR入门到精通",
        "items": ["剪辑·特效·调色", "卡点视频·字幕制作", "自媒体必备技能", "拍下发网盘·永久有效"],
        "detail_title": "🎬 教程内容包含",
        "detail_items": [
            ("✂️", "剪映从入门到精通"),
            ("🎞️", "Pr专业剪辑全流程"),
            ("✨", "特效制作+转场技巧"),
            ("🎨", "调色理论+实操"),
            ("🎵", "卡点视频制作"),
        ],
        "detail_features": [
            "✅ 剪映+PR双软件教学",
            "✅ 从零开始包教包会",
            "✅ 做自媒体必备技能",
        ],
        "detail_title2": "💡 学完你能做什么",
        "detail_items2": [
            ("🎥", "Vlog/日常视频剪辑"),
            ("📱", "抖音/快手短视频"),
            ("📺", "B站/YouTube视频"),
            ("💼", "接单做视频剪辑赚钱"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
    {
        "name": "简历PPT模板",
        "title": "简历PPT模板",
        "subtitle": "500套精选通用",
        "items": ["简历模板·PPT模板", "全行业覆盖", "职场求职必备", "拍下发网盘·永久有效"],
        "detail_title": "📁 模板内容包含",
        "detail_items": [
            ("📄", "简历模板200+套"),
            ("📊", "PPT模板200+套"),
            ("💼", "求职面试资料包"),
            ("📝", "自我评价范文"),
            ("🎓", "应届生专属模板"),
        ],
        "detail_features": [
            "✅ 覆盖互联网/金融/教育等行业",
            "✅ 双倍高效制作简历和PPT",
            "✅ 精美设计直接下载使用",
        ],
        "detail_title2": "🎯 适合场景",
        "detail_items2": [
            ("👔", "找工作/换工作"),
            ("🎓", "应届生求职面试"),
            ("📊", "工作汇报/述职PPT"),
            ("🏢", "商务展示/项目路演"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
    {
        "name": "AI副业赚钱",
        "title": "AI副业赚钱",
        "subtitle": "10种赚钱方法",
        "items": ["零基础也能做", "AI变现案例合集", "日赚100+不是梦", "拍下发网盘·永久有效"],
        "detail_title": "💰 10种AI赚钱方法",
        "detail_items": [
            ("✍️", "AI写作接单赚钱"),
            ("🎨", "AI绘画卖图变现"),
            ("📹", "AI视频批量制作"),
            ("📊", "AI办公外包服务"),
            ("🎓", "AI知识付费教学"),
        ],
        "detail_features": [
            "✅ 全部真实可操作项目",
            "✅ 每个方法都有案例拆解",
            "✅ 零基础也能上手",
        ],
        "detail_title2": "📈 学员反馈",
        "detail_items2": [
            ("💰", "小王：做AI绘画月入5000+"),
            ("✍️", "小李：AI写作日赚200+"),
            ("🎬", "小张：AI视频一条爆款赚3000+"),
            ("📚", "小刘：卖AI教程月入过万"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
    {
        "name": "学习资料包",
        "title": "学习资料包",
        "subtitle": "超值学习大礼包",
        "items": ["AI·运营·剪辑全覆盖", "一次搞定所有技能", "持续更新中", "拍下发网盘·永久有效"],
        "detail_title": "📚 超值资料包内容",
        "detail_items": [
            ("🤖", "AI工具使用教程合集"),
            ("📱", "自媒体运营宝典"),
            ("🎬", "视频剪辑从入门到精通"),
            ("📄", "简历PPT模板大礼包"),
            ("💼", "副业赚钱实操指南"),
        ],
        "detail_features": [
            "✅ 一份资料搞定所有技能",
            "✅ AI+运营+剪辑一站式学习",
            "✅ 价值999+的精品学习包",
        ],
        "detail_title2": "🔥 资料包优势",
        "detail_items2": [
            ("🎁", "一次购买终身学习"),
            ("🔄", "持续更新不收额外费用"),
            ("📱", "手机电脑都能看"),
            ("🚚", "百度网盘发货随时下载"),
        ],
        "detail_features2": [
            "✅ 拍下即发 · 无需等待",
            "✅ 永久更新 · 终身有效",
        ],
    },
]

def draw_background(draw):
    """画紫底渐变背景"""
    for y in range(H):
        p = y / H
        r = int(100 + p * 30)
        g = int(30 + p * 20)
        b = int(140 + p * 20)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    # 左上蓝色光晕
    for r2 in range(250, 0, -1):
        a = int(25 * (1 - r2/250))
        draw.ellipse([100-r2, 100-r2, 100+r2, 100+r2], fill=(80, 180, 255, a) if a > 0 else None)
    # 右下橙色光晕
    for r2 in range(300, 0, -1):
        a = int(20 * (1 - r2/300))
        draw.ellipse([700-r2, 700-r2, 700+r2, 700+r2], fill=(255, 180, 80, a) if a > 0 else None)

def add_card():
    """返回毛玻璃卡片叠加层"""
    layer = Image.new('RGBA', (W, H), (0,0,0,0))
    cd = ImageDraw.Draw(layer)
    cd.rounded_rectangle([50, 50, 750, 750], radius=22, fill=(255,255,255,18), outline=(200,150,255,100), width=2)
    return layer

def get_fonts():
    try:
        title_font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 56)
        sub_font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 28)
        item_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 32)
        dt_font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 44)
        dt_sub = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 30)
        dt_item = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
        dt_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    except:
        sf = "C:/Windows/Fonts/simhei.ttf"
        title_font = ImageFont.truetype(sf, 56)
        sub_font = ImageFont.truetype(sf, 28)
        item_font = ImageFont.truetype(sf, 32)
        dt_font = ImageFont.truetype(sf, 44)
        dt_sub = ImageFont.truetype(sf, 30)
        dt_item = ImageFont.truetype(sf, 24)
        dt_small = ImageFont.truetype(sf, 20)
    return title_font, sub_font, item_font, dt_font, dt_sub, dt_item, dt_small

def make_main_cover(product):
    """生成主图封面"""
    img = Image.new('RGB', (W, H), (0,0,0))
    draw = ImageDraw.Draw(img)
    draw_background(draw)
    
    # 卡片
    card = add_card()
    img_rgba = img.convert('RGBA')
    final = Image.alpha_composite(img_rgba, card)
    final_rgb = Image.new('RGB', final.size, (0,0,0))
    final_rgb.paste(final, (0,0), final)
    draw = ImageDraw.Draw(final_rgb)
    
    tf, sf, itf, _, _, _, _ = get_fonts()
    cx = W // 2
    
    # 标题
    draw.text((cx, 200), product["title"], fill=(255,255,255), font=tf, anchor="mm")
    # 副标题
    draw.text((cx, 270), product["subtitle"], fill=(200,180,255), font=sf, anchor="mm")
    # 分割线
    draw.line([(cx-150, 300), (cx+150, 300)], fill=(255,200,100), width=2)
    # 列表
    for i, item in enumerate(product["items"]):
        y = 340 + i * 55
        draw.ellipse([cx-120, y-6, cx-108, y+6], fill=(255,200,100))
        draw.text((cx-95, y), item, fill=(255,255,255), font=itf, anchor="lm")
    # 底部
    draw.text((cx, 720), "橘子网游", fill=(255,200,100), font=sf, anchor="mm")
    
    return final_rgb

def make_detail(product, detail_num=1):
    """生成附图"""
    img = Image.new('RGB', (W, H), (0,0,0))
    draw = ImageDraw.Draw(img)
    draw_background(draw)
    
    card = add_card()
    img_rgba = img.convert('RGBA')
    final = Image.alpha_composite(img_rgba, card)
    final_rgb = Image.new('RGB', final.size, (0,0,0))
    final_rgb.paste(final, (0,0), final)
    draw = ImageDraw.Draw(final_rgb)
    
    _, _, _, dt_font, dt_sub, dt_item, dt_small = get_fonts()
    cx = W // 2
    
    if detail_num == 1:
        # 第一张附图 - 内容清单
        draw.text((cx, 120), product["detail_title"], fill=(255,255,255), font=dt_font, anchor="mm")
        draw.line([(cx-200, 160), (cx+200, 160)], fill=(255,200,100), width=2)
        
        y = 200
        for icon, text in product["detail_items"]:
            draw.text((130, y), icon, fill=(255,200,100), font=dt_sub, anchor="lm")
            draw.text((180, y), text, fill=(220,220,240), font=dt_item, anchor="lm")
            y += 50
        
        draw.line([(cx-200, y+10), (cx+200, y+10)], fill=(255,200,100), width=2)
        y += 40
        for feat in product["detail_features"]:
            draw.text((cx, y), feat, fill=(200,255,200), font=dt_sub, anchor="mm")
            y += 50
        
        draw.text((cx, 740), "橘子网游 · 品质保证", fill=(255,200,100), font=dt_small, anchor="mm")
    else:
        # 第二张附图 - 亮点/卖点
        draw.text((cx, 120), product["detail_title2"], fill=(255,255,255), font=dt_font, anchor="mm")
        draw.line([(cx-200, 160), (cx+200, 160)], fill=(255,200,100), width=2)
        
        y = 210
        for icon, text in product["detail_items2"]:
            draw.text((130, y), icon, fill=(255,200,100), font=dt_sub, anchor="lm")
            draw.text((180, y), text, fill=(220,220,240), font=dt_item, anchor="lm")
            y += 55
        
        draw.line([(cx-200, y+10), (cx+200, y+10)], fill=(255,200,100), width=2)
        y += 40
        for feat in product["detail_features2"]:
            draw.text((cx, y), feat, fill=(200,255,200), font=dt_sub, anchor="mm")
            y += 50
        
        draw.text((cx, 740), "橘子网游 · 品质保证", fill=(255,200,100), font=dt_small, anchor="mm")
    
    return final_rgb

# 批量生成
count = 0
for prod in PRODUCTS:
    name = prod["name"].replace(" ", "_")
    
    # 主图
    main_img = make_main_cover(prod)
    f1 = os.path.join(OUTPUT_DIR, f"{name}_主图.jpg")
    main_img.save(f1, quality=95)
    count += 1
    print(f"[OK] 主图 {name}")
    
    # 附图1
    d1 = make_detail(prod, 1)
    f2 = os.path.join(OUTPUT_DIR, f"{name}_附图1.jpg")
    d1.save(f2, quality=95)
    count += 1
    print(f"[OK] 附图1 {name}")
    
    # 附图2
    d2 = make_detail(prod, 2)
    f3 = os.path.join(OUTPUT_DIR, f"{name}_附图2.jpg")
    d2.save(f3, quality=95)
    count += 1
    print(f"[OK] 附图2 {name}")

print(f"\n✅ 全部生成完毕！共{count}张图片")
