



/* v3 */



function switchPage(id,el){document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});el.classList.add('active');document.querySelectorAll('.tab-page').forEach(function(p){p.classList.remove('active')});document.getElementById('page-'+id).classList.add('active');if(id==='dashboard')loadDashboard();if(id==='files')loadAllFiles();if(id==='upload')loadMyFiles();if(id==='users')loadUsers();if(id==='clouddata')initCloudData()}



var z=document.getElementById('dropZone');if(z)z.addEventListener('click',function(){var fi=document.getElementById('fileInput');if(fi)fi.click()});var fi=document.getElementById('fileInput');if(fi)fi.addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])});



document.getElementById('fileList').addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('确认删除文件「'+fname+'」吗？'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadAllFiles();alert('文件已删除')}).catch(function(){alert('删除失败')})})



document.getElementById('myFileList').addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('确认删除文件「'+fname+'」吗？'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadMyFiles();alert('文件已删除')}).catch(function(){alert('删除失败')})})







;



async function uploadFile(file){var fd=new FormData();fd.append('file',file);document.getElementById('uploadProgress').style.display='block';try{var xhr=new XMLHttpRequest();await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve();else if(xhr.status===401)window.location.href='/';else reject()};xhr.open('POST','/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功','success');loadMyFiles()}catch(e){showToast('上传失败','error')}document.getElementById('uploadProgress').style.display='none'}



async function loadDashboard(){try{var r=await fetch('/admin/stats',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();document.getElementById('statUsers').textContent=d.users;document.getElementById('statFiles').textContent=d.files;document.getElementById('statSize').textContent=d.size_display;document.getElementById('statAdmin').textContent=d.admins}catch(e){}}



async function loadAllFiles(){try{var r=await fetch('/admin/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('fileList').innerHTML='<p style="color:#999;text-align:center;padding:20px">暂无文件</p>';return}var h='<ul class="file-list">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class="file-item"><div class="file-info"><div class="file-name">'+f.original_name+'</div><div class="file-meta">'+f.size+'B | '+f.owner+'</div></div><div class="file-actions"><a href="/download/'+f.id+'" download>下载</a><button class="af-del" data-fid="' + f.id + '" data-fname="'+f.original_name+'">删除</button></div></li>'}h+='</ul>';document.getElementById('fileList').innerHTML=h}catch(e){}}



async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}



document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.del-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('确定要删除用户 '+uname+' 吗?此操作不可恢复!'))deleteUser(uid)})



document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.set-admin-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('确定将用户 '+uname+' 设为管理员吗?')){fetch('/admin/user/'+uid+'/set_admin',{method:'POST',credentials:'include'}).then(function(r){if(r.ok){alert('已设为管理员');loadUsers()}else{r.json().then(function(d){alert(d.detail||'设置失败')})}}).catch(function(){alert('请求失败')})}})



async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}async function loadMyFiles(){try{var r=await fetch('/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('myFileList').innerHTML='<p style="color:#999;text-align:center;padding:20px">暂无文件</p>';return}var h='<ul class="file-list">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class="file-item"><div class="file-info"><div class="file-name">'+f.original_name+'</div><div class="file-meta">'+f.size+'B</div></div><div class="file-actions"><a href="/download/'+f.id+'" download>下载</a><button class="af-del" data-fid="' + f.id + '" data-fname="'+f.original_name+'">删除</button></div></li>'}h+='</ul>';document.getElementById('myFileList').innerHTML=h}catch(e){}}



async function delFile(id){if(!confirm('确定删除？'))return;try{var r=await fetch('/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('删除成功','success');loadMyFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}







async function exportCD(mode){var pid=document.getElementById('cdpSelect').value;var m={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+m[mode]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+mode)}







async function exportCD(mode){var pid=document.getElementById('cdpSelect').value;var m={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+m[mode]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+mode)}











function loadCloudDataProjects(){fetch('/admin/cdprojects',{credentials:'include'}).then(function(r){return r.json()}).then(function(ps){window.cdProjects=ps;var sel=document.getElementById('cdpSelect');if(!sel)return;sel.innerHTML='';for(var i=0;i<ps.length;i++){var o=document.createElement('option');o.value=ps[i].id;o.text='ID:'+ps[i].id+' '+ps[i].name;sel.appendChild(o)}var p=ps[0];if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id="cdpToken_'+p.id+'">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick="resetToken('+p.id+')" class="mybtn btn btn-danger">重置TOKEN</button></td></tr>';loadCloudDataStats(p.id);loadCloudDataList(p.id,1)}})}



function loadCloudDataStats(pid){fetch('/admin/cdprojects/stats/'+pid,{credentials:'include'}).then(function(r){return r.json()}).then(function(s){document.getElementById('cdTotal').textContent=s.total;document.getElementById('cdNoRead').textContent=s.noRead;document.getElementById('cdRead').textContent=s.read})}



function loadCloudDataList(pid,page){var q=document.getElementById('cdQueryType').value;var s=document.getElementById('cdSearchText').value;var u='/admin/cddata/'+pid+'?page='+page+'&limit=20&queryType='+q+(s?'&search='+encodeURIComponent(s):'');fetch(u,{credentials:'include'}).then(function(r){return r.json()}).then(function(d){var tb=document.getElementById('cdDataBody');if(!tb)return;tb.innerHTML='';for(var i=0;i<d.items.length;i++){var x=d.items[i];var st=x.read?'已读取':'未读取';var sc=st==='已读取'?'green':'orange';var btnT=x.read?'修改为未读取':'修改为已读取';tb.innerHTML+='<tr><td>'+x.id+'</td><td>'+x.name+'</td><td><a href="#" onclick="downloadCD('+x.id+');return false">(点击下载)</a></td><td>'+x.md5+'</td><td>'+(x.t||'')+'</td><td><span style="color:'+sc+'">'+st+'</span></td><td><button onclick="toggleCDState('+x.id+')" class="mybtn btn btn-danger">'+btnT+'</button> <button onclick="if(confirm("确定删除?"))deleteCD('+x.id+')" class="mybtn btn btn-danger">删除数据</button></td></tr>'}window.cdPage=page;window.cdTotal=d.total;var pn=Math.ceil(d.total/20)||1;var ph='<li><a href="#" onclick="loadCloudDataList('+pid+',1);return false">首页</a></li><li><a href="#" onclick="loadCloudDataList('+pid+','+Math.max(1,page-1)+');return false">上一页</a></li>';for(var i=1;i<=pn;i++){ph+='<li class="'+(i===page?'active':'')+'"><a href="#" onclick="loadCloudDataList('+pid+','+i+');return false">'+i+'</a></li>'}ph+='<li><a href="#" onclick="loadCloudDataList('+pid+','+Math.min(pn,page+1)+');return false">下一页</a></li><li><a href="#" onclick="loadCloudDataList('+pid+','+pn+');return false">尾页</a></li>';document.getElementById('cdPagination').innerHTML=ph})}



function toggleCDState(cid){fetch('/admin/cddata/state/'+cid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)}})}



function deleteCD(cid){var pid=document.getElementById('cdpSelect').value;fetch('/admin/cddata/'+cid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)})}



function uploadTextFile(){var key=document.getElementById('cdUploadKey').value.trim();var fileInput=document.getElementById('cdUploadFile');if(!fileInput.files||!fileInput.files[0]){alert('请选择文件');return}if(!key)key=fileInput.files[0].name.replace(/\.[^.]+$/,'');var pid=document.getElementById('cdpSelect').value;if(!pid){alert('请先选择项目');return}var reader=new FileReader();reader.onload=function(e){var val=e.target.result;fetch('/admin/clouddata/add',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({key:key,value:val,project_id:parseInt(pid)})}).then(function(r){if(r.ok){document.getElementById('cdUploadStatus').textContent='上传成功: '+key;document.getElementById('cdUploadKey').value='';fileInput.value='';loadCloudDataList(pid,1)}else{alert('上传失败')}}).catch(function(){alert('上传失败')})};reader.readAsText(fileInput.files[0])}



function resetToken(pid){if(!confirm('重置后旧Token失效，确定重置吗?'))return;fetch('/admin/cdprojects/resettoken/'+pid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){document.getElementById('cdpToken_'+pid).textContent=d.token;showToast('重置成功','success')}})}



function resetAllRead(pid){if(!confirm('确定将所有数据设为未读取?'))return;fetch('/admin/cdprojects/resetallread/'+pid,{method:'POST',credentials:'include'}).then(function(){loadCloudDataStats(pid);loadCloudDataList(pid,1)})}



function createProject(){var n=prompt('请输入key标识符称:');if(!n)return;fetch('/admin/cdprojects',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({name:n})}).then(function(){loadCloudDataProjects();showToast('创建成功','success')})}



function deleteProject(){var pid=document.getElementById('cdpSelect').value;if(!confirm('删除项目会清空所有数据，确定删除吗?'))return;fetch('/admin/cdprojects/'+pid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataProjects();showToast('删除成功','success')})}



function exportCD(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+t[m]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+m)}



function batchDelete(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部数据',read:'已读取数据',unread:'未读取数据'};if(!confirm('确定删除'+t[m]+'?'))return;fetch('/admin/cddata/batch/'+pid+'?mode='+m,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,1);loadCloudDataStats(pid);showToast('删除成功','success')})}



function searchCD(){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,1)}



function downloadCD(cid){window.open('/admin/cddata/download/'+cid)}



function initCloudData(){var sel=document.getElementById('cdpSelect');if(!sel)return;sel.onchange=function(){var pid=this.value;if(!pid)return;var p=window.cdProjects.find(function(x){return x.id==pid});if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id="cdpToken_'+p.id+'">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick="resetToken('+p.id+')" class="mybtn btn btn-danger">重置TOKEN</button></td></tr>'}loadCloudDataStats(pid);loadCloudDataList(pid,1)};document.getElementById('cdQueryType').onchange=function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)};loadCloudDataProjects()}



document.addEventListener('DOMContentLoaded',initCloudData);



