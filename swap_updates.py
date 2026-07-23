import urllib.request, json, base64

TOKEN = "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"
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "push-script"}

req_src = urllib.request.Request("https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py", headers=headers)
r = urllib.request.urlopen(req_src)
data = json.loads(r.read())
sha = data["sha"]
raw_bytes = base64.b64decode(data["content"])
content = raw_bytes.decode("utf-8")

print(f"Current SHA: {sha}")
print(f"File length: {len(raw_bytes)} bytes")

# Find the two UPDATE statements
users_marker = b"UPDATE users SET id="
files_marker = b"UPDATE files SET user_id="

users_pos = raw_bytes.find(users_marker)
files_pos = raw_bytes.find(files_marker)

print(f"users UPDATE at byte {users_pos}")
print(f"files UPDATE at byte {files_pos}")

# Find the surrounding lines
# Go back to start of the line (before "await conn.execute")
for start_pos in range(users_pos - 5, users_pos - 200, -1):
    if raw_bytes[start_pos:start_pos+2] == b"\r\n":
        start_pos += 2
        break
else:
    start_pos = users_pos - 100
    
# Go forward to after the files line (find next \r\n that's followed by another \r\n)
end_pos = files_pos + 150
for end_pos in range(files_pos + 60, files_pos + 250):
    if raw_bytes[end_pos:end_pos+4] == b"\r\n\r\n":
        end_pos += 2  # keep one \r\n
        break
    elif raw_bytes[end_pos:end_pos+2] == b"\r\n" and raw_bytes[end_pos+2:end_pos+4] == b"\r\n":
        end_pos += 2
        break

section = raw_bytes[start_pos:end_pos]
print(f"\nSection bytes ({start_pos}-{end_pos}):")
print(section.decode("utf-8", errors="replace"))

# Find the exact lines to swap
lines = section.split(b"\r\n")
print(f"\nLines in section: {len(lines)}")
for i, l in enumerate(lines):
    print(f"  [{i}]: {l}")

# Swap users and files lines
users_idx_in_section = None
files_idx_in_section = None
for i, l in enumerate(lines):
    if b"UPDATE users SET id=" in l:
        users_idx_in_section = i
    if b"UPDATE files SET user_id=" in l:
        files_idx_in_section = i

if users_idx_in_section is not None and files_idx_in_section is not None:
    print(f"\nSwapping lines {users_idx_in_section} and {files_idx_in_section}")
    lines[users_idx_in_section], lines[files_idx_in_section] = lines[files_idx_in_section], lines[users_idx_in_section]
    
    # Rebuild section
    new_section = b"\r\n".join(lines)
    print(f"\nNew section:")
    print(new_section.decode("utf-8", errors="replace"))
    
    # Replace in raw bytes
    new_raw_bytes = raw_bytes.replace(section, new_section, 1)
    
    # Verify
    new_content = new_raw_bytes.decode("utf-8")
    compile(new_content, "test", "exec")
    print("\nPython syntax: VALID")
    
    # Push
    body = json.dumps({
        "message": "fix: set_id swap UPDATE order (files first, then users)",
        "content": base64.b64encode(new_raw_bytes).decode(),
        "sha": sha,
    }).encode()
    
    put_req = urllib.request.Request(
        "https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py",
        data=body, method="PUT",
        headers={**headers, "Content-Type": "application/json"}
    )
    put_r = urllib.request.urlopen(put_req)
    resp = json.loads(put_r.read())
    print(f"New SHA: {resp['content']['sha']}")
    print("Push successful!")
else:
    print(f"Could not find both lines. users={users_idx_in_section}, files={files_idx_in_section}")
