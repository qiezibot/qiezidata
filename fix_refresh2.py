# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

idx = content.find(b'async function deleteUser')
end = content.find(b'async function loadMyFiles', idx)

# Build clean replacement using string, not bytes literal
new_js = (
    "async function deleteUser(uid){try{"
    "var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});"
    "if(r.ok){"
    "var r2=await fetch('/admin/users',{credentials:'include'});"
    "if(r2.status===401){window.location.href='/';return}"
    "var users=await r2.json();"
    "var h='';"
    "for(var i=0;i<users.length;i++){"
    "var u=users[i];"
    "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'"
    "+'<td>'+(u.role==='admin'?'-'"
    ":'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button>')"
    "+'</td></tr>'}"
    "document.getElementById('userTableBody').innerHTML=h"
    "}else{var e=await r.json();alert(e.detail||'\u5220\u9664\u5931\u8d25')}"
    "}catch(e){alert('\u5220\u9664\u5931\u8d25')}}"
)

content = content[:idx] + new_js.encode('utf-8') + content[end:]
with open('railway_file_server.py', 'wb') as f:
    f.write(content)

print('New deleteUser written!')

# Verify
idx2 = content.find(b'async function deleteUser')
end2 = content.find(b'async function loadMyFiles', idx2)
print(content[idx2:end2].decode('utf-8'))

# Verify no showToast in deleteUser
if b'showToast' in content[idx2:end2]:
    print('WARNING: showToast still present!')
else:
    print('OK: no showToast in deleteUser')
