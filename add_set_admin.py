import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# 1. Add backend route POST /admin/user/{uid}/set_admin
# Find the existing set_id route or last admin route
anchor = "\n@app.post('/admin/user/{uid}/set_id')"
set_admin_code = (
    "\n@app.post('/admin/user/{uid}/set_admin')\n"
    "async def set_user_admin(uid: int, request: Request):\n"
    "    uid = _require(request); user = await _user(uid)\n"
    "    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)\n"
    "    if use_pg:\n"
    "        async with db_pool.acquire() as conn:\n"
    "            row = await conn.fetchrow('SELECT id FROM users WHERE id=$1', uid)\n"
    "            if not row:\n"
    "                return JSONResponse({'ok':False,'detail':'user not found'}, status_code=404)\n"
    "            await conn.execute('UPDATE users SET role=\\'admin\\' WHERE id=$1', uid)\n"
    "    else:\n"
    "        conn = sqlite3.connect(DB_PATH)\n"
    "        cur = conn.cursor()\n"
    "        cur.execute('SELECT id FROM users WHERE id=?', (uid,))\n"
    "        if not cur.fetchone():\n"
    "            conn.close()\n"
    "            return JSONResponse({'ok':False,'detail':'user not found'}, status_code=404)\n"
    "        cur.execute('UPDATE users SET role=\\'admin\\' WHERE id=?', (uid,))\n"
    "        conn.commit(); conn.close()\n"
    "    return JSONResponse({'ok':True})\n"
)

if anchor in content:
    content = content.replace(anchor, set_admin_code + anchor, 1)
    print("Backend set_admin route added OK")
else:
    print("ERROR: set_id anchor not found!")
    idx = content.find('/admin/user/{uid}/set_id')
    print(repr(content[idx-30:idx+60]))
    exit(1)

# 2. Update JS: add setAdmin link/button to user table
# Find the delete button rendering in loadUsers
old_js_render = "(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button>')"
new_js_render = "(u.role==='admin'?'<span style=\"color:green\">\u5df2\u662f\u7ba1\u7406\u5458</span>':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button> <button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\">\u8bbe\u4e3a\u7ba1\u7406\u5458</button>')"

if old_js_render in content:
    content = content.replace(old_js_render, new_js_render, 1)
    print("JS loadUsers updated with set admin button")
else:
    print("WARNING: old JS render not found!")
    idx = content.find("role==='admin'")
    print(repr(content[idx-50:idx+200]))
    # Try alternative - maybe the escaped version
    alt = "role===\\'admin\\'"
    idx2 = content.find(alt)
    if idx2 >= 0:
        print(f'Alt version at {idx2}: {repr(content[idx2:idx2+200])}')

# 3. Add event delegation for set-admin button
old_delegation_end = "deleteUser(uid)})"
new_delegation_end = (
    "deleteUser(uid)})\n"
    "document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.set-admin-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('确定将用户 '+uname+' 设为管理员吗?')){fetch('/admin/user/'+uid+'/set_admin',{method:'POST',credentials:'include'}).then(function(r){if(r.ok){alert('已设为管理员');loadUsers()}else{r.json().then(function(d){alert(d.detail||'设置失败')})}}).catch(function(){alert('请求失败')})}})"
)

# The first delegation listener ends with "deleteUser(uid)})"
# But need to find the right one - the second one (for del-btn)
idx_del = content.rfind("deleteUser(uid)})")
if idx_del >= 0:
    end_of_delegation = content.find("\n", idx_del)
    # Check if it's the right one
    context = content[idx_del-50:idx_del+10]
    if '.del-btn' in context or 'set-admin-btn' not in context:
        # This is the del-btn delegation, append after it
        content = content[:idx_del+len("deleteUser(uid)})")] + "\n" + new_delegation_end.split("\n",1)[1]
        print("set-admin delegation added after del-btn delegation")
    else:
        print("Already has set-admin delegation?")
else:
    print("WARNING: deleteUser delegation end not found")

# Verify
idx1 = content.find('"""')
idx2 = content.find('"""', idx1+3) + 3
code = content[idx2:]
try:
    compile(code, 'prod', 'exec')
    print("Python syntax: VALID")
except SyntaxError as e:
    print(f"ERROR line {e.lineno}: {e.msg}")
    lines = code.split('\n')
    for i in range(max(0,e.lineno-3), min(len(lines), e.lineno+2)):
        print(f"  {i+1}: {lines[i][:120]}")
    exit(1)

body = json.dumps({
    "message": "feat: add set_admin route + button in user management",
    "content": base64.b64encode(content.encode('utf-8')).decode(),
    "sha": sha,
}).encode()

put_req = urllib.request.Request(
    "https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py",
    data=body, method="PUT",
    headers={**headers, "Content-Type": "application/json"}
)
put_r = urllib.request.urlopen(put_req)
resp = json.loads(put_r.read())
print(f"Push OK, new SHA: {resp['content']['sha']}")
