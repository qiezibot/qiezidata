"""
Complete clouddata overhaul: add project system + all dingdangmao features
"""
c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# ======== FIXES ========
# Fix 1: Response import
c = c.replace(
    'from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse',
    'from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse, Response'
)

# Fix 2: clouddata_list already uses db_fetch, good.

# ======== DATABASE TABLES ========
# Add clouddata_projects table creation in init_db's PG branch
pg_table_add = """
            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata_projects(id SERIAL PRIMARY KEY,name VARCHAR(255) NOT NULL,token VARCHAR(64) NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            # migrate old clouddata to default project
            try:
                cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata_projects")
                if cnt == 0:
                    await conn.execute("INSERT INTO clouddata_projects (name,token) VALUES ($1,$2)", 'default', 'token_default')
                    old_cd = await conn.fetchval("SELECT COUNT(*) FROM clouddata")
                    if old_cd > 0:
                        await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects WHERE name='default') WHERE project_id IS NULL")
            except: pass
            try:
                await conn.execute("ALTER TABLE clouddata ADD COLUMN project_id INTEGER REFERENCES clouddata_projects(id) DEFAULT 1")
                await conn.execute("ALTER TABLE clouddata ADD COLUMN name VARCHAR(255) DEFAULT ''")
                await conn.execute("ALTER TABLE clouddata ADD COLUMN md5 VARCHAR(32) DEFAULT ''")
            except: pass
"""
# Insert after clouddata table creation in PG branch
pg_insert_after = "BOOLEAN NOT NULL DEFAULT FALSE')"
pg_idx = c.find(pg_insert_after, c.find('init_db'))
c = c[:pg_idx+len(pg_insert_after)] + pg_table_add + c[pg_idx+len(pg_insert_after):]
print('PG tables added')

# Same for SQLite
sq_table_add = """
        conn.execute('CREATE TABLE IF NOT EXISTS clouddata_projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,token TEXT NOT NULL,created_at TEXT NOT NULL)')
        try: conn.execute("ALTER TABLE clouddata ADD COLUMN project_id INTEGER DEFAULT 1")
        except: pass
        try: conn.execute("ALTER TABLE clouddata ADD COLUMN name TEXT DEFAULT ''")
        except: pass
        try: conn.execute("ALTER TABLE clouddata ADD COLUMN md5 TEXT DEFAULT ''")
        except: pass
"""
sq_insert_after = "read INTEGER NOT NULL DEFAULT 0"
sq_idx = c.find(sq_insert_after, c.find('init_db'))
sq_idx2 = c.find(")", sq_idx+1)
c = c[:sq_idx2] + sq_insert_after + ")" + c[sq_idx2:]
# Actually the SQLite clouddata table already has read. Just add after the table creation
sq_idx = c.find("read INTEGER NOT NULL DEFAULT 0)", c.find('init_db'))
sq_end = c.find("\n", c.find("DEFAULT 0)", sq_idx))
c = c[:sq_end] + sq_table_add + c[sq_end:]
print('SQLite tables added')

# ======== BACKEND FUNCTIONS ========
# We need to add the backend functions. Find a good insertion point - after the existing clouddata routes
backend_code = '''
# ---- CloudData Project API ----
@app.get('/admin/cdprojects')
async def cdprojects_list(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        r = await db_fetch("SELECT id,name,token,to_char(created_at,'YYYY-MM-DD HH24:MI') AS t FROM clouddata_projects ORDER BY id DESC")
    else:
        r = await db_fetch('SELECT id AS \"id\",name,token,created_at AS t FROM clouddata_projects ORDER BY id DESC')
    return r

@app.post('/admin/cdprojects')
async def cdprojects_create(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    body = await request.json(); name = body.get('name','')
    import uuid
    token = uuid.uuid4().hex[:32]
    if use_pg:
        await db_execute("INSERT INTO clouddata_projects (name,token) VALUES ($1,$2)", name, token)
    else:
        await db_execute("INSERT INTO clouddata_projects (name,token,created_at) VALUES (?,?,?)", name, token, datetime.utcnow().isoformat())
    return {'ok':True}

@app.delete('/admin/cdprojects/{pid}')
async def cdprojects_delete(request: Request, pid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    await db_execute("DELETE FROM clouddata WHERE project_id=?", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1", pid)
    if use_pg:
        await db_execute("DELETE FROM clouddata_projects WHERE id=$1", pid)
    else:
        await db_execute("DELETE FROM clouddata_projects WHERE id=?", pid)
    return {'ok':True}

@app.post('/admin/cdprojects/resettoken/{pid}')
async def cdprojects_reset_token(request: Request, pid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    import uuid
    token = uuid.uuid4().hex[:32]
    if use_pg:
        await db_execute("UPDATE clouddata_projects SET token=$1 WHERE id=$2", token, pid)
    else:
        await db_execute("UPDATE clouddata_projects SET token=? WHERE id=?", token, pid)
    return {'ok':True, 'token':token}

@app.post('/admin/cdprojects/resetallread/{pid}')
async def cdprojects_reset_all_read(request: Request, pid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        await db_execute("UPDATE clouddata SET read=FALSE WHERE project_id=$1", pid)
    else:
        await db_execute("UPDATE clouddata SET read=0 WHERE project_id=?", pid)
    return {'ok':True}

@app.get('/admin/cdprojects/stats/{pid}')
async def cdprojects_stats(request: Request, pid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        total = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=$1", pid)
        no_read = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=$1 AND read=FALSE", pid)
        read_cnt = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=$1 AND read=TRUE", pid)
    else:
        total = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=?", pid)
        no_read = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=0", pid)
        read_cnt = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=1", pid)
    return {'total':total, 'noRead':no_read, 'read':read_cnt}

@app.get('/admin/cddata/{pid}')
async def cddata_list(request: Request, pid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    page = int(request.query_params.get('page',1)); limit = int(request.query_params.get('limit',20))
    queryType = int(request.query_params.get('queryType', -1))  # -1=all, 0=unread, 1=read
    search = request.query_params.get('search','')
    offset = (page-1)*limit

    where = f"WHERE project_id='{pid}'"
    if queryType == 0: where += " AND read=FALSE" if use_pg else " AND read=0"
    elif queryType == 1: where += " AND read=TRUE" if use_pg else " AND read=1"
    if search: where += f" AND name LIKE '%{search}%'"

    if use_pg:
        total = await db_fetchval(f"SELECT COUNT(*) FROM clouddata {where}")
        r = await db_fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}")
    else:
        total = await db_fetchval(f"SELECT COUNT(*) FROM clouddata {where}")
        r = await db_fetch(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}")
    return {'items': r, 'total': total}

@app.post('/admin/cddata/state/{cid}')
async def cddata_toggle_state(request: Request, cid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        await db_execute("UPDATE clouddata SET read=NOT read WHERE id=$1", cid)
        r = await db_fetch("SELECT read FROM clouddata WHERE id=$1", cid)
    else:
        await db_execute("UPDATE clouddata SET read = CASE WHEN read=0 THEN 1 ELSE 0 END WHERE id=?", cid)
        r = await db_fetch("SELECT read FROM clouddata WHERE id=?", cid)
    return {'ok':True, 'read': bool(r[0]['read']) if r else False}

@app.delete('/admin/cddata/{cid}')
async def cddata_delete(request: Request, cid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    await db_execute("DELETE FROM clouddata WHERE id=?", cid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE id=$1", cid)
    return {'ok':True}

@app.delete('/admin/cddata/batch/{pid}')
async def cddata_batch_delete(request: Request, pid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    mode = request.query_params.get('mode','all')  # all, read, unread
    if mode == 'all':
        await db_execute("DELETE FROM clouddata WHERE project_id=?", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1", pid)
    elif mode == 'read':
        await db_execute("DELETE FROM clouddata WHERE project_id=? AND read=1", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1 AND read=TRUE", pid)
    elif mode == 'unread':
        await db_execute("DELETE FROM clouddata WHERE project_id=? AND read=0", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1 AND read=FALSE", pid)
    return {'ok':True}

@app.get('/admin/cddata/export/{pid}/{mode}')
async def cddata_export(request: Request, pid: int, mode: str):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    where = f"WHERE project_id='{pid}'"
    if mode == 'read': where += " AND read=TRUE" if use_pg else " AND read=1"
    elif mode == 'unread': where += " AND read=FALSE" if use_pg else " AND read=0"
    
    if use_pg:
        r = await db_fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC")
    else:
        r = await db_fetch(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC")
    
    import csv, io
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['ID','Key','Value','Name','MD5','Time','Read'])
    for row in r:
        writer.writerow([row['id'],row['k'],row['v'],row.get('name',''),row.get('md5',''),row['t'],'已读' if row['read'] else '未读'])
    csv_bytes = out.getvalue().encode('utf-8-sig')
    return Response(content=csv_bytes, media_type='text/csv', headers={'Content-Disposition': f'attachment; filename=clouddata_{pid}_{mode}.csv'})

@app.get('/admin/cddata/download/{cid}')
async def cddata_download(request: Request, cid: int):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        r = await db_fetch("SELECT k,v FROM clouddata WHERE id=$1", cid)
    else:
        r = await db_fetch("SELECT k,v FROM clouddata WHERE id=?", cid)
    if not r: raise HTTPException(status_code=404)
    data = r[0]['v'].encode('utf-8')
    return Response(content=data, media_type='text/plain', headers={'Content-Disposition': f'attachment; filename={r[0]["k"]}.txt'})

'''

# Find insertion point - after the last clouddata route before the templates
# Look for admin template start
tpl_idx = c.find("_ADMIN = '''")
backend_idx = c.rfind("@app.", 0, tpl_idx)
if backend_idx < tpl_idx:
    # Insert at the end of all routes
    pass
backend_idx = c.rfind('\n\n', 0, tpl_idx)
if backend_idx < 0:
    backend_idx = tpl_idx
else:
    backend_idx += 2  # after the double newline

c = c[:backend_idx] + '\n' + backend_code + c[backend_idx:]
print('Backend API code inserted')

# ======== FRONTEND UI ========
# Replace the clouddata section in _ADMIN template
cd_section_start = c.find('async function loadCloudData')
cd_section_end = c.find('async function delCloudData') + 2  # after close brace

new_cd_frontend = '''
function loadCloudDataProjects(){fetch('/admin/cdprojects',{credentials:'include'}).then(r=>r.json()).then(ps=>{window.cdProjects=ps;var sel=document.getElementById('cdpSelect');sel.innerHTML='';ps.forEach((p,i)=>{var o=document.createElement('option');o.value=p.id;o.text='ID:'+p.id+' '+p.name;sel.appendChild(o)});var p=ps[0];if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>';loadCloudDataStats(p.id);loadCloudDataList(p.id,1)}})}}

function loadCloudDataStats(pid){fetch('/admin/cdprojects/stats/'+pid,{credentials:'include'}).then(r=>r.json()).then(s=>{document.getElementById('cdTotal').textContent=s.total;document.getElementById('cdNoRead').textContent=s.noRead;document.getElementById('cdRead').textContent=s.read})}

function loadCloudDataList(pid,page){var q=document.getElementById('cdQueryType').value;var s=document.getElementById('cdSearchText').value;var u='/admin/cddata/'+pid+'?page='+page+'&limit=20&queryType='+q+(s?'&search='+encodeURIComponent(s):'');fetch(u,{credentials:'include'}).then(r=>r.json()).then(d=>{var tb=document.getElementById('cdDataBody');tb.innerHTML='';d.items.forEach(function(x){var st=x.read?'已读取':'未读取';var sc=st=='已读取'?'green':'orange';var btnT=x.read?'修改为未读取':'修改为已读取';tb.innerHTML+='<tr><td>'+x.id+'</td><td>'+x.name+'</td><td><a href=\"#\" onclick=\"downloadCD('+x.id+');return false\">(点击下载)</a></td><td>'+x.md5+'</td><td>'+(x.t||'')+'</td><td><span style=\"color:'+sc+'\">'+st+'</span></td><td><button onclick=\"toggleCDState('+x.id+')\" class=\"mybtn btn btn-danger\">'+btnT+'</button> <button onclick=\"if(confirm(\'确定删除?\'))deleteCD('+x.id+')\" class=\"mybtn btn btn-danger\">删除数据</button></td></tr>'});window.cdPage=page;window.cdTotal=d.total;var pn=Math.ceil(d.total/20)||1;var ph='';for(var i=1;i<=pn;i++){ph+='<li class=\"'+(i==page?'active':'')+'\"><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+i+');return false\">'+i+'</a></li>'}document.getElementById('cdPagination').innerHTML='<li><a href=\"#\" onclick=\"loadCloudDataList('+pid+',1);return false\">首页</a></li><li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+Math.max(1,page-1)+');return false\">上一页</a></li>'+ph+'<li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+Math.min(pn,page+1)+');return false\">下一页</a></li><li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+pn+');return false\">尾页</a></li>'})}

function toggleCDState(cid){fetch('/admin/cddata/state/'+cid,{method:'POST',credentials:'include'}).then(r=>r.json()).then(function(d){if(d.ok){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)}})}

function deleteCD(cid){var pid=document.getElementById('cdpSelect').value;fetch('/admin/cddata/'+cid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)})}

function resetToken(pid){if(!confirm('重置后旧Token失效，确定重置吗?'))return;fetch('/admin/cdprojects/resettoken/'+pid,{method:'POST',credentials:'include'}).then(r=>r.json()).then(d=>{if(d.ok){document.getElementById('cdpToken_'+pid).textContent=d.token;showToast('重置成功','success')}})}

function resetAllRead(pid){if(!confirm('确定将所有数据设为未读取?'))return;fetch('/admin/cdprojects/resetallread/'+pid,{method:'POST',credentials:'include'}).then(function(){loadCloudDataStats(pid);loadCloudDataList(pid,1)})}

function createProject(){var n=prompt('请输入项目名称:');if(!n)return;fetch('/admin/cdprojects',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({name:n})}).then(function(){loadCloudDataProjects();showToast('创建成功','success')})}

function deleteProject(){var pid=document.getElementById('cdpSelect').value;if(!confirm('删除项目会清空所有数据，确定删除吗?'))return;fetch('/admin/cdprojects/'+pid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataProjects();showToast('删除成功','success')})}

function exportCD(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+t[m]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+m)}

function batchDelete(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部数据',read:'已读取数据',unread:'未读取数据'};if(!confirm('确定删除'+t[m]+'?'))return;fetch('/admin/cddata/batch/'+pid+'?mode='+m,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,1);loadCloudDataStats(pid);showToast('删除成功','success')})}

function searchCD(){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,1)}

function downloadCD(cid){window.open('/admin/cddata/download/'+cid)}

// Event listeners
document.addEventListener('DOMContentLoaded',function(){var sel=document.getElementById('cdpSelect');if(sel){sel.addEventListener('change',function(){var pid=this.value;if(pid){var p=window.cdProjects.find(x=>x.id==pid);if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>'}loadCloudDataStats(pid);loadCloudDataList(pid,1)}});document.getElementById('cdQueryType').addEventListener('change',function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)});loadCloudDataProjects()}});
'''

old_cd_frontend = c[cd_section_start:cd_section_end]
c = c.replace(old_cd_frontend, new_cd_frontend)
print('Frontend JS replaced')

# ======== REPLACE HTML SECTION ========
old_html_start = c.find('page-clouddata">')
old_html_end = c.find('</div>', old_html_start)
old_html_end = c.find('</div>', old_html_end + 6)
old_html_end = c.find('</div>', old_html_end + 6)

new_html = '''page-clouddata">
<div class="card" style="background:#edf7ec;padding:10px">
<div style="margin-bottom:10px">
<span style="font-size:18px">选择项目:</span>
<select id="cdpSelect" style="width:300px;display:inline-block;padding:4px;border-radius:4px;border:1px solid #ccc"></select>
<button onclick="createProject()" class="btn btn-info" style="margin:0 5px">创建云数据项目</button>
<button onclick="deleteProject()" class="btn btn-danger">删除当前选择项目</button>
<button onclick="resetAllRead(document.getElementById('cdpSelect').value)" class="btn btn-success" style="margin:0 5px">设置全部数据状态为未读取</button>
</div>
<div style="margin-bottom:10px">
<span style="font-size:16px">总数:</span><span id="cdTotal" style="font-size:17px;font-weight:bold">0</span>
<span style="font-size:16px;margin-left:15px">未读取:</span><span id="cdNoRead" style="font-size:17px;font-weight:bold;color:orange">0</span>
<span style="font-size:16px;margin-left:15px">已读取:</span><span id="cdRead" style="font-size:17px;font-weight:bold;color:green">0</span>
<button onclick="loadCloudDataStats(document.getElementById('cdpSelect').value)" class="btn btn-info" style="margin-left:10px">刷新</button>
</div>
<div style="overflow:auto">
<table class="user-table" style="font-size:13px">
<thead><tr><th>项目ID</th><th>项目名称</th><th>访问Token</th><th>项目创建时间</th><th>操作命令</th></tr></thead>
<tbody id="cdpTableBody"></tbody>
</table>
</div>
</div>

<h5 style="margin:1px"></h5>
<div class="card" style="background:#fff4f4;padding:10px">
<div style="margin-bottom:10px">
<span style="font-size:18px">选择数据状态:</span>
<select id="cdQueryType" style="width:200px;display:inline-block;padding:4px;border-radius:4px;border:1px solid #ccc">
<option value="-1">所有数据</option>
<option value="0">未读取的数据</option>
<option value="1">已读取的数据</option>
</select>
<button onclick="exportCD('all')" class="btn btn-success">导出所有数据</button>
<button onclick="exportCD('unread')" class="btn btn-success">导出所有未读取数据</button>
<button onclick="exportCD('read')" class="btn btn-success">导出所有已读取数据</button>
<div class="btn-group" style="display:inline-block;margin-left:5px">
<button class="btn btn-danger dropdown-toggle" onclick="var m=this.nextElementSibling;m.style.display=m.style.display=='none'?'block':'none'">删除数据 &#9660;</button>
<ul style="display:none;position:absolute;background:#fff;border:1px solid #ccc;list-style:none;padding:5px;z-index:10">
<li><a href="#" onclick="batchDelete('all');return false" style="color:#333">删除所有数据</a></li>
<li><a href="#" onclick="batchDelete('read');return false" style="color:#333">删除所有已读取数据</a></li>
<li><a href="#" onclick="batchDelete('unread');return false" style="color:#333">删除所有未读取数据</a></li>
</ul>
</div>
<input id="cdSearchText" type="text" style="width:300px;display:inline-block;padding:4px;border-radius:4px;border:1px solid #ccc;margin-left:10px" placeholder="输入数据名字搜索数据" onkeydown="if(event.keyCode==13)searchCD()">
<button onclick="searchCD()" class="btn btn-info" style="margin-left:5px">🔍</button>
</div>
<div style="overflow:auto">
<table class="user-table" style="font-size:13px">
<thead><tr><th>Id</th><th>数据名字</th><th>数据</th><th>数据MD5</th><th>更新时间</th><th>状态</th><th>数据操作</th></tr></thead>
<tbody id="cdDataBody"></tbody>
</table>
</div>
<nav style="margin-top:10px;text-align:center">
<ul id="cdPagination" class="pagination" style="list-style:none;display:inline-flex;gap:5px;padding:0"></ul>
</nav>
</div>
</div>'''

c = c[:old_html_start] + new_html + c[old_html_end:]
print('HTML replaced')

# Verify
assert ', Response' in c, 'Response import lost!'
assert 'clouddata_projects' in c, 'projects table missing!'
assert 'cdpSelect' in c, 'project selector missing!'
assert 'cdDataBody' in c, 'data table missing!'
assert 'cdPagination' in c, 'pagination missing!'

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('=== ALL OK ===')
print('Size:', len(c))
