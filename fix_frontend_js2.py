new_js = '''
function loadCloudDataProjects(){fetch('/admin/cdprojects',{credentials:'include'}).then(function(r){return r.json()}).then(function(ps){window.cdProjects=ps;var sel=document.getElementById('cdpSelect');if(!sel)return;sel.innerHTML='';for(var i=0;i<ps.length;i++){var o=document.createElement('option');o.value=ps[i].id;o.text='ID:'+ps[i].id+' '+ps[i].name;sel.appendChild(o)}var p=ps[0];if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>';loadCloudDataStats(p.id);loadCloudDataList(p.id,1)}})}

function loadCloudDataStats(pid){fetch('/admin/cdprojects/stats/'+pid,{credentials:'include'}).then(function(r){return r.json()}).then(function(s){document.getElementById('cdTotal').textContent=s.total;document.getElementById('cdNoRead').textContent=s.noRead;document.getElementById('cdRead').textContent=s.read})}

function loadCloudDataList(pid,page){var q=document.getElementById('cdQueryType').value;var s=document.getElementById('cdSearchText').value;var u='/admin/cddata/'+pid+'?page='+page+'&limit=20&queryType='+q+(s?'&search='+encodeURIComponent(s):'');fetch(u,{credentials:'include'}).then(function(r){return r.json()}).then(function(d){var tb=document.getElementById('cdDataBody');if(!tb)return;tb.innerHTML='';for(var i=0;i<d.items.length;i++){var x=d.items[i];var st=x.read?'已读取':'未读取';var sc=st==='已读取'?'green':'orange';var btnT=x.read?'修改为未读取':'修改为已读取';tb.innerHTML+='<tr><td>'+x.id+'</td><td>'+x.name+'</td><td><a href=\"#\" onclick=\"downloadCD('+x.id+');return false\">(点击下载)</a></td><td>'+x.md5+'</td><td>'+(x.t||'')+'</td><td><span style=\"color:'+sc+'\">'+st+'</span></td><td><button onclick=\"toggleCDState('+x.id+')\" class=\"mybtn btn btn-danger\">'+btnT+'</button> <button onclick=\"if(confirm(\'确定删除?\'))deleteCD('+x.id+')\" class=\"mybtn btn btn-danger\">删除数据</button></td></tr>'}window.cdPage=page;window.cdTotal=d.total;var pn=Math.ceil(d.total/20)||1;var ph='<li><a href=\"#\" onclick=\"loadCloudDataList('+pid+',1);return false\">首页</a></li><li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+Math.max(1,page-1)+');return false\">上一页</a></li>';for(var i=1;i<=pn;i++){ph+='<li class=\"'+(i===page?'active':'')+'\"><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+i+');return false\">'+i+'</a></li>'}ph+='<li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+Math.min(pn,page+1)+');return false\">下一页</a></li><li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+pn+');return false\">尾页</a></li>';document.getElementById('cdPagination').innerHTML=ph})}

function toggleCDState(cid){fetch('/admin/cddata/state/'+cid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)}})}

function deleteCD(cid){var pid=document.getElementById('cdpSelect').value;fetch('/admin/cddata/'+cid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)})}

function resetToken(pid){if(!confirm('重置后旧Token失效，确定重置吗?'))return;fetch('/admin/cdprojects/resettoken/'+pid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){document.getElementById('cdpToken_'+pid).textContent=d.token;showToast('重置成功','success')}})}

function resetAllRead(pid){if(!confirm('确定将所有数据设为未读取?'))return;fetch('/admin/cdprojects/resetallread/'+pid,{method:'POST',credentials:'include'}).then(function(){loadCloudDataStats(pid);loadCloudDataList(pid,1)})}

function createProject(){var n=prompt('请输入项目名称:');if(!n)return;fetch('/admin/cdprojects',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({name:n})}).then(function(){loadCloudDataProjects();showToast('创建成功','success')})}

function deleteProject(){var pid=document.getElementById('cdpSelect').value;if(!confirm('删除项目会清空所有数据，确定删除吗?'))return;fetch('/admin/cdprojects/'+pid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataProjects();showToast('删除成功','success')})}

function exportCD(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+t[m]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+m)}

function batchDelete(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部数据',read:'已读取数据',unread:'未读取数据'};if(!confirm('确定删除'+t[m]+'?'))return;fetch('/admin/cddata/batch/'+pid+'?mode='+m,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,1);loadCloudDataStats(pid);showToast('删除成功','success')})}

function searchCD(){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,1)}

function downloadCD(cid){window.open('/admin/cddata/download/'+cid)}

function initCloudData(){var sel=document.getElementById('cdpSelect');if(!sel)return;sel.onchange=function(){var pid=this.value;if(!pid)return;var p=window.cdProjects.find(function(x){return x.id==pid});if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>'}loadCloudDataStats(pid);loadCloudDataList(pid,1)};document.getElementById('cdQueryType').onchange=function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)};loadCloudDataProjects()}

document.addEventListener('DOMContentLoaded',initCloudData);
'''

c = open('railway_file_server.py', 'r', encoding='utf-8').read()

start = c.find('function loadCloudDataProjects')
# Find loadDashboard() AFTER start
ld = c.find('loadDashboard()', start)
end = c.find(';', ld) + 1

print(f'start={start}, ld={ld}, end={end}')

c = c[:start] + new_js + c[end:]
print(f'New size: {len(c)}')

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('OK')

