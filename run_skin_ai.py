"""用下载好的ModelScope皮肤精修模型直接跑"""
import os, sys
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import cv2, uuid

OUTPUT_DIR = r"C:\temp\comfy_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

img_path = r'C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\ebc873ea-5136-42ce-9155-e62e21d2d988.png'

print("加载皮肤精修模型 (damo/cv_unet_skin-retouching)...")
pipe = pipeline(Tasks.skin_retouching, model='damo/cv_unet_skin-retouching')
print("模型加载成功 ✅")

img = cv2.imread(img_path)
h, w = img.shape[:2]
print(f"原图: {w}x{h}")

# 缩放到2000以内（模型有尺寸限制）
scale = 2000 / max(w, h)
if scale < 1:
    img_small = cv2.resize(img, (int(w*scale), int(h*scale)))
    print(f"缩放到: {int(w*scale)}x{int(h*scale)}")
else:
    img_small = img

print("推理中...")
result = pipe(img_small)
print(f"结果类型: {type(result).__name__}")

# 处理输出
if isinstance(result, dict):
    keys = list(result.keys())
    print(f"Keys: {keys}")
    # 尝试找到图像输出
    for k in keys:
        v = result[k]
        if hasattr(v, 'shape'):
            print(f"  {k}: shape={v.shape}, dtype={v.dtype}")
            uid = uuid.uuid4().hex[:8]
            out_path = os.path.join(OUTPUT_DIR, f"skin_ai_{uid}.jpg")
            cv2.imwrite(out_path, v, [cv2.IMWRITE_JPEG_QUALITY, 95])
            print(f"  已保存: {out_path}")
        else:
            print(f"  {k}: {type(v).__name__}, value={str(v)[:100]}")
elif hasattr(result, 'shape'):
    uid = uuid.uuid4().hex[:8]
    out_path = os.path.join(OUTPUT_DIR, f"skin_ai_{uid}.jpg")
    cv2.imwrite(out_path, result, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"已保存: {out_path}")
else:
    print(f"结果: {str(result)[:200]}")

print("完成")
