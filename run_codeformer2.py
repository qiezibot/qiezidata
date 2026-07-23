"""Run CodeFormer workflow via ComfyUI API - correct node IDs"""
import requests, json

with open("C:/ComfyUI/workflows/wedding_pro_codeformer.json", encoding="utf-8") as f:
    wf = json.load(f)

# Set input image on LoadImage node (id: 4)
wf["4"]["inputs"]["image"] = "wedding_input.png"

r = requests.post(
    "http://127.0.0.1:8188/prompt",
    json={"prompt": wf},
    timeout=300,
    proxies={"http": None, "https": None}
)
print(r.status_code, r.json())
