# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# Correct fix: wrap with escaped single quotes: confirmDelete(id,'name')
# Template: onclick=\"confirmDelete('+u.id+',\\''+u.username+'\\')\"
# This produces: onclick="confirmDelete(2,'dad')"

idx = content.find(b'async function loadUsers')
end_idx = content.find(b'async function confirmDelete')

if idx >= 0 and end_idx > idx:
    new_js = "async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td><td>'+(u.role==='admin'?'-':'<button onclick=\\\"confirmDelete('+u.id+',\\''+u.username+'\\')\\\" class=\\\"del-btn\\\">\\u5220\\u9664</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}\n"
    
    content = content[:idx] + new_js.encode('utf-8') + content[end_idx:]
    
    with open('railway_file_server.py', 'wb') as f:
        f.write(content)
    print("Fixed!")

# Verify the output
if b'confirmDelete(' in content:
    idx2 = content.find(b'confirmDelete(')
    end2 = content.find(b')\\" class', idx2)
    print("Rendered onclick:", repr(content[idx2:end2+2]))
    
print("Done")
