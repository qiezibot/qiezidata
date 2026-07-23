# -*- coding: utf-8 -*-
# Add clouddata page to admin template + backend APIs

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ===== 1. Sidebar: add clouddata nav item =====
old = '<span class="icon">&#x1f465;</span>\u7528\u6237\u7ba1\u7406</div>\n<div class="nav-spacer">'
new = '<span class="icon">&#x1f465;</span>\u7528\u6237\u7ba1\u7406</div>\n<div class="nav-item" onclick="switchPage(\'clouddata\',this)"><span class="icon">&#x2601;</span>\u4e91\u6570\u636e</div>\n<div class="nav-spacer">'
content = content.replace(old, new, 1)

# ===== 2. Add clouddata tab page =====
old = '</div>\n</div>\n<div id="toast"'
new = (
    '</div>\n</div>\n'
    '<div class="tab-page" id="page-clouddata">\n'
    '<div class="card"><h2>\u4e91\u6570\u636e</h2>\n'
    '<div style="display:flex;gap:8px;margin-bottom:16px">\n'
    '<input type="text" id="cdKey" placeholder="Key" style="flex:1;padding:8px 12px;border:2px solid #eee;border-radius:6px;font-size:14px;outline:none">\n'
    '<input type="text" id="cdVal" placeholder="Value" style="flex:2;padding:8px 12px;border:2px solid #eee;border-radius:6px;font-size:14px;outline:none">\n'
    '<button onclick="addCloudData()" style="padding:8px 20px;background:#667eea;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px">\u6dfb\u52a0</button>\n'
    '</div>\n'
    '<div id="cdList"><p style="color:#999;text-align:center;padding:20px">\u6682\u65e0\u6570\u636e</p></div>\n'
    '</div>\n</div>\n</div>\n<div id="toast"'
)
content = content.replace(old, new, 1)

# ===== 3. Add JS functions =====
# Find switchPage override
old_js_start = 'var _origSP = switchPage'
old_js_block_end = 'loadDashboard()'

js_code = (
    'var _origSP = switchPage;\n'
    'switchPage = function(id,el){_origSP(id,el);if(id===\'clouddata\')setTimeout(loadCloudData,100)};\n'
    'async function loadCloudData(){\n'
    '  try{\n'
    '    var r=await fetch(\'/admin/clouddata\',{credentials:\'include\'});\n'
    '    if(r.status===401){window.location.href=\'/\';return}\n'
    '    var d=await r.json();\n'
    '    if(!d.length){document.getElementById(\'cdList\').innerHTML=\'<p style="color:#999;text-align:center;padding:20px">\u6682\u65e0\u6570\u636e</p>\';return}\n'
    '    var h=\'<table class="user-table"><thead><tr><th>Key</th><th>Value</th><th>\u66f4\u65b0\u65f6\u95f4</th><th>\u64cd\u4f5c</th></tr></thead><tbody>\';\n'
    '    for(var i=0;i<d.length;i++){h+=\'<tr><td>\'+d[i].k+\'</td><td>\'+d[i].v+\'</td><td>\'+(d[i].t||\'-\')+\'</td><td><button onclick="delCloudData(\'+d[i].id+\')" style="padding:2px 8px;border:1px solid #e74c3c;border-radius:4px;color:#e74c3c;background:#fff;cursor:pointer;font-size:12px">\u5220\u9664</button></td></tr>\'}\n'
    '    h+=\'</tbody></table>\';document.getElementById(\'cdList\').innerHTML=h\n'
    '  }catch(e){}\n'
    '}\n'
    'async function addCloudData(){\n'
    '  var k=document.getElementById(\'cdKey\').value.trim();\n'
    '  var v=document.getElementById(\'cdVal\').value.trim();\n'
    '  if(!k||!v)return;\n'
    '  try{\n'
    '    var r=await fetch(\'/admin/clouddata/add\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},credentials:\'include\',body:JSON.stringify({key:k,value:v})});\n'
    '    if(r.ok){document.getElementById(\'cdKey\').value=\'\';document.getElementById(\'cdVal\').value=\'\';loadCloudData();showToast(\'\u6dfb\u52a0\u6210\u529f\',\'success\')}else if(r.status===401)window.location.href=\'/\'\n'
    '  }catch(e){}\n'
    '}\n'
    'async function delCloudData(id){\n'
    '  if(!confirm(\'\u786e\u5b9a\u5220\u9664?\'))return;\n'
    '  try{\n'
    '    var r=await fetch(\'/admin/clouddata/\'+id,{method:\'DELETE\',credentials:\'include\'});\n'
    '    if(r.ok){loadCloudData();showToast(\'\u5220\u9664\u6210\u529f\',\'success\')}else if(r.status===401)window.location.href=\'/\'\n'
    '  }catch(e){}\n'
    '}\n'
    'loadDashboard()'
)

content = content.replace(old_js_start + ';\nswitchPage', '// clouddata\n' + js_code[:js_code.find('loadDashboard()')] + 'var _origSP = switchPage;\nswitchPage', 1)
content = content.replace('loadDashboard()', 'loadDashboard()', 1)  # no-op

# Actually simpler: just replace the block from _origSP to loadDashboard()
old_block = 'var _origSP = switchPage;\nswitchPage = function(id,el){_origSP(id,el);if(id===\'clouddata\')setTimeout(loadCloudData,100)};\n\nloadDashboard()'
content = content.replace(old_block, js_code, 1)

# ===== 4. Add backend API routes =====
api = (
    "\n"
    "@app.get('/admin/clouddata')\n"
    "async def clouddata_list(request: Request):\n"
    "    uid = _require(request); user = await _user(uid)\n"
    "    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)\n"
    "    if use_pg:\n"
    "        return await db_fetch(\"SELECT id,k,v,to_char(t,'YYYY-MM-DD HH24:MI') AS t FROM clouddata ORDER BY id DESC\")\n"
    "    else:\n"
    "        return await db_fetch('SELECT id,k,v,t FROM clouddata ORDER BY id DESC')\n"
    "\n"
    "@app.post('/admin/clouddata/add')\n"
    "async def clouddata_add(request: Request):\n"
    "    uid = _require(request); user = await _user(uid)\n"
    "    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)\n"
    "    b = await request.json(); k = b.get('key','').strip(); v = b.get('value','').strip()\n"
    "    if not k or not v: raise HTTPException(400)\n"
    "    if use_pg:\n"
    "        await db_exec('INSERT INTO clouddata(k,v) VALUES($1,$2) ON CONFLICT(k) DO UPDATE SET v=$2', k, v)\n"
    "    else:\n"
    "        await db_exec('INSERT OR REPLACE INTO clouddata(k,v) VALUES(?,?)', k, v)\n"
    "    return {'ok': True}\n"
    "\n"
    "@app.delete('/admin/clouddata/{cid}')\n"
    "async def clouddata_del(cid: int, request: Request):\n"
    "    uid = _require(request); user = await _user(uid)\n"
    "    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)\n"
    "    if use_pg:\n"
    "        await db_exec('DELETE FROM clouddata WHERE id=$1', cid)\n"
    "    else:\n"
    "        await db_exec('DELETE FROM clouddata WHERE id=?', cid)\n"
    "    return {'ok': True}\n"
    "\n"
)
content = content.replace("@app.get('/admin/stats')", api + "@app.get('/admin/stats')", 1)

# Add clouddata table in init_db - inside async with block
old_init = "            await conn.execute('CREATE TABLE IF NOT EXISTS users"
new_init_pg = (
    "            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata(id SERIAL PRIMARY KEY,k VARCHAR(255) UNIQUE NOT NULL,v TEXT NOT NULL,t TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')\n"
    "\n"
    "            await conn.execute('CREATE TABLE IF NOT EXISTS users"
)
content = content.replace(old_init, new_init_pg, 1)

# Add SQLite clouddata table after files table
old_sqlite = "        if not cols:\n            conn.execute('CREATE TABLE IF NOT EXISTS files"
new_sqlite = (
    "        conn.execute('CREATE TABLE IF NOT EXISTS clouddata(id INTEGER PRIMARY KEY AUTOINCREMENT,k TEXT UNIQUE NOT NULL,v TEXT NOT NULL,t TEXT NOT NULL)')\n"
    "        if not cols:\n            conn.execute('CREATE TABLE IF NOT EXISTS files"
)
content = content.replace(old_sqlite, new_sqlite, 1)

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Written! Size=%d" % len(content))
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print("py_compile OK!")

for t in ['clouddata', '\u4e91\u6570\u636e', 'loadCloudData', 'addCloudData', 'delCloudData']:
    assert t in content, "Missing: " + t
print("All checks passed!")
