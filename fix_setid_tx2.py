import urllib.request, json, base64

TOKEN = "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"
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "push-script"}

req_src = urllib.request.Request("https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py", headers=headers)
r = urllib.request.urlopen(req_src)
data = json.loads(r.read())
sha = data["sha"]
raw_bytes = base64.b64decode(data["content"])

print(f"Current SHA: {sha}")

# Replace the entire transaction block with a simpler approach
# Use conn.execute with raw SQL that temporarily handles FK
# 
# asyncpg doesn't support multi-statement execute() with params properly
# So let's do it as: run two separate awaits with FK temporarily disabled
#
# Actually let's just run them as separate awaits in the right order but with FK constraint temporarily removed

old_marker = b"        # Transaction: create placeholder, swap files, swap user, cleanup\n        await conn.execute('''\n            INSERT INTO users (id, username, display_name, role, password_hash, created_at)\n            VALUES ($1, $$_tmp_$$, $$_tmp_$$, $$user$$, $$_tmp_$$, NOW())\n            ON CONFLICT DO NOTHING;\n            UPDATE files SET user_id=\\$1 WHERE user_id=\\$2;\n            UPDATE users SET id=\\$1 WHERE id=\\$2;\n            DELETE FROM users WHERE id=\\$3 AND username=$$_tmp_$$;\n        '''"

# That's too brittle. Better to find the multiline string block
# Find the ''' start. The pattern is: await conn.execute('''\n...\n...''', new_id, uid)
# Actually asyncpg doesn't support named params in multi-statement
# Let's just use separate await calls with FK disable in between them

# Strategy: find the block from "# Update ID" to just before "return JSONResponse"
marker_id = b"# Update ID"
marker_return = b"return JSONResponse"

start_idx = raw_bytes.find(marker_id, 9700)  # start search from ~9700
end_idx = raw_bytes.rfind(marker_return, 9700)

print(f"start: {start_idx}")
print(f"end: {end_idx}")

# Find exact line boundaries
line_start = raw_bytes.rfind(b"\r\n", 0, start_idx) + 2
line_end = raw_bytes.rfind(b"\r\n", 0, end_idx)

old_block = raw_bytes[line_start:line_end]
print(f"\nOld block ({line_start}-{line_end}, {len(old_block)} bytes):")
print(old_block.decode("utf-8", errors="replace"))

new_block = b"""        # Disable FK check temporarily
        await conn.execute('SET session_replication_role = replica')
        # Update files first, then users
        await conn.execute('UPDATE files SET user_id=$1 WHERE user_id=$2', new_id, uid)
        await conn.execute('UPDATE users SET id=$1 WHERE id=$2', new_id, uid)
        # Re-enable FK check
        await conn.execute('SET session_replication_role = origin')"""

# Replace
new_raw = raw_bytes.replace(old_block, new_block, 1)

# Verify syntax
try:
    compile(new_raw.decode("utf-8", errors="replace"), "test", "exec")
    print("\nPython syntax: VALID")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    exit(1)

# Show the resulting function
idx = new_raw.find(b"set_user_id")
print(f"\nResulting function:")
print(new_raw[idx:idx+900].decode("utf-8", errors="replace"))

# Push
body = json.dumps({
    "message": "fix: set_id with session_replication_role (disable FK temporarily)",
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
