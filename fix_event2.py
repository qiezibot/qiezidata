# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# Find the loadUsers async function
a_idx = content.find(b'async function loadUsers')
c_idx = content.find(b'async function confirmDelete')

if a_idx >= 0 and c_idx > a_idx:
    # Also find the start of deleteUser (right after confirmDelete)
    d_idx = content.find(b'async function deleteUser', c_idx)
    
    # Remove the old loadUsers + confirmDelete
    # Keep the deleteUser function
    deleteUser_fn = content[d_idx:]
    
    # New loadUsers with event delegation
    new_js = (
        b"async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});"
        b"if(r.status===401){window.location.href='/';return}"
        b"var users=await r.json();var h='';"
        b"for(var i=0;i<users.length;i++){"
        b"var u=users[i];"
        b"h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>"
        b"h+='<td>'+(u.role==='admin'?'-'"
        b":'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button>')+'</td></tr>'}"
        b"document.getElementById('userTableBody').innerHTML=h"
        b"}catch(e){}}\n"
        b"document.addEventListener('click',function(e){"
        b"var btn=e.target.closest('.del-btn');"
        b"if(!btn)return;"
        b"var uid=parseInt(btn.getAttribute('data-uid'));"
        b"var uname=btn.getAttribute('data-uname');"
        b"if(confirm('确定要删除用户 '+uname+' 吗?此操作不可恢复!'))deleteUser(uid)})\n"
    )
    
    new_content = content[:a_idx] + new_js + deleteUser_fn
    with open('railway_file_server.py', 'wb') as f:
        f.write(new_content)
    print("Completed! Replaced loadUsers + confirmDelete with event delegation approach")
    
    # Verify script syntax
    s_idx = new_content.find(b'<script>')
    e_idx = new_content.find(b'</script>', s_idx)
    script = new_content[s_idx+8:e_idx]
    try:
        compile(script, '<test>', 'exec')
        print("Script syntax OK!")
    except SyntaxError as e:
        print(f"Script syntax ERROR: {e}")
else:
    print("Cannot find function boundaries")
