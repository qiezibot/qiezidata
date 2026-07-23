import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Insert fetchone route before popfirst
anchor = "\n@app.get('/api/cddata/{project_id}/popfirst')"

fetchone_code = (
    "\n@app.get('/api/cddata/{project_id}/fetchone')\n"
    "async def api_fetch_one_cddata(project_id: int, request: Request):\n"
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
    "            await conn.execute('UPDATE clouddata SET read=TRUE WHERE id=$1', row['id'])\n"
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
    "        cur.execute('UPDATE clouddata SET read=1 WHERE id=?', (row[0],))\n"
    "        conn.commit(); conn.close()\n"
    "        return PlainTextResponse(val)\n"
)

if anchor in content:
    content = content.replace(anchor, fetchone_code + anchor, 1)
    print("Fetch-one route added OK")
else:
    print("ERROR: anchor not found!")
    exit(1)

# Update API docs: add fetchone as #4, renumber rest
# Current doc has 5 endpoints, rename #5 popfirst to #6, add #4 fetchone
old_label_4 = '\n<h4 style="margin:15px 0 5px">4. \u6807\u8bb0\u6570\u636e\u72b6\u6001</h4>'
new_label_4 = ('\n<h4 style="margin:15px 0 5px">4. \u83b7\u53d6\u7b2c\u4e00\u6761\u672a\u8bfb\u6570\u636e\uff08\u81ea\u52a8\u6807\u5df2\u8bfb\uff09</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>GET</strong> /api/cddata/{project_id}/fetchone?token={token}<br>\n'
    '<span style="color:#999">\u53d6\u8be5\u9879\u76ee\u4e0b\u7b2c\u4e00\u6761\u672a\u8bfb\u6570\u636e\uff08\u6309id\u5347\u5e8f\uff09\uff0c\u8fd4\u56de\u5185\u5bb9\u540e\u81ea\u52a8\u6807\u4e3a\u5df2\u8bfb\u3002</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">5. \u6807\u8bb0\u6570\u636e\u72b6\u6001</h4>')

content = content.replace(old_label_4, new_label_4, 1)
print("API doc: fetchone added as #4, state renumbered to #5")

# Renumber remaining
content = content.replace('<h4 style="margin:15px 0 5px">5. \u5220\u9664\u7b2c\u4e00\u6761\u6570\u636e\uff08\u5373\u7528\u5373\u5220\uff09</h4>',
    '<h4 style="margin:15px 0 5px">6. \u5220\u9664\u7b2c\u4e00\u6761\u6570\u636e\uff08\u5373\u7528\u5373\u5220\uff09</h4>', 1)
content = content.replace('<h4 style="margin:15px 0 5px">6. \u5220\u9664\u6570\u636e</h4>',
    '<h4 style="margin:15px 0 5px">7. \u5220\u9664\u6570\u636e</h4>', 1)
print("API doc: renumbered #5->#6, #6->#7")

# Also add lua example for fetchone in the lr section
# Insert before the popfirst lua example
old_lua_marker = "<strong>lua</strong> \u83b7\u53d6\u5e76\u5220\u9664\u7b2c\u4e00\u6761\u672a\u8bfb\u6570\u636e\uff08GET\uff09<br>"
new_lua_marker = (
    "<strong>lua</strong> \u83b7\u53d6\u7b2c\u4e00\u6761\u672a\u8bfb\u6570\u636e\u5e76\u6807\u5df2\u8bfb\uff08GET\uff09<br>\n"
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/2/fetchone?token=xxx"<br>\n'
    'local resp = http.get(url, {})<br>'
    'traceprint(resp.body)<br><br>\n'
    "<strong>lua</strong> \u83b7\u53d6\u5e76\u5220\u9664\u7b2c\u4e00\u6761\u672a\u8bfb\u6570\u636e\uff08GET\uff09<br>"
)

content = content.replace(old_lua_marker, new_lua_marker, 1)
print("Lua fetchone example added OK")

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
    "message": "feat: add /api/cddata/{project_id}/fetchone (get first unread + mark read) + update docs",
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
