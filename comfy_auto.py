"""
ComfyUI 全自动修图脚本
功能：接收图片路径 → 提交到ComfyUI工作流 → 获取修好的图 → 返回结果路径
支持：CodeFormer精修 + RealESRGAN放大 + 去斑（频率分离）
"""

import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.error
import shutil

# 修复控制台编码
if sys.stdout.encoding != 'utf-8' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 屏蔽代理，避免SOCKS5冲突
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ.pop('SOCKS5', None)
os.environ.pop('socks5', None)

# ============ 配置 ============
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = r"C:\ComfyUI\output"
WORKFLOW_FILE = r"C:\ComfyUI\workflows\wedding_pro_codeformer.json"
CUSTOM_RESULT_DIR = r"C:\temp\comfy_results"

os.makedirs(CUSTOM_RESULT_DIR, exist_ok=True)

# ============ ComfyUI API 工具函数 ============

def queue_prompt(prompt_workflow):
    """提交工作流到ComfyUI"""
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_history(prompt_id):
    """获取工作流执行历史"""
    req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_image(filename, subfolder, folder_type="output"):
    """获取生成的图片"""
    params = f"?filename={filename}&subfolder={subfolder}&type={folder_type}"
    req = urllib.request.Request(f"{COMFYUI_URL}/view{params}")
    response = urllib.request.urlopen(req)
    return response.read()

def wait_for_completion(prompt_id, timeout=600, check_interval=2):
    """等待工作流完成"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            history = get_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(check_interval)
    raise TimeoutError(f"等待超时 {timeout}秒，prompt_id: {prompt_id}")

# ============ 核心修图函数 ============

def load_workflow(workflow_path):
    """加载工作流JSON模板"""
    with open(workflow_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def inject_image_path(workflow, image_path):
    """
    将图片路径注入工作流中的 LoadImage 节点
    因为ComfyUI的LoadImage只读 input/ 目录，我们需要先复制图片过去
    """
    # 确定目标路径
    input_dir = r"C:\ComfyUI\input"
    os.makedirs(input_dir, exist_ok=True)
    
    # 生成唯一文件名
    ext = os.path.splitext(image_path)[1] or ".jpg"
    target_name = f"auto_{uuid.uuid4().hex[:8]}{ext}"
    target_path = os.path.join(input_dir, target_name)
    
    # 复制图片到input目录
    shutil.copy2(image_path, target_path)
    
    # 注入到工作流中所有LoadImage节点
    for node_id, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = target_name
    
    return target_name

def run_retouch(input_image_path, workflow_path=None):
    """
    执行修图
    参数:
        input_image_path: 输入图片路径
        workflow_path: 工作流JSON路径（默认用CodeFormer版）
    返回:
        输出图片路径列表
    """
    if workflow_path is None:
        workflow_path = WORKFLOW_FILE
    
    # 检查图片是否存在
    if not os.path.exists(input_image_path):
        raise FileNotFoundError(f"图片不存在: {input_image_path}")
    
    # 加载工作流
    workflow = load_workflow(workflow_path)
    
    # 注入图片
    input_name = inject_image_path(workflow, input_image_path)
    print(f"[ComfyAuto] 已复制图片到input目录: {input_name}")
    
    # 提交
    result = queue_prompt(workflow)
    prompt_id = result.get("prompt_id", "")
    print(f"[ComfyAuto] 提交工作流成功, prompt_id: {prompt_id}")
    
    # 等待完成
    history = wait_for_completion(prompt_id)
    print(f"[ComfyAuto] 工作流完成")
    
    # 提取输出图片
    outputs = history.get("outputs", {})
    saved_images = []
    
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            for img in node_output["images"]:
                filename = img["filename"]
                subfolder = img.get("subfolder", "")
                folder_type = img.get("type", "output")
                image_data = get_image(filename, subfolder, folder_type)
                
                # 保存到自定义结果目录
                out_path = os.path.join(CUSTOM_RESULT_DIR, filename)
                with open(out_path, 'wb') as f:
                    f.write(image_data)
                saved_images.append(out_path)
                print(f"[ComfyAuto] 结果已保存: {out_path}")
    
    return saved_images


# ============ 命令行入口 ============

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python comfy_auto.py <图片路径> [工作流路径]")
        print("示例: python comfy_auto.py C:\\temp\\photo.jpg")
        sys.exit(1)
    
    input_path = sys.argv[1]
    wf_path = sys.argv[2] if len(sys.argv) > 2 else WORKFLOW_FILE
    
    try:
        results = run_retouch(input_path, wf_path)
        if results:
            print(f"\n✅ 修图完成！输出文件:")
            for r in results:
                print(f"   {r}")
        else:
            print("\n⚠️ 没有生成输出图片")
    except Exception as e:
        print(f"\n❌ 修图失败: {e}")
        sys.exit(1)
