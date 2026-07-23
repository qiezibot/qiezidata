import urllib.request, json, base64

TOKEN = "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"
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "push-script"}

req_src = urllib.request.Request("https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py", headers=headers)
r = urllib.request.urlopen(req_src)
data = json.loads(r.read())
sha = data["sha"]
raw_bytes = base64.b64decode(data["content"])

print(f"Current SHA: {sha}")

# Find the set_user_id function and replace its UPDATE logic
# Current logic (2 separate awaits):
#   await conn.execute('UPDATE files SET user_id=$1 WHERE user_id=$2', new_id, uid)
#   await conn.execute('UPDATE users SET id=$1 WHERE id=$2', new_id, uid)
# 
# New logic: multi-statement
#   await conn.execute('''
#     INSERT INTO users (id, username, display_name, role, password_hash, created_at)
#     VALUES ($1, '_tmp_', '_tmp_', 'user', '', NOW())
#     ON CONFLICT DO NOTHING;
#     UPDATE files SET user_id=$1 WHERE user_id=$2;
#     UPDATE users SET id=$1 WHERE id=$2;
#     DELETE FROM users WHERE id=$3 AND username='_tmp_';
#   ''', new_id, uid, uid)
#   (where $3 is the old uid)

# Find the files UPDATE and users UPDATE lines
old_marker = b"UPDATE files SET user_id="
new_marker = b"UPDATE users SET id="

old_pos = raw_bytes.find(old_marker)
new_pos = raw_bytes.find(new_marker, old_pos)

print(f"Found files UPDATE at {old_pos}")
print(f"Found users UPDATE at {new_pos}")

# Find the return line after both
ret_marker = b"return JSONResponse"
ret_pos = raw_bytes.find(ret_marker, new_pos)
print(f"Found return at {ret_pos}")

# Build new SQL: use 3 params: new_id, old_uid(uid), old_uid_for_cleanup
new_sql = b"""        # Transaction: create placeholder, swap files, swap user, cleanup
        await conn.execute('''
            INSERT INTO users (id, username, display_name, role, password_hash, created_at)
            VALUES ($1, $$_tmp_$$, $$_tmp_$$, $$user$$, $$_tmp_$$, NOW())
            ON CONFLICT DO NOTHING;
            UPDATE files SET user_id=$1 WHERE user_id=$2;
            UPDATE users SET id=$1 WHERE id=$2;
            DELETE FROM users WHERE id=$3 AND username=$$_tmp_$$;
        ''', new_id, uid, uid)"""

# Replace from "await conn.execute('UPDATE files..." to just before "return JSONResponse"
# We need to identify the exact block
files_line_start = raw_bytes.rfind(b"\r\n", 0, old_pos) + 2
ret_line_start = raw_bytes.rfind(b"\r\n", 0, ret_pos)

old_block = raw_bytes[files_line_start:ret_line_start]
print(f"\nOld block ({files_line_start}-{ret_line_start}):")
print(old_block.decode("utf-8", errors="replace"))

# Make new_block with proper indentation
indent = b"        "
new_block = new_sql

# Replace
new_raw = raw_bytes[:files_line_start] + new_block + raw_bytes[ret_line_start:]

# Verify syntax
try:
    compile(new_raw.decode("utf-8", errors="replace"), "test", "exec")
    print("\nPython syntax: VALID")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    exit(1)

# Check set_user_id in new file
idx = new_raw.find(b"set_user_id")
print(f"\nNew file at set_user_id:")
print(new_raw[idx:idx+600].decode("utf-8", errors="replace"))

# Push
body = json.dumps({
    "message": "fix: set_id with transaction (placeholder user for FK)",
    "content": base64.b64encode(new_raw).decode(),
    "sha": sha,
}).encode()

put_req = urllib.request.Request(
    "https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py",
    data=body, method="PUT",
    headers={**headers, "Content-Type": "application/json"}
)
put_r = urllib.request.urlopen(put_req)
resp = json.loads(put_r.read())
print(f"\nNew SHA: {resp['content']['sha']}")
print("Push successful!")
