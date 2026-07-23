"""测试ModelScope皮肤精修模型"""
import cv2, os
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

print("加载皮肤精修模型...")
pipe = pipeline(Tasks.skin_retouching, model='damo/cv_skin_retouching_torch')
print("模型加载成功 ✅")

img = cv2.imread(r'C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\ebc873ea-5136-42ce-9155-e62e21d2d988.png')
h, w = img.shape[:2]
print(f"原图: {w}x{h}")

# 模型对超大图有限制，缩到2000px
scale = 2000 / max(w, h)
if scale < 1:
    img_small = cv2.resize(img, (int(w*scale), int(h*scale)))
    print(f"缩放到: {int(w*scale)}x{int(h*scale)}")
else:
    img_small = img

print("开始推理...")
result = pipe(img_small)

is_dict = isinstance(result, dict)
print(f"结果类型: {type(result).__name__}")
if is_dict:
    for k in result.keys():
        v = result[k]
        if hasattr(v, 'shape'):
            print(f"  {k}: shape={v.shape}, dtype={v.dtype}")
        else:
            print(f"  {k}: {type(v).__name__}")
