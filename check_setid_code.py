import urllib.request, json, base64

TOKEN = "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"
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "push-script"}

req_src = urllib.request.Request("https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py", headers=headers)
r = urllib.request.urlopen(req_src)
data = json.loads(r.read())
raw = base64.b64decode(data["content"])

idx = raw.find(b"set_user_id")
chunk = raw[idx:idx+800]
for i, line in enumerate(chunk.split(b"\r\n"), 1):
    decoded = line.decode("utf-8", errors="replace")[:120]
    if decoded.strip():
        print(f"{i}: {decoded}")

# Also check the conflict check - old_id might not exist as a check against new_id being the same
# Print more of the function
idx2 = raw.find(b"set_user_id")
end = raw.find(b"\n\n\n@app.on", idx2)
if end < 0:
    end = min(len(raw), idx2 + 1500)
full_func = raw[idx2:end]
print("\n=== FULL FUNCTION ===")
print(full_func.decode("utf-8", errors="replace"))
