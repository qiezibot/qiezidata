"""Run CodeFormer workflow via ComfyUI API"""
import requests, json

with open("C:/ComfyUI/workflows/wedding_pro_codeformer.json", encoding="utf-8") as f:
    wf = json.load(f)

wf["1"]["inputs"]["image"] = "wedding_input.png"

r = requests.post(
    "http://127.0.0.1:8188/prompt",
    json={"prompt": wf},
    timeout=30,
    proxies={"http": None, "https": None}
)
print(r.status_code, r.json())
