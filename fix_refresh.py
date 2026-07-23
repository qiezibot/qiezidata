# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

idx = content.find(b'async function deleteUser')
end = content.find(b'async function loadMyFiles', idx)

# Replace location.reload() with inline fetch + re-render
# We need to re-fetch users and rebuild the table
# Since loadUsers() is not in window scope, we inline the logic

new_func = b'''async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}'''.encode('utf-8')

# Add the closing part
new_rest = b'''else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}

if r.ok part was already added tracking locally, let me just do the full replacement
'''.encode('utf-8')

# Just do the full string replacement properly
# Find the complete deleteUser function
old_func = content[idx:end]

# Build complete replacement
full_new = (
    b'async function deleteUser(uid){try{var r=await fetch(\'/admin/user/\'+uid,{method:\'DELETE\',credentials:\'include\'});'
    b'if(r.ok){'
    b'var r2=await fetch(\'/admin/users\',{credentials:\'include\'});'
    b'if(r2.status===401){window.location.href=\'/\';return}'
    b'var users=await r2.json();'
    b'var h=\'\';'
    b'for(var i=0;i<users.length;i++){'
    b'var u=users[i];'
    b"h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'"
    b"+'<td>'+(u.role==='admin'?'-':"
    b"'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\\u5220\\u9664</button>')"
    b"+'</td></tr>'}"
    b"document.getElementById('userTableBody').innerHTML=h"
    b'}else{var e=await r.json();alert(e.detail||\'\\u5220\\u9664\\u5931\\u8d25\')}'
    b'}catch(e){alert(\'\\u5220\\u9664\\u5931\\u8d25\')}}'
)

content = content[:idx] + full_new + content[end:]
with open('railway_file_server.py', 'wb') as f:
    f.write(content)

print('New deleteUser written!')

# Verify
idx2 = content.find(b'async function deleteUser')
end2 = content.find(b'async function loadMyFiles', idx2)
print(content[idx2:end2].decode('utf-8'))
