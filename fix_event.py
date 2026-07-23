# -*- coding: utf-8 -*-
"""Complete rewrite of loadUsers to use event delegation instead of inline onclick"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# New approach: 
# 1. Remove confirmDelete function (will use direct deleteUser with confirm)
# 2. Rewrite loadUsers to just render a data-id attribute on delete buttons
# 3. Add event delegation for delete buttons

old_loadUsers = b"async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td><td>'+(u.role==='admin'?'-':'<button onclick=\\\"confirmDelete('+u.id+',\\'+u.username+'\\')\\\" class=\\\"del-btn\\">\\u5220\\u9664</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}"

new_loadUsers = b"""async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td><td>'+(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}
document.getElementById('userTableBody').addEventListener('click',function(e){
  var btn=e.target.closest('.del-btn');
  if(!btn)return;
  var uid=parseInt(btn.getAttribute('data-uid'));
  var uname=btn.getAttribute('data-uname');
  if(confirm('确定要删除用户 '+uname+' 吗?此操作不可恢复!'))deleteUser(uid)
})"""

# Replace
if old_loadUsers in content:
    content = content.replace(old_loadUsers, new_loadUsers)
    with open('railway_file_server.py', 'wb') as f:
        f.write(content)
    print("Replaced loadUsers with event delegation")
else:
    print("Old pattern not found, trying partial match")
    # Find the async function loadUsers by locating the function
    a_idx = content.find(b'async function loadUsers')
    c_idx = content.find(b'async function confirmDelete')
    if a_idx >= 0 and c_idx > a_idx:
        print(f"Found loadUsers at {a_idx} to confirmDelete at {c_idx}")
        # Also need to remove the confirmDelete function
        d_idx = content.find(b'async function deleteUser', c_idx)
        section = content[a_idx:d_idx]
        print(f"Section length: {len(section)}")
        # Just replace with new versions
        full_replacement = new_loadUsers + b"\n"
        content = content[:a_idx] + full_replacement + content[d_idx:]
        with open('railway_file_server.py', 'wb') as f:
            f.write(content)
        print("Replaced both loadUsers and confirmDelete")
    else:
        print("Cannot find functions")

# Verify syntax
s_idx = content.find(b'<script>')
e_idx = content.find(b'</script>', s_idx)
script = content[s_idx+8:e_idx]
try:
    compile(script, '<test>', 'exec')
    print("Script syntax OK!")
except SyntaxError as e:
    print(f"Script syntax ERROR: {e}")
