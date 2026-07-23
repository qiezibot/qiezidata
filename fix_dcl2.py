c = open('railway_file_server.py', 'r', encoding='utf-8').read()

old_dcl = "DOMContentLoaded',function(){var sel=document.getElementById('cdpSelect');if(sel){sel.addEventListener('change',function(){var pid=this.value;if(pid){var p=window.cdProjects.find(x=>x.id==pid);if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>'}loadCloudDataStats(pid);loadCloudDataList(pid,1)loadCloudDataProjects(); }}});document.getElementById('cdQueryType').addEventListener('change',function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)});loadCloudDataProjects()\n}})}});"

new_dcl = "DOMContentLoaded',function(){var sel=document.getElementById('cdpSelect');if(sel){sel.addEventListener('change',function(){var pid=this.value;if(pid){var p=window.cdProjects.find(function(x){return x.id==pid});if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>'}loadCloudDataStats(pid);loadCloudDataList(pid,1)}});document.getElementById('cdQueryType').addEventListener('change',function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)});loadCloudDataProjects()}})"

assert old_dcl in c, 'DCL block not found!'
c = c.replace(old_dcl, new_dcl)
open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('OK size:', len(c))
