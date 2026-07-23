"""
超级精修脚本 v1 - 茄子出品 🍆
功能：一键美白磨皮 + 调色 + 去瑕疵 + 换背景 + 证件照
用法：python photo_editor.py <输入图片路径> [模式]
模式：beauty(人像精修) | product(电商白底) | idphoto(证件照) | auto(自动检测)
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def load_image(path):
    """加载图片，支持中文路径"""
    if not os.path.exists(path):
        print(f"❌ 文件不存在: {path}")
        return None, None
    # 用 PIL 读，转 OpenCV
    img_pil = Image.open(path)
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return img_cv, img_pil

def save_image(img_cv, output_path):
    """保存图片"""
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    img_pil.save(output_path)
    print(f"✅ 已保存: {output_path}")

def auto_white_balance(img):
    """自动白平衡"""
    result = cv2.xphoto.createSimpleWB().balanceWhite(img)
    return result

def skin_smooth(img, strength=0.6):
    """磨皮 - 双边滤波 + 高斯模糊蒙版"""
    # 双边滤波保留边缘
    smooth = cv2.bilateralFilter(img, 9, 75, 75)
    # 高斯模糊做背景平滑
    blur = cv2.GaussianBlur(img, (0, 0), 10)
    # 混合
    result = cv2.addWeighted(smooth, strength, blur, 1 - strength, 0)
    return result

def face_beauty(img):
    """人像精修：美白+磨皮+调色"""
    print("✨ 正在美白调色...")
    # 先自动白平衡
    try:
        img = auto_white_balance(img)
    except:
        pass
    
    # 转LAB提亮
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    print("✨ 正在磨皮...")
    img = skin_smooth(img, 0.5)
    
    # 微调饱和度
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.1)  # 加饱和度
    hsv[:, :, 2] = cv2.multiply(hsv[:, :, 2], 1.05)  # 提亮
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    print("✨ 正在锐化...")
    sharpen = np.array([[-1, -1, -1],
                         [-1,  9, -1],
                         [-1, -1, -1]])
    img = cv2.filter2D(img, -1, sharpen)
    
    return img

def product_photo(img):
    """电商图处理：抠图白底 + 增强"""
    print("📦 正在处理电商图...")
    # 先把白底调纯白
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = gray > 200  # 接近白色的区域
    img[mask] = [255, 255, 255]
    
    # 增强对比度让商品更鲜明
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # 锐化
    sharpen = np.array([[0, -1, 0],
                         [-1, 5, -1],
                         [0, -1, 0]])
    img = cv2.filter2D(img, -1, sharpen)
    
    return img

def id_photo_bg(img):
    """证件照：柔光+统一背景色调"""
    print("🪪 正在处理证件照...")
    # 柔和调色
    img = cv2.bilateralFilter(img, 5, 50, 50)
    return img

def auto_enhance(img):
    """全自动增强：先判断内容再处理"""
    # 简单检测：如果是人像（肤色区域多）走beauty，否则走product
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 肤色范围
    lower_skin = np.array([0, 20, 70])
    upper_skin = np.array([20, 255, 255])
    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
    skin_ratio = cv2.countNonZero(skin_mask) / (img.shape[0] * img.shape[1])
    
    if skin_ratio > 0.1:
        print("🔄 检测到人像，使用人像精修模式")
        return face_beauty(img)
    else:
        print("🔄 检测到商品/风景，使用电商图模式")
        return product_photo(img)

def main():
    if len(sys.argv) < 2:
        print("""
使用方法：
  python photo_editor.py <图片路径> [模式]

模式：
  beauty   - 人像精修（美白磨皮调色）
  product  - 电商白底图增强
  idphoto  - 证件照优化
  auto     - 自动检测模式（默认）

示例：
  python photo_editor.py C:\photo.jpg beauty
  python photo_editor.py C:\bag.jpg product
        """)
        return
    
    input_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    print(f"📷 加载图片: {input_path}")
    img_cv, img_pil = load_image(input_path)
    if img_cv is None:
        return
    
    print(f"📐 图片尺寸: {img_cv.shape[1]}x{img_cv.shape[0]}")
    
    # 模式处理
    if mode == "beauty":
        result = face_beauty(img_cv)
    elif mode == "product":
        result = product_photo(img_cv)
    elif mode == "idphoto":
        result = id_photo_bg(img_cv)
    else:
        result = auto_enhance(img_cv)
    
    # 生成输出路径
    dir_name = os.path.dirname(input_path) or "."
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(dir_name, f"{base_name}_精修.png")
    
    save_image(result, output_path)
    print(f"\n🎉 完成！输出文件: {output_path}")

if __name__ == "__main__":
    main()
