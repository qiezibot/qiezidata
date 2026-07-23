c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Find the admin script block: between switchPage function and loadDashboard
start = c.find('function switchPage')
end = c.find('loadDashboard()</script>')
end = end + len('loadDashboard()</script>')

# Regenerate the entire admin JS (the clouddata part is broken)
# We need to keep switchPage and other existing functions, just replace broken clouddata JS

# Find the exact section that contains the clouddata JS - from function loadCloudDataProjects to DOMContentLoaded
js_start = c.find('function loadCloudDataProjects')
js_end = c.find('document.addEventListener', js_start)
js_end = c.find(';', js_end) + 1

# Replace with clean version - no confusion
new_js_block = '''function loadCloudDataProjects(){fetch('/admin/cdprojects',{credentials:'include'}).then(function(r){return r.json()}).then(function(ps){window.cdProjects=ps;var sel=document.getElementById('cdpSelect');if(!sel)return;sel.innerHTML='';for(var i=0;i<ps.length;i++){var o=document.createElement('option');o.value=ps[i].id;o.text='ID:'+ps[i].id+' '+ps[i].name;sel.appendChild(o)}var p=ps[0];if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\\"cdpToken_'+p.id+'\\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\\"resetToken('+p.id+')\\" class=\\"mybtn btn btn-danger\\">\u91cd\u7f6eTOKEN</button></td></tr>';loadCloudDataStats(p.id);loadCloudDataList(p.id,1)}})}
function loadCloudDataStats(pid){fetch('/admin/cdprojects/stats/'+pid,{credentials:'include'}).then(function(r){return r.json()}).then(function(s){document.getElementById('cdTotal').textContent=s.total;document.getElementById('cdNoRead').textContent=s.noRead;document.getElementById('cdRead').textContent=s.read})}
function loadCloudDataList(pid,page){var q=document.getElementById('cdQueryType').value;var s=document.getElementById('cdSearchText').value;var u='/admin/cddata/'+pid+'?page='+page+'&limit=20&queryType='+q+(s?'&search='+encodeURIComponent(s):'');fetch(u,{credentials:'include'}).then(function(r){return r.json()}).then(function(d){var tb=document.getElementById('cdDataBody');if(!tb)return;tb.innerHTML='';for(var i=0;i<d.items.length;i++){var x=d.items[i];var st=x.read?'\u5df2\u8bfb\u53d6':'\u672a\u8bfb\u53d6';var sc=st==='\u5df2\u8bfb\u53d6'?'green':'orange';var btnT=x.read?'\u4fee\u6539\u4e3a\u672a\u8bfb\u53d6':'\u4fee\u6539\u4e3a\u5df2\u8bfb\u53d6';tb.innerHTML+='<tr><td>'+x.id+'</td><td>'+x.name+'</td><td><a href=\\"#\\" onclick=\\"downloadCD('+x.id+');return false\\">(\u70b9\u51fb\u4e0b\u8f7d)</a></td><td>'+x.md5+'</td><td>'+(x.t||'')+'</td><td><span style=\\"color:'+sc+'\\">'+st+'</span></td><td><button onclick=\\"toggleCDState('+x.id+')\\" class=\\"mybtn btn btn-danger\\">'+btnT+'</button> <button onclick=\\"if(confirm(\'\u786e\u5b9a\u5220\u9664?\'))deleteCD('+x.id+')\\" class=\\"mybtn btn btn-danger\\">\u5220\u9664\u6570\u636e</button></td></tr>'}window.cdPage=page;window.cdTotal=d.total;var pn=Math.ceil(d.total/20)||1;var ph='<li><a href=\\"#\\" onclick=\\"loadCloudDataList('+pid+',1);return false\\">\u9996\u9875</a></li><li><a href=\\"#\\" onclick=\\"loadCloudDataList('+pid+','+Math.max(1,page-1)+');return false\\">\u4e0a\u4e00\u9875</a></li>';for(var i=1;i<=pn;i++){ph+='<li class=\\"'+(i===page?'active':'')+'\\"><a href=\\"#\\" onclick=\\"loadCloudDataList('+pid+','+i+');return false\\">'+i+'</a></li>'}ph+='<li><a href=\\"#\\" onclick=\\"loadCloudDataList('+pid+','+Math.min(pn,page+1)+');return false\\">\u4e0b\u4e00\u9875</a></li><li><a href=\\"#\\" onclick=\\"loadCloudDataList('+pid+','+pn+');return false\\">\u5c3e\u9875</a></li>';document.getElementById('cdPagination').innerHTML=ph})}
function toggleCDState(cid){fetch('/admin/cddata/state/'+cid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)}})}
function deleteCD(cid){var pid=document.getElementById('cdpSelect').value;fetch('/admin/cddata/'+cid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)})}
function resetToken(pid){if(!confirm('\u91cd\u7f6e\u540e\u65e7Token\u5931\u6548\uff0c\u786e\u5b9a\u91cd\u7f6e\u5417?'))return;fetch('/admin/cdprojects/resettoken/'+pid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){document.getElementById('cdpToken_'+pid).textContent=d.token;showToast('\u91cd\u7f6e\u6210\u529f','success')}})}
function resetAllRead(pid){if(!confirm('\u786e\u5b9a\u5c06\u6240\u6709\u6570\u636e\u8bbe\u4e3a\u672a\u8bfb\u53d6?'))return;fetch('/admin/cdprojects/resetallread/'+pid,{method:'POST',credentials:'include'}).then(function(){loadCloudDataStats(pid);loadCloudDataList(pid,1)})}
function createProject(){var n=prompt('\u8bf7\u8f93\u5165\u9879\u76ee\u540d\u79f0:');if(!n)return;fetch('/admin/cdprojects',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({name:n})}).then(function(){loadCloudDataProjects();showToast('\u521b\u5efa\u6210\u529f','success')})}
function deleteProject(){var pid=document.getElementById('cdpSelect').value;if(!confirm('\u5220\u9664\u9879\u76ee\u4f1a\u6e05\u7a7a\u6240\u6709\u6570\u636e\uff0c\u786e\u5b9a\u5220\u9664\u5417?'))return;fetch('/admin/cdprojects/'+pid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataProjects();showToast('\u5220\u9664\u6210\u529f','success')})}
function exportCD(m){var pid=document.getElementById('cdpSelect').value;var t={all:'\u5168\u90e8',read:'\u5df2\u8bfb\u53d6',unread:'\u672a\u8bfb\u53d6'};if(!confirm('\u786e\u5b9a\u5bfc\u51fa'+t[m]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+m)}
function batchDelete(m){var pid=document.getElementById('cdpSelect').value;var t={all:'\u5168\u90e8\u6570\u636e',read:'\u5df2\u8bfb\u53d6\u6570\u636e',unread:'\u672a\u8bfb\u53d6\u6570\u636e'};if(!confirm('\u786e\u5b9a\u5220\u9664'+t[m]+'?'))return;fetch('/admin/cddata/batch/'+pid+'?mode='+m,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,1);loadCloudDataStats(pid);showToast('\u5220\u9664\u6210\u529f','success')})}
function searchCD(){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,1)}
function downloadCD(cid){window.open('/admin/cddata/download/'+cid)}
function initCloudData(){var sel=document.getElementById('cdpSelect');if(!sel)return;sel.onchange=function(){var pid=this.value;if(!pid)return;var p=window.cdProjects.find(function(x){return x.id==pid});if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\\"cdpToken_'+p.id+'\\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\\"resetToken('+p.id+')\\" class=\\"mybtn btn btn-danger\\">\u91cd\u7f6eTOKEN</button></td></tr>'}loadCloudDataStats(pid);loadCloudDataList(pid,1)};document.getElementById('cdQueryType').onchange=function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)};loadCloudDataProjects()}
document.addEventListener('DOMContentLoaded',initCloudData);
'''

assert js_start >= 0, 'js_start not found'
assert js_end > js_start, f'js_end={js_end} <= js_start={js_start}'

c = c[:js_start] + new_js_block + c[js_end:]
print(f'Replaced JS block from {js_start} to {js_end}')
print(f'New size: {len(c)}')

# Verify syntax
open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('Python syntax OK')

# Check key markers in file
for marker in ['function loadCloudDataProjects', 'initCloudData', 'cdpSelect', 'cdDataBody', 'cdPagination', 'exportCD']:
    assert marker in c, f'{marker} missing!'
print('All markers present')
print('DONE')
