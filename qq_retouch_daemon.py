"""
QQ自动修图守护脚本（完整版）
功能：监听QQ下载目录 → 新图自动修 → 回发修好的图到QQ
"""

import json
import os
import sys
import time
import subprocess
import glob
import threading
import shutil

# ============ 配置 ============
WATCH_DIR = r"C:\Users\lfy20\.openclaw\qqbot\downloads"
COMFY_SCRIPT = os.path.join(os.path.dirname(__file__), "comfy_auto.py")
CHECK_INTERVAL = 3  # 秒，快一点响应
PROCESSED_LOG = os.path.join(os.path.dirname(__file__), "processed_images.json")
OUTPUT_DIR = r"C:\temp\comfy_results"

os.makedirs(WATCH_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_processed():
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": []}

def save_processed(processed_list):
    with open(PROCESSED_LOG, 'w', encoding='utf-8') as f:
        json.dump({"processed": processed_list}, f, ensure_ascii=False, indent=2)

def watch_directory():
    processed = load_processed()
    processed_set = set(processed["processed"])
    
    print(f"[QQ修图] 开始监听: {WATCH_DIR}")
    print(f"[QQ修图] 已处理: {len(processed_set)} 张")
    
    while True:
        try:
            image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
            images = []
            for ext in image_exts:
                images.extend(glob.glob(os.path.join(WATCH_DIR, f"*{ext}")))
                images.extend(glob.glob(os.path.join(WATCH_DIR, f"*{ext.upper()}")))
            images = list(set(images))
            
            for img_path in images:
                basename = os.path.basename(img_path)
                if basename in processed_set:
                    continue
                
                # 等文件写入完成
                try:
                    size1 = os.path.getsize(img_path)
                    time.sleep(1)
                    size2 = os.path.getsize(img_path)
                    if size1 != size2:
                        continue
                except (OSError, FileNotFoundError):
                    continue
                
                print(f"\n[QQ修图] 发现新图: {basename}")
                process_image(img_path)
                
                processed_set.add(basename)
                save_processed(list(processed_set))
            
        except Exception as e:
            print(f"[QQ修图] 异常: {e}")
        
        time.sleep(CHECK_INTERVAL)

def process_image(img_path):
    basename = os.path.basename(img_path)
    
    try:
        env = os.environ.copy()
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'SOCKS5', 'socks5']:
            env.pop(key, None)
        
        result = subprocess.run(
            [sys.executable, COMFY_SCRIPT, img_path],
            capture_output=True, text=True, timeout=300, env=env
        )
        
        if result.returncode == 0:
            # 从输出中提取结果文件路径
            output_files = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and os.path.exists(line) and os.path.isfile(line):
                    output_files.append(line)
            
            if output_files:
                print(f"[QQ修图] 修好了: {basename}")
                # 这里会把结果写到一个队列文件，让主AI读取后发回QQ
                write_result_queue(basename, img_path, output_files)
            else:
                print(f"[QQ修图] 未找到结果文件")
        else:
            print(f"[QQ修图] 失败: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print(f"[QQ修图] 超时")
    except Exception as e:
        print(f"[QQ修图] 异常: {e}")

def write_result_queue(original_name, input_path, output_paths):
    """写结果到队列，供主AI读取后自动发回QQ"""
    queue_file = os.path.join(os.path.dirname(__file__), "retouch_queue.json")
    
    entry = {
        "original": original_name,
        "input_path": input_path,
        "output_paths": output_paths,
        "timestamp": time.time()
    }
    
    queue = []
    if os.path.exists(queue_file):
        try:
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
        except:
            queue = []
    
    queue.append(entry)
    with open(queue_file, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    
    print(f"[QQ修图] 已入队列: {output_paths}")

def clean_old_files():
    """清理旧文件（每小时）"""
    while True:
        try:
            now = time.time()
            for d in [OUTPUT_DIR, r"C:\ComfyUI\input"]:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        fpath = os.path.join(d, f)
                        if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > 7200:
                            try:
                                os.remove(fpath)
                            except:
                                pass
        except:
            pass
        time.sleep(3600)

if __name__ == "__main__":
    cleaner = threading.Thread(target=clean_old_files, daemon=True)
    cleaner.start()
    watch_directory()
