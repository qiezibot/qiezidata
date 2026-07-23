# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    data = f.read()

# Locate boundaries
a_idx = data.find(b'async function loadUsers')
c_idx = data.find(b'async function confirmDelete')
d_idx = data.find(b'async function deleteUser', c_idx)

if a_idx >= 0 and d_idx > a_idx:
    # New loadUsers: use data attributes and global event listener
    delete_btn_code = "'<button data-uid=\u0022'+u.id+'\u0022 data-uname=\u0022'+u.username+'\u0022 class=\u0022del-btn\u0022>\u5220\u9664</button>')"
    
    new_loadUsers = (
        "async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});"
        "if(r.status===401){window.location.href='/';return}"
        "var users=await r.json();var h='';"
        "for(var i=0;i<users.length;i++){var u=users[i];"
        "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'"
        "+'<td>'+(u.role==='admin'?'-':" + delete_btn_code + "+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}\n"
        "document.getElementById('userTableBody').addEventListener('click',function(e){"
        "var btn=e.target.closest('.del-btn');"
        "if(!btn)return;"
        "var uid=parseInt(btn.getAttribute('data-uid'));"
        "var uname=btn.getAttribute('data-uname');"
        "if(confirm('\u786e\u5b9a\u8981\u5220\u9664\u7528\u6237 '+uname+' \u5417?\u6b64\u64cd\u4f5c\u4e0d\u53ef\u6062\u590d!'))deleteUser(uid)})\n"
    )
    
    # Replace: loadUsers + confirmDelete → loadUsers (event delegation)
    new_content = data[:a_idx] + new_loadUsers.encode('utf-8') + data[d_idx:]
    
    with open('railway_file_server.py', 'wb') as f:
        f.write(new_content)
    print("Done! Replaced functions")
    
    # Verify
    s_idx = new_content.find(b'<script>')
    e_idx = new_content.find(b'</script>', s_idx)
    script = new_content[s_idx+8:e_idx]
    try:
        compile(script, '<test>', 'exec')
        print("Script compiles OK!")
    except SyntaxError as e:
        print(f"Script syntax ERROR: {e}")
    
    # Show the onclick part
    idx2 = new_content.find(b'data-uid')
    print(f"data-uid at {idx2}")
    print(repr(new_content[idx2-20:idx2+80]))
else:
    print("Cannot find function boundaries")
