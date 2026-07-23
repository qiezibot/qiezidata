#!/usr/bin/env python3
"""Send an image through ComfyUI wedding retouch workflow and save the result."""
import urllib.request
import json
import sys
import time
import os

INPUT_IMAGE = "wedding_input.png"
WORKFLOW_FILE = "C:/ComfyUI/workflows/wedding_retouch_basic.json"
OUTPUT_DIR = "C:/ComfyUI/output"

# Load workflow
with open(WORKFLOW_FILE, encoding="utf-8") as f:
    wf = json.load(f)

# Set input image
for n in wf["nodes"]:
    if n["type"] == "LoadImage":
        n["widgets"]["image"] = INPUT_IMAGE
    if n["type"] == "SaveImage":
        n["inputs"]["filename_prefix"] = "wedding_output"
    if n["type"] == "FaceRestore":
        n["inputs"]["fidelity"] = 0.8

body = json.dumps(wf).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8188/prompt",
    data=body,
    headers={"Content-Type": "application/json"}
)

print("Submitting workflow...")
r = urllib.request.urlopen(req, timeout=30)
result = json.loads(r.read().decode("utf-8"))
print(f"Prompt ID: {result.get('prompt_id', 'unknown')}")

# Wait for completion
prompt_id = result.get("prompt_id", "")
print("Waiting for processing...")
time.sleep(2)

# Check history
try:
    hr = urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=10)
    history = json.loads(hr.read().decode("utf-8"))
    print(f"History keys: {list(history.keys())}")
except Exception as e:
    print(f"History check: {e}")

# List output files
print("\nOutput files:")
for f in os.listdir(OUTPUT_DIR):
    if f.startswith("wedding_output"):
        print(f"  {f} ({os.path.getsize(os.path.join(OUTPUT_DIR, f)) / 1024:.0f} KB)")
