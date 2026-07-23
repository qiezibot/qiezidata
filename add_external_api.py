import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Find the last external API route before the admin routes
# Insert the GET single data route right before the existing /admin/cddata/... routes
# Find a good anchor: the @app.get('/admin/cddata/{pid}') route
insert_anchor = "\n@app.get('/admin/cddata/{pid}')"

new_routes_code = (
    "\n@app.get('/api/cddata/{data_id}')\n"
    "async def api_get_cddata(request: Request, data_id: int):\n"
    "    token = request.query_params.get('token','')\n"
    "    if not token:\n"
    "        return JSONResponse({'ok':False,'detail':'no token'}, status_code=403)\n"
    "    if use_pg:\n"
    "        async with db_pool.acquire() as conn:\n"
    "            row = await conn.fetchrow('SELECT cd.*, cp.token as pt FROM clouddata cd LEFT JOIN clouddata_projects cp ON cd.project_id=cp.id WHERE cd.id=$1', data_id)\n"
    "            if not row or row['pt'] != token:\n"
    "                return JSONResponse({'ok':False,'detail':'not found or token mismatch'}, status_code=404)\n"
    "            await conn.execute('UPDATE clouddata SET read=TRUE WHERE id=$1', data_id)\n"
    "            return PlainTextResponse(row['v'])\n"
    "    else:\n"
    "        conn = sqlite3.connect(DB_PATH)\n"
    "        cur = conn.cursor()\n"
    "        cur.execute('SELECT cd.id, cd.v, cp.token FROM clouddata cd LEFT JOIN clouddata_projects cp ON cd.project_id=cp.id WHERE cd.id=?', (data_id,))\n"
    "        row = cur.fetchone()\n"
    "        if not row or row[2] != token:\n"
    "            conn.close()\n"
    "            return JSONResponse({'ok':False,'detail':'not found or token mismatch'}, status_code=404)\n"
    "        cur.execute('UPDATE clouddata SET read=1 WHERE id=?', (data_id,))\n"
    "        conn.commit(); conn.close()\n"
    "        return PlainTextResponse(row[1])\n"
)

if insert_anchor in content:
    content = content.replace(insert_anchor, new_routes_code + insert_anchor, 1)
    print("External GET /api/cddata/{data_id} route added OK")
else:
    print("ERROR: anchor not found!")
    idx = content.find("/admin/cddata/{pid}")
    print(repr(content[idx-30:idx+30]))
    exit(1)

# Also add POST /api/cddata/{project_id} for upload (mentioned in docs)
# Check if it exists first
if "@app.post('/api/cddata/" not in content:
    insert_anchor2 = "\n@app.get('/admin/cddata/{pid}')"
    new_upload = (
        "\n@app.post('/api/cddata/{project_id}')\n"
        "async def api_post_cddata(project_id: int, request: Request):\n"
        "    b = await request.json(); k = b.get('key','').strip(); v = b.get('value','').strip()\n"
        "    token = request.query_params.get('token','')\n"
        "    if not k or not v or not token:\n"
        "        return JSONResponse({'ok':False,'detail':'missing params'}, status_code=400)\n"
        "    if use_pg:\n"
        "        async with db_pool.acquire() as conn:\n"
        "            row = await conn.fetchrow('SELECT token FROM clouddata_projects WHERE id=$1', project_id)\n"
        "            if not row or row['token'] != token:\n"
        "                return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)\n"
        "            name = k; md5 = hashlib.md5(v.encode()).hexdigest()\n"
        "            await conn.execute('DELETE FROM clouddata WHERE project_id=$1 AND k=$2', project_id, k)\n"
        "            await conn.execute('INSERT INTO clouddata(project_id,k,v,name,md5) VALUES($1,$2,$3,$4,$5)', project_id, k, v, name, md5)\n"
        "    else:\n"
        "        conn = sqlite3.connect(DB_PATH)\n"
        "        cur = conn.cursor()\n"
        "        cur.execute('SELECT token FROM clouddata_projects WHERE id=?', (project_id,))\n"
        "        row = cur.fetchone()\n"
        "        if not row or row[0] != token:\n"
        "            conn.close()\n"
        "            return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)\n"
        "        name = k; md5 = hashlib.md5(v.encode()).hexdigest()\n"
        "        cur.execute('DELETE FROM clouddata WHERE project_id=? AND k=?', (project_id, k))\n"
        "        cur.execute('INSERT INTO clouddata(project_id,k,v,name,md5) VALUES(?,?,?,?,?)', (project_id, k, v, name, md5))\n"
        "        conn.commit(); conn.close()\n"
        "    return JSONResponse({'ok':True, 'key':k})\n"
    )
    content = content.replace(insert_anchor2, new_upload + insert_anchor2, 1)
    print("External POST /api/cddata/{project_id} route added OK")
else:
    print("POST /api/cddata/ route already exists")

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
    "message": "feat: add external GET /api/cddata/{data_id} (auto mark read) + POST /api/cddata/{project_id}",
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
