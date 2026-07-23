"""
全自动修图流水线 v2
监听QQ下载目录 → AI去斑(ModelScope) → RealESRGAN放大(ComfyUI) → 回图到QQ

启动方式：python retouch_pipeline.py [--daemon]
"""

import json
import os
import sys
import time
import uuid
import cv2
import numpy as np
import subprocess
import threading
import shutil
import glob
import urllib.request
import traceback

# ============ 配置 ============
WATCH_DIR = r"C:\Users\lfy20\.openclaw\qqbot\downloads"
OUTPUT_DIR = r"C:\temp\comfy_results"
COMFYWF = r"C:\ComfyUI\workflows\upscale_only.json"
COMFY_SCRIPT = os.path.join(os.path.dirname(__file__), "comfy_auto.py")
QUEUE_FILE = os.path.join(os.path.dirname(__file__), "retouch_queue.json")
PROCESSED_LOG = os.path.join(os.path.dirname(__file__), "processed_images.json")

# ModelScope模型路径
MODELSCOPE_MODEL = r"C:\Users\lfy20\.cache\modelscope\hub\models\damo\cv_unet_skin-retouching"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(WATCH_DIR, exist_ok=True)


def load_processed():
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r') as f:
            return json.load(f)
    return {"processed": []}


def save_processed(plist):
    with open(PROCESSED_LOG, 'w') as f:
        json.dump({"processed": plist}, f, indent=2)


def skin_retouch(input_path, output_path):
    """ModelScope AI皮肤精修"""
    print(f"[修图] AI去斑开始: {os.path.basename(input_path)}")
    
    from modelscope.outputs import OutputKeys
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks
    
    # 强制不用锁
    os.environ['MODELSCOPE_LOCK'] = 'false'
    
    pipe = pipeline(
        Tasks.skin_retouching,
        model=MODELSCOPE_MODEL,
        device='gpu'
    )
    
    img = cv2.imread(input_path)
    h, w = img.shape[:2]
    print(f"[修图] 原图: {w}x{h}")
    
    # 缩到2000以内（模型限制）
    scale = min(2000 / max(h, w), 1.0)
    if scale < 1:
        small = cv2.resize(img, (int(w*scale), int(h*scale)))
        print(f"[修图] 缩放到: {int(w*scale)}x{int(h*scale)}")
    else:
        small = img
    
    # 推理
    result = pipe(small)
    output_img = result[OutputKeys.OUTPUT_IMG]
    
    if isinstance(output_img, np.ndarray):
        # 转回BGR
        if output_img.shape[-1] == 3:
            output_img = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR)
        
        # 缩回原图大小
        if scale < 1:
            output_img = cv2.resize(output_img, (w, h))
        
        cv2.imwrite(output_path, output_img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        print(f"[修图] ✅ AI去斑完成: {output_path}")
        return True
    return False


def upscale(input_path, output_prefix):
    """ComfyUI RealESRGAN放大"""
    print(f"[修图] RealESRGAN放大: {os.path.basename(input_path)}")
    
    env = os.environ.copy()
    for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
        env.pop(k, None)
    
    result = subprocess.run(
        [sys.executable, COMFY_SCRIPT, input_path, COMFYWF],
        capture_output=True, text=True, timeout=900, env=env
    )
    
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and os.path.exists(line) and os.path.isfile(line):
                print(f"[修图] ✅ 放大完成: {line}")
                return line
    print(f"[修图] ❌ 放大失败")
    return None


def write_queue(original_name, input_path, output_paths):
    """写结果到队列，供主AI读并回图"""
    entry = {
        "original": original_name,
        "input_path": input_path,
        "output_paths": output_paths,
        "timestamp": time.time()
    }
    
    queue = []
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            queue = json.load(f)
    
    queue.append(entry)
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)
    
    print(f"[修图] ✅ 已入队列，等待AI回图")


def process_single_image(img_path):
    """处理单张图片的完整流程"""
    basename = os.path.basename(img_path)
    uid = uuid.uuid4().hex[:8]
    
    print(f"\n{'='*50}")
    print(f"[修图] 处理: {basename}")
    print(f"{'='*50}")
    
    try:
        # 1. AI去斑
        skin_path = os.path.join(OUTPUT_DIR, f"skin_{uid}.png")
        if not skin_retouch(img_path, skin_path):
            # 如果去斑失败，用原图
            skin_path = img_path
        
        # 2. ComfyUI放大
        upscaled_path = upscale(skin_path, uid)
        
        # 3. 入队列
        output_paths = [skin_path]
        if upscaled_path:
            output_paths.append(upscaled_path)
        
        write_queue(basename, img_path, output_paths)
        return True
        
    except Exception as e:
        print(f"[修图] ❌ 处理失败: {e}")
        traceback.print_exc()
        return False


def watch_loop():
    """监听目录"""
    processed = load_processed()
    processed_set = set(processed["processed"])
    
    print(f"\n{'='*50}")
    print(f"全自动修图流水线启动")
    print(f"监听目录: {WATCH_DIR}")
    print(f"已处理: {len(processed_set)} 张")
    print(f"{'='*50}\n")
    
    while True:
        try:
            exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
            images = set()
            for ext in exts:
                for p in glob.glob(os.path.join(WATCH_DIR, f"*{ext}")) + \
                        glob.glob(os.path.join(WATCH_DIR, f"*{ext.upper()}")):
                    images.add(p)
            
            for img_path in sorted(images):
                basename = os.path.basename(img_path)
                if basename in processed_set:
                    continue
                
                # 等文件写完
                try:
                    s1 = os.path.getsize(img_path)
                    time.sleep(1.5)
                    s2 = os.path.getsize(img_path)
                    if s1 != s2:
                        continue
                    if s1 < 1024:
                        continue  # 太小忽略
                except:
                    continue
                
                print(f"\n[监听] 新图: {basename}")
                process_single_image(img_path)
                processed_set.add(basename)
                save_processed(list(processed_set))
        
        except Exception as e:
            print(f"[监听] 异常: {e}")
            traceback.print_exc()
        
        time.sleep(3)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        watch_loop()
    elif len(sys.argv) >= 2:
        process_single_image(sys.argv[1])
    else:
        print("用法:")
        print("  python retouch_pipeline.py --daemon    # 后台监听模式")
        print("  python retouch_pipeline.py <图片路径>  # 单张处理")
