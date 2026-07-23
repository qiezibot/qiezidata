import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# === 1. Nav item ===
idx = content.find("switchPage('clouddata',this)")
end_nav = content.find('</div>', idx) + 6
nav_line = '\r\n<div class="nav-item" onclick="switchPage(\'apidocs\',this)"><span class="icon">\U0001f4d6</span>API\u6587\u6863</div>'
content = content[:end_nav] + nav_line + content[end_nav:]
print("Nav item added OK")

# === 2. API docs HTML page ===
idx_toast = content.find('<div id="toast"')
api_html = ('<div class="tab-page" id="page-apidocs">\n'
    '<div class="card" style="background:#e8f4fd;padding:15px">\n'
    '<h3 style="margin-top:0">\U0001f4d6 API \u5bf9\u63a5\u6587\u6863</h3>\n'
    '<p style="color:#666;font-size:14px">\u4ee5\u4e0b\u63a5\u53e3\u4f9b\u7b2c\u4e09\u65b9\u5f00\u53d1\u8005\u5bf9\u63a5\u4f7f\u7528\uff0c\u9700\u8981\u5148\u83b7\u53d6 Access Token\u3002</p>\n\n'
    '<h4 style="margin:15px 0 5px">1. \u83b7\u53d6\u6570\u636e\u5217\u8868</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>GET</strong> /api/cddata/{project_id}?token={token}&amp;queryType=-1<br>\n'
    '<span style="color:#999">\u53c2\u6570\uff1aproject_id=\u9879\u76eeID, token=\u9879\u76eeToken, queryType=-1\u5168\u90e8/0\u672a\u8bfb/1\u5df2\u8bfb</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">2. \u83b7\u53d6\u5355\u6761\u6570\u636e</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>GET</strong> /api/cddata/{data_id}?token={token}<br>\n'
    '<span style="color:#999">\u8fd4\u56de\u8be5\u6761\u6570\u636e\u7684\u539f\u59cb\u5185\u5bb9\uff08\u7eaf\u6587\u672c\uff09</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">3. \u4e0a\u4f20\u6570\u636e</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>POST</strong> /api/cddata/{project_id}?token={token}<br>\n'
    '<span style="color:#999">Body (JSON): {"key": "xxx", "value": "xxx"}</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">4. \u6807\u8bb0\u6570\u636e\u72b6\u6001</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>POST</strong> /api/cddata/state/{data_id}?token={token}<br>\n'
    '<span style="color:#999">\u5207\u6362\u8be5\u6761\u6570\u636e\u7684\u5df2\u8bfb/\u672a\u8bfb\u72b6\u6001</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">5. \u5220\u9664\u6570\u636e</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>DELETE</strong> /api/cddata/{data_id}?token={token}\n'
    '</div>\n\n'
    '<br>\n'
    '<h4 style="color:#e74c3c">\u83b7\u53d6 Token</h4>\n'
    '<p style="font-size:13px;color:#666">\u5728\u4e91\u6570\u636e\u9875\u9762\u521b\u5efa\u9879\u76ee\u540e\uff0c\u9879\u76ee\u8be6\u60c5\u4e2d\u4f1a\u663e\u793a\u5bf9\u5e94\u7684 Token\u3002<br>\n'
    'Token \u7528\u4e8e\u9274\u6743\uff0c\u8bf7\u59a5\u5584\u4fdd\u7ba1\u3002</p>\n'
    '</div>\n</div>\n\n')

content = content[:idx_toast] + api_html + content[idx_toast:]
print("API docs page added OK")

# === 3. Upload text file JS with project_id ===
old_js = "function uploadTextFile(){var key=document.getElementById('cdUploadKey').value.trim();if(!key){alert('请输入Key');return}var fileInput=document.getElementById('cdUploadFile');if(!fileInput.files||!fileInput.files[0]){alert('请选择文件');return}var reader=new FileReader();reader.onload=function(e){var val=e.target.result;fetch('/admin/clouddata/add',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({key:key,value:val})}).then(function(r){if(r.ok){document.getElementById('cdUploadStatus').textContent='上传成功';document.getElementById('cdUploadKey').value='';fileInput.value='';var pid=document.getElementById('cdpSelect').value;if(pid)loadCloudDataList(pid,1)}else{alert('上传失败')}}).catch(function(){alert('上传失败')})};reader.readAsText(fileInput.files[0])}"

new_js = "function uploadTextFile(){var key=document.getElementById('cdUploadKey').value.trim();var fileInput=document.getElementById('cdUploadFile');if(!fileInput.files||!fileInput.files[0]){alert('请选择文件');return}if(!key)key=fileInput.files[0].name.replace(/\.[^.]+$/,'');var pid=document.getElementById('cdpSelect').value;if(!pid){alert('请先选择项目');return}var reader=new FileReader();reader.onload=function(e){var val=e.target.result;fetch('/admin/clouddata/add',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({key:key,value:val,project_id:parseInt(pid)})}).then(function(r){if(r.ok){document.getElementById('cdUploadStatus').textContent='上传成功: '+key;document.getElementById('cdUploadKey').value='';fileInput.value='';loadCloudDataList(pid,1)}else{alert('上传失败')}}).catch(function(){alert('上传失败')})};reader.readAsText(fileInput.files[0])}"

if old_js in content:
    content = content.replace(old_js, new_js, 1)
    print("uploadTextFile JS updated OK")
else:
    print("ERROR: old JS not found!")
    idx = content.find('uploadTextFile')
    end = content.find('})', idx) + 4
    print(f"Actual JS: {repr(content[idx:end])}")
    exit(1)

# === 4. Backend clouddata_add ===
old_py = '    b = await request.json(); k = b.get(\'key\',\'\').strip(); v = b.get(\'value\',\'\').strip()\r\n    if not k or not v: raise HTTPException(400)\r\n    if use_pg:\r\n        await db_execute(\'INSERT INTO clouddata(k,v) VALUES($1,$2) ON CONFLICT(k) DO UPDATE SET v=$2\', k, v)\r\n    else:\r\n        await db_execute(\'INSERT OR REPLACE INTO clouddata(k,v) VALUES(?,?)\', k, v)\r\n    return {\'ok\': True}'

new_py = '    b = await request.json(); k = b.get(\'key\',\'\').strip(); v = b.get(\'value\',\'\').strip(); pid = b.get(\'project_id\')\r\n    if not k or not v: raise HTTPException(400)\r\n    if pid is not None:\r\n        import hashlib\r\n        name = k; md5 = hashlib.md5(v.encode()).hexdigest()\r\n        if use_pg:\r\n            await db_execute("DELETE FROM clouddata WHERE project_id=$1 AND k=$2", pid, k)\r\n            await db_execute("INSERT INTO clouddata(project_id,k,v,name,md5) VALUES($1,$2,$3,$4,$5)", pid, k, v, name, md5)\r\n        else:\r\n            await db_execute("DELETE FROM clouddata WHERE project_id=? AND k=?", pid, k)\r\n            await db_execute("INSERT INTO clouddata(project_id,k,v,name,md5) VALUES(?,?,?,?,?)", pid, k, v, name, md5)\r\n    else:\r\n        if use_pg:\r\n            await db_execute(\'INSERT INTO clouddata(k,v) VALUES($1,$2) ON CONFLICT(k) DO UPDATE SET v=$2\', k, v)\r\n        else:\r\n            await db_execute(\'INSERT OR REPLACE INTO clouddata(k,v) VALUES(?,?)\', k, v)\r\n    return {\'ok\': True}'

if old_py in content:
    content = content.replace(old_py, new_py, 1)
    print("clouddata_add backend updated OK")
else:
    print("ERROR: old_py not found!")
    idx = content.find("b = await request.json()")
    if idx >= 0:
        print(f"Actual: {repr(content[idx:idx+400])}")
    exit(1)

# === Verify ===
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
    "message": "fix: correct nav insert + API docs page + clouddata project_id support",
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
