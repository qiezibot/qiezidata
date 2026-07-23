import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# The problem: the regex replacement broke the file. Start fresh.
# Re-do the changes more carefully

# 1. Backend route: insert set_admin before set_id
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
content = content.replace(anchor, set_admin_code + anchor, 1)
print("Backend route added")

# 2. JS: update user table rendering
# The original render
old_js = "(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button>')"
new_js = "(u.role==='admin'?'<span style=\"color:green\">\u5df2\u662f\u7ba1\u7406\u5458</span>':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">\u8bbe\u4e3a\u7ba1\u7406\u5458</button>')"

if old_js in content:
    content = content.replace(old_js, new_js, 1)
    print("JS render updated")
else:
    print("ERROR: old JS not found")
    exit(1)

# 3. Add event delegation for set-admin
# Find the end of del-btn delegation listener
old_end = "deleteUser(uid)})\r\n"
# Insert after
new_end = old_end + (
    "document.getElementById('userTableBody').addEventListener('click',function(e){"
    "var btn=e.target.closest('.set-admin-btn');"
    "if(!btn)return;"
    "var uid=parseInt(btn.getAttribute('data-uid'));"
    "var uname=btn.getAttribute('data-uname');"
    "if(confirm('\u786e\u5b9a\u5c06\u7528\u6237 '+uname+' \u8bbe\u4e3a\u7ba1\u7406\u5458\u5417?')){"
    "fetch('/admin/user/'+uid+'/set_admin',{method:'POST',credentials:'include'}).then(function(r){"
    "if(r.ok){alert('\u5df2\u8bbe\u4e3a\u7ba1\u7406\u5458');loadUsers()}"
    "else{r.json().then(function(d){alert(d.detail||'\u8bbe\u7f6e\u5931\u8d25')})}"
    "}).catch(function(){alert('\u8bf7\u6c42\u5931\u8d25')})}})\r\n"
)

if old_end in content:
    content = content.replace(old_end, new_end, 1)
    print("set-admin delegation added")
else:
    print("ERROR: old_end not found")
    print(repr(content[content.find('deleteUser(uid)')-20:content.find('deleteUser(uid)')+30]))
    exit(1)

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
    "message": "feat: add set_admin route + button in user management (fixed)",
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
