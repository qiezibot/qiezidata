import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Insert popfirst route before the first external route
# Find the GET /api/cddata/{data_id} route we added last time
anchor = "\n@app.get('/api/cddata/{data_id}')"

pop_code = (
    "\n@app.get('/api/cddata/{project_id}/popfirst')\n"
    "async def api_pop_first_cddata(project_id: int, request: Request):\n"
    "    token = request.query_params.get('token','')\n"
    "    if not token:\n"
    "        return JSONResponse({'ok':False,'detail':'no token'}, status_code=403)\n"
    "    if use_pg:\n"
    "        async with db_pool.acquire() as conn:\n"
    "            row = await conn.fetchrow('SELECT token FROM clouddata_projects WHERE id=$1', project_id)\n"
    "            if not row or row['token'] != token:\n"
    "                return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)\n"
    "            row = await conn.fetchrow('SELECT id, v FROM clouddata WHERE project_id=$1 AND read=FALSE ORDER BY id ASC LIMIT 1', project_id)\n"
    "            if not row:\n"
    "                return JSONResponse({'ok':False,'detail':'no unread data'}, status_code=404)\n"
    "            val = row['v']\n"
    "            await conn.execute('DELETE FROM clouddata WHERE id=$1', row['id'])\n"
    "            return PlainTextResponse(val)\n"
    "    else:\n"
    "        conn = sqlite3.connect(DB_PATH)\n"
    "        cur = conn.cursor()\n"
    "        cur.execute('SELECT token FROM clouddata_projects WHERE id=?', (project_id,))\n"
    "        row = cur.fetchone()\n"
    "        if not row or row[0] != token:\n"
    "            conn.close()\n"
    "            return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)\n"
    "        cur.execute('SELECT id, v FROM clouddata WHERE project_id=? AND read=0 ORDER BY id ASC LIMIT 1', (project_id,))\n"
    "        row = cur.fetchone()\n"
    "        if not row:\n"
    "            conn.close()\n"
    "            return JSONResponse({'ok':False,'detail':'no unread data'}, status_code=404)\n"
    "        val = row[1]\n"
    "        cur.execute('DELETE FROM clouddata WHERE id=?', (row[0],))\n"
    "        conn.commit(); conn.close()\n"
    "        return PlainTextResponse(val)\n"
)

if anchor in content:
    content = content.replace(anchor, pop_code + anchor, 1)
    print("Pop-first route added OK")
else:
    print("ERROR: anchor not found!")
    idx = content.find("/api/cddata/{data_id}")
    print(repr(content[idx-30:idx+60]))
    exit(1)

# Also update API docs to include popfirst
# Find the 5th endpoint section (DELETE) and add popfirst before it
old_delete_section = "\n<h4 style=\"margin:15px 0 5px\">5. \u5220\u9664\u6570\u636e</h4>"

new_delete_section = (
    "\n<h4 style=\"margin:15px 0 5px\">5. \u5220\u9664\u7b2c\u4e00\u6761\u6570\u636e\uff08\u5373\u7528\u5373\u5220\uff09</h4>\n"
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>GET</strong> /api/cddata/{project_id}/popfirst?token={token}<br>\n'
    '<span style="color:#999">\u8fd4\u56de\u8be5\u9879\u76ee\u4e0b\u7b2c\u4e00\u6761\u672a\u8bfb\u6570\u636e\uff08\u6309id\u5347\u5e8f\uff09\uff0c\u8fd4\u56de\u540e\u76f4\u63a5\u5220\u9664\uff0c\u9002\u5408\u961f\u5217\u5f0f\u6d88\u606f\u5904\u7406\u3002</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">6. \u5220\u9664\u6570\u636e</h4>'
)

if old_delete_section in content:
    content = content.replace(old_delete_section, new_delete_section, 1)
    print("API doc updated with popfirst OK")
else:
    print("WARNING: old_delete_section not found")
    idx = content.find('\u5220\u9664\u6570\u636e</h4>')
    print(repr(content[idx-20:idx+50]))

# Also add lua example for popfirst
old_lua_del = 'local url = "https://qiezidata-production.up.railway.app/api/cddata/123?token=xxx"<br>\nlocal resp = http.delete(url, {})<br>traceprint(resp.body)'
new_lua_del = (
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/123?token=xxx"<br>\n'
    'local resp = http.delete(url, {})<br>'
    'traceprint(resp.body)<br><br>\n'
    "<strong>lua</strong> \u83b7\u53d6\u5e76\u5220\u9664\u7b2c\u4e00\u6761\u672a\u8bfb\u6570\u636e\uff08GET\uff09<br>\n"
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/2/popfirst?token=xxx"<br>\n'
    'local resp = http.get(url, {})<br>'
    'traceprint(resp.body)'
)

if old_lua_del in content:
    content = content.replace(old_lua_del, new_lua_del, 1)
    print("Lua popfirst example added OK")
else:
    print("WARNING: old_lua_del not found")
    idx = content.find('traceprint(resp.body)<br>\n</div>\n</div>\n</div>\n\n<div id="toast"')
    print(f"WARNING at {idx}")

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
    "message": "feat: add /api/cddata/{project_id}/popfirst (get+delete first unread) + update docs",
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
