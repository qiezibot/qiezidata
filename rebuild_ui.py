# Full rebuild: DingDangCat-style Chinese admin with 云数据
# Reads the current file, splices in new templates

ADMIN = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>管理后台 - 茄子数据</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;display:flex;min-height:100vh}
.sidebar{width:220px;background:#fff;border-right:1px solid #e8e8e8;min-height:100vh;flex-shrink:0;display:flex;flex-direction:column}
.sidebar .logo{padding:20px 16px 12px;font-size:20px;font-weight:700;color:#667eea;border-bottom:1px solid #f0f0f0;margin-bottom:8px}
.sidebar .nav-item{padding:12px 20px;cursor:pointer;color:#555;font-size:14px;display:flex;align-items:center;gap:10px;border-left:3px solid transparent;transition:all .2s;margin:2px 0}
.sidebar .nav-item:hover{background:#f5f7ff;color:#667eea}
.sidebar .nav-item.active{background:#f0f2ff;color:#667eea;border-left-color:#667eea;font-weight:500}
.sidebar .nav-item .icon{font-size:18px;width:24px;text-align:center}
.sidebar .nav-spacer{flex:1}
.sidebar .nav-bottom{border-top:1px solid #f0f0f0;padding:12px 20px;font-size:13px;color:#999}
.sidebar .nav-bottom a{color:#999;text-decoration:none}
.sidebar .nav-bottom a:hover{color:#667eea}
.main{flex:1;display:flex;flex-direction:column}
.header{background:#fff;border-bottom:1px solid #e8e8e8;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.header .title{font-size:16px;font-weight:500;color:#333}
.header .user-area{display:flex;align-items:center;gap:16px;font-size:14px;color:#666}
.header .user-area a{color:#e74c3c;text-decoration:none;font-size:13px}
.content{padding:24px;flex:1;overflow-y:auto}
.tab-page{display:none}
.tab-page.active{display:block}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,.06);text-align:center}
.stat-card .num{font-size:30px;font-weight:700;color:#667eea}
.stat-card .label{font-size:13px;color:#999;margin-top:4px}
.card{background:#fff;border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.card h2{font-size:16px;margin-bottom:16px;color:#444}
.user-table{width:100%;border-collapse:collapse;font-size:14px}
.user-table th{text-align:left;padding:10px 12px;border-bottom:2px solid #eee;color:#666;font-weight:500;font-size:13px}
.user-table td{padding:10px 12px;border-bottom:1px solid #f0f0f0;font-size:13px}
.upload-zone{border:2px dashed #ccc;border-radius:10px;padding:36px;text-align:center;cursor:pointer;transition:all .2s}
.upload-zone:hover{border-color:#667eea;background:#f8f9ff}
.upload-icon{font-size:40px;margin-bottom:8px}
progress{width:100%;height:6px;border-radius:3px;margin-top:10px;display:none}
.file-list{list-style:none}
.file-item{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0}
.file-item:last-child{border-bottom:none}
.file-info{flex:1}
.file-name{font-size:14px;font-weight:500}
.file-meta{font-size:12px;color:#999;margin-top:2px}
.file-actions{display:flex;gap:6px}
.file-actions a,.file-actions button{padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#555;background:#fff;cursor:pointer;transition:all .15s}
.file-actions a:hover,.file-actions button:hover{border-color:#667eea;color:#667eea}
.file-actions .del-btn:hover{background:#fff5f5;border-color:#e74c3c;color:#e74c3c}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;opacity:0;z-index:999;transition:opacity .3s}
.toast.show{opacity:1}
.toast.success{background:#27ae60}
.toast.error{background:#e74c3c}
</style></head><body>
<div class="sidebar">
<a href="/" class="logo">茄子数据</a>
<div class="nav-item active" onclick="switchPage('dashboard',this)"><span class="icon">&#x1f4ca;</span>仪表盘</div>
<div class="nav-item" onclick="switchPage('files',this)"><span class="icon">&#x1f4c1;</span>文件管理</div>
<div class="nav-item" onclick="switchPage('upload',this)"><span class="icon">&#x1f4e4;</span>上传</div>
<div class="nav-item" onclick="switchPage('users',this)"><span class="icon">&#x1f465;</span>用户管理</div>
<div class="nav-item" onclick="switchPage('clouddata',this)"><span class="icon">&#x2601;</span>云数据</div>
<div class="nav-spacer"></div>
<div class="nav-bottom"><span>&#x1f464; <!--U--></span> &middot; <a href="/logout">退出登录</a></div>
</div>
<div class="main">
<div class="header"><span class="title">管理后台</span><span class="user-area">&#x1f464; <!--U--></span></div>
<div class="content">
<div class="tab-page active" id="page-dashboard">
<div class="stats">
<div class="stat-card"><div class="num" id="statUsers">-</div><div class="label">用户数</div></div>
<div class="stat-card"><div class="num" id="statFiles">-</div><div class="label">文件数</div></div>
<div class="stat-card"><div class="num" id="statSize">-</div><div class="label">存储量</div></div>
<div class="stat-card"><div class="num" id="statAdmin">-</div><div class="label">管理员</div></div>
</div>
</div>
<div class="tab-page" id="page-files">
<div class="card"><h2>全部文件</h2><div id="fileList"><p style="color:#999;text-align:center;padding:20px">暂无文件</p></div></div>
</div>
<div class="tab-page" id="page-upload">
<div class="card"><h2>上传文件</h2><div class="upload-zone" id="dropZone"><div class="upload-icon">&#x1f4c1;</div><p style="color:#999">拖拽文件到此处或点击选择</p><input type="file" id="fileInput" style="display:none"></div><progress id="uploadProgress" max="100"></progress></div>
<div class="card"><h2>我的文件</h2><div id="myFileList"><p style="color:#999;text-align:center;padding:20px">暂无文件</p></div></div>
</div>
<div class="tab-page" id="page-users">
<div class="card"><h2>用户列表</h2><table class="user-table"><thead><tr><th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th></tr></thead><tbody id="userTableBody"></tbody></table></div>
</div>
<div class="tab-page" id="page-clouddata">
<div class="card"><h2>云数据</h2>
<div style="display:flex;gap:8px;margin-bottom:16px">
<input type="text" id="cdKey" placeholder="Key" style="flex:1;padding:8px 12px;border:2px solid #eee;border-radius:6px;font-size:14px;outline:none">
<input type="text" id="cdVal" placeholder="Value" style="flex:2;padding:8px 12px;border:2px solid #eee;border-radius:6px;font-size:14px;outline:none">
<button onclick="addCloudData()" style="padding:8px 20px;background:#667eea;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px">添加</button>
</div>
<div id="cdList"><p style="color:#999;text-align:center;padding:20px">暂无数据</p></div>
</div>
</div>
</div></div>
<div id="toast" class="toast"></div>
<script>
function switchPage(id,el){document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});el.classList.add('active');document.querySelectorAll('.tab-page').forEach(function(p){p.classList.remove('active')});document.getElementById('page-'+id).classList.add('active');if(id==='dashboard')loadDashboard();if(id==='files')loadAllFiles();if(id==='upload')loadMyFiles();if(id==='users')loadUsers();if(id==='clouddata')loadCloudData()}
document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});document.getElementById('fileInput').addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])});
async function uploadFile(file){var fd=new FormData();fd.append('file',file);document.getElementById('uploadProgress').style.display='block';try{var xhr=new XMLHttpRequest();await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve();else if(xhr.status===401)window.location.href='/';else reject()};xhr.open('POST','/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功','success');loadMyFiles()}catch(e){showToast('上传失败','error')}document.getElementById('uploadProgress').style.display='none'}
async function loadDashboard(){try{var r=await fetch('/admin/stats',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();document.getElementById('statUsers').textContent=d.users;document.getElementById('statFiles').textContent=d.files;document.getElementById('statSize').textContent=d.size_display;document.getElementById('statAdmin').textContent=d.admins}catch(e){}}
async function loadAllFiles(){try{var r=await fetch('/admin/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('fileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B | '+f.owner+'</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>下载</a></div></li>'}h+='</ul>';document.getElementById('fileList').innerHTML=h}catch(e){}}
async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}
async function loadMyFiles(){try{var r=await fetch('/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('myFileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>下载</a><button class=\"del-btn\" onclick=\"delFile('+f.id+')\">删除</button></div></li>'}h+='</ul>';document.getElementById('myFileList').innerHTML=h}catch(e){}}
async function delFile(id){if(!confirm('确定删除？'))return;try{var r=await fetch('/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('删除成功','success');loadMyFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}
async function loadCloudData(){try{var r=await fetch('/admin/clouddata',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();if(!d.length){document.getElementById('cdList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无数据</p>';return}var h='<table class=\"user-table\"><thead><tr><th>Key</th><th>Value</th><th>更新时间</th><th>操作</th></tr></thead><tbody>';for(var i=0;i<d.length;i++){h+='<tr><td>'+d[i].k+'</td><td>'+d[i].v+'</td><td>'+(d[i].t||'-')+'</td><td><button onclick=\"delCloudData('+d[i].id+')\" style=\"padding:2px 8px;border:1px solid #e74c3c;border-radius:4px;color:#e74c3c;background:#fff;cursor:pointer;font-size:12px\">删除</button></td></tr>'}h+='</tbody></table>';document.getElementById('cdList').innerHTML=h}catch(e){}}
async function addCloudData(){var k=document.getElementById('cdKey').value.trim();var v=document.getElementById('cdVal').value.trim();if(!k||!v)return;try{var r=await fetch('/admin/clouddata/add',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({key:k,value:v})});if(r.ok){document.getElementById('cdKey').value='';document.getElementById('cdVal').value='';loadCloudData();showToast('添加成功','success')}else if(r.status===401)window.location.href='/'}catch(e){}}
async function delCloudData(id){if(!confirm('确定删除?'))return;try{var r=await fetch('/admin/clouddata/'+id,{method:'DELETE',credentials:'include'});if(r.ok){loadCloudData();showToast('删除成功','success')}else if(r.status===401)window.location.href='/'}catch(e){}}
function showToast(m,t){var el=document.getElementById('toast');el.textContent=m;el.className='toast '+t+' show';setTimeout(function(){el.classList.remove('show')},3000)}loadDashboard()</script></body></html>"""

LOGIN = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>茄子数据</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.95);border-radius:16px;padding:40px 36px;box-shadow:0 20px 60px rgba(0,0,0,.3);max-width:400px;width:100%;text-align:center}
.card h1{font-size:28px;color:#333;margin-bottom:4px}
.card .subtitle{color:#999;margin-bottom:24px;font-size:14px}
.tabs{display:flex;margin-bottom:24px;border-bottom:2px solid #eee}
.tab{flex:1;text-align:center;padding:10px;cursor:pointer;color:#999;font-weight:500;border-bottom:2px solid transparent;margin-bottom:-2px;font-size:14px}
.tab.active{color:#667eea;border-bottom-color:#667eea}
.form{display:none}
.form.active{display:block}
.input-group{margin-bottom:16px;text-align:left}
.input-group label{display:block;font-size:13px;color:#555;margin-bottom:4px}
.input-group input{width:100%;padding:11px 14px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none;transition:border .2s}
.input-group input:focus{border-color:#667eea}
.btn{width:100%;padding:11px;background:#667eea;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer;transition:background .2s}
.btn:hover{background:#5a6fd6}
.msg{font-size:13px;margin-top:10px;display:none;padding:8px 12px;border-radius:6px;color:#c0392b;background:#fdecea}
.msg.success{color:#27ae60;background:#eafaf1}
</style></head><body><div class="card">
<h1>茄子数据</h1><p class="subtitle">文件管理 v2.1</p>
<div class="tabs"><div class="tab active" onclick="switchTab('login')">登录</div><div class="tab" onclick="switchTab('register')">注册</div></div>
<div class="form active" id="loginForm">
<form method="post" action="/login">
<div class="input-group"><label>用户名</label><input type="text" name="username" placeholder="输入用户名" required autofocus></div>
<div class="input-group"><label>密码</label><input type="password" name="password" placeholder="输入密码" required></div>
<button class="btn" type="submit">登录</button>
</form>
<div class="msg" id="loginError">用户名或密码错误</div>
</div>
<div class="form" id="registerForm">
<form method="post" action="/register" onsubmit="return validateRegister()">
<div class="input-group"><label>用户名</label><input type="text" name="username" id="regUser" placeholder="2-20个字符" required minlength="2" maxlength="20" pattern="^[a-zA-Z0-9_]+$"></div>
<div class="input-group"><label>显示名称</label><input type="text" name="display_name" placeholder="选填" maxlength="30"></div>
<div class="input-group"><label>密码</label><input type="password" name="password" id="regPass" placeholder="至少4个字符" required minlength="4"></div>
<button class="btn" type="submit">注册</button>
</form>
<div class="msg" id="regError"></div>
</div>
</div>
<script>
var p=new URLSearchParams(window.location.search);if(p.get('e')==='1')document.getElementById('loginError').style.display='block';if(p.get('reg')==='1'){document.getElementById('loginError').textContent='注册成功，请登录';document.getElementById('loginError').className='msg success';document.getElementById('loginError').style.display='block'}
function switchTab(n){document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});document.querySelectorAll('.form').forEach(function(f){f.classList.remove('active')});if(n==='login'){document.querySelector('.tab:first-child').classList.add('active');document.getElementById('loginForm').classList.add('active')}else{document.querySelector('.tab:last-child').classList.add('active');document.getElementById('registerForm').classList.add('active')}}
function validateRegister(){var p1=document.getElementById('regPass').value;if(p1.length<4){document.getElementById('regError').textContent='密码太短';document.getElementById('regError').style.display='block';return false}return true}
</script></body></html>"""

USER = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>我的文件 - 茄子数据</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5}
.header{background:#fff;padding:0 24px;height:52px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e8e8e8}
.header .logo{font-size:18px;font-weight:700;color:#667eea;text-decoration:none}
.header .user-area{display:flex;align-items:center;gap:12px;font-size:14px;color:#666}
.header .user-area a{color:#e74c3c;text-decoration:none;font-size:13px}
.container{max-width:800px;margin:20px auto;padding:0 16px}
.card{background:#fff;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.card h2{font-size:16px;margin-bottom:14px;color:#444}
.upload-zone{border:2px dashed #ccc;border-radius:10px;padding:32px;text-align:center;cursor:pointer;transition:all .2s}
.upload-zone:hover{border-color:#667eea;background:#f8f9ff}
.upload-icon{font-size:36px;margin-bottom:6px}
progress{width:100%;height:6px;margin-top:10px;display:none}
.file-list{list-style:none}
.file-item{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0}
.file-item:last-child{border-bottom:none}
.file-info{flex:1}
.file-name{font-size:14px;font-weight:500}
.file-meta{font-size:12px;color:#999;margin-top:2px}
.file-actions{display:flex;gap:6px}
.file-actions a,.file-actions button{padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#555;background:#fff;cursor:pointer}
.file-actions a:hover{border-color:#667eea;color:#667eea}
.file-actions button:hover{background:#fff5f5;border-color:#e74c3c;color:#e74c3c}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;opacity:0;z-index:999}
.toast.show{opacity:1}
.toast.success{background:#27ae60}
.toast.error{background:#e74c3c}
</style></head><body>
<div class="header"><a href="/" class="logo">茄子数据</a><div class="user-area"><span>&#x1f464; <!--U--></span><a href="/logout">退出</a></div></div>
<div class="container">
<div class="card"><h2>上传文件</h2><div class="upload-zone" id="dropZone"><div class="upload-icon">&#x1f4c1;</div><p style="color:#999">拖拽文件到此处或点击选择</p><input type="file" id="fileInput" style="display:none"></div><progress id="uploadProgress" max="100"></progress></div>
<div class="card"><h2>我的文件</h2><div id="fileList"><p style="color:#999;text-align:center;padding:20px">暂无文件</p></div></div>
</div>
<div id="toast" class="toast"></div>
<script>
document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});document.getElementById('fileInput').addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])});
async function uploadFile(file){var fd=new FormData();fd.append('file',file);document.getElementById('uploadProgress').style.display='block';try{var xhr=new XMLHttpRequest();await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve();else if(xhr.status===401)window.location.href='/';else reject()};xhr.open('POST','/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功','success');loadFiles()}catch(e){showToast('上传失败','error')}document.getElementById('uploadProgress').style.display='none'}
async function loadFiles(){try{var r=await fetch('/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('fileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>下载</a><button class=\"del-btn\" onclick=\"delFile('+f.id+')\">删除</button></div></li>'}h+='</ul>';document.getElementById('fileList').innerHTML=h}catch(e){}}
async function delFile(id){if(!confirm('确定删除？'))return;try{var r=await fetch('/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('删除成功','success');loadFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}
function showToast(m,t){var el=document.getElementById('toast');el.textContent=m;el.className='toast '+t+' show';setTimeout(function(){el.classList.remove('show')},3000)}loadFiles()</script></body></html>"""

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

login_assign_end = content.find('"""\n\n_ADMIN = ')
admin_assign_end = content.find('"""\n\n_USER = ')
user_assign_end = content.find('"""\n\n\n\nif __name__')

login_val_start = content.find('"""\\') + 4
admin_val_start = content.find('"""\\', login_assign_end) + 4
user_val_start = content.find('"""\\', admin_assign_end) + 4

new_content = (content[:login_val_start] + LOGIN +
               content[login_assign_end:admin_val_start] + ADMIN +
               content[admin_assign_end:user_val_start] + USER +
               content[user_assign_end:])

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Size: {len(content)} -> {len(new_content)} bytes")

import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print("py_compile OK!")

for t in ['clouddata', '云数据', 'loadCloudData', 'addCloudData', 'delCloudData', 'admin/clouddata/add', 'admin/clouddata/{cid}']:
    assert t in new_content, f"Missing: {t}"

print("All checks passed!")
