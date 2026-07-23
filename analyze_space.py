import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 压缩：超过 2 个连续空行的缩到 2 个（保留代码间的空行）
lines = c.split('\n')
result = []
empty_run = 0
for line in lines:
    if not line.strip():
        empty_run += 1
        if empty_run <= 2:
            result.append('')
    else:
        empty_run = 0
        result.append(line)
c2 = '\n'.join(result)
print(f'Original: {len(c)} chars, {len(lines)} lines')
print(f'Compressed: {len(c2)} chars, {len(result)} lines')
print(f'Saved: {len(c) - len(c2)} chars')

# 可用空间（按 86KB 上限）
avail = 86000 - len(c2)
print(f'Available for UI: ~{avail} bytes')

# 如果有空间，加改密码 UI
if avail > 0:
    # 极简版：只加 admin 用户表的"修改密码"按钮 + 一个模态框
    # 不做个人资料模态框，只做改密码的
    extra = """<div id=pwdModal class=modal style=display:none><div class=modal-content style=max-width:380px><span class=modal-close onclick=pm()>×</span><h3>修改用户密码</h3><p id=pwdi style=color:#666></p><div class=form-group><label>新密码</label><input id=pwdnp type=password></div><button class=btn onclick=pwds()>确认</button><div id=pwdem style=display:none></div></div></div><script>function pm(){document.getElementById('pwdModal').style.display='none'}function pwdm(uid){document.getElementById('pwdModal').style.display='flex';document.getElementById('pwdi').textContent='用户: '+uid;document.getElementById('pwdnp').value='';var em=document.getElementById('pwdem');em.style.display='none'}function pwds(){var np=document.getElementById('pwdnp').value;var em=document.getElementById('pwdem');em.style.display='none';if(np.length<4){em.textContent='至少4个字符';em.style.display='block';return}var uid=document.getElementById('pwdi').textContent.split(': ')[1];fetch('/admin/user/'+uid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:np})}).then(r=>r.json()).then(d=>{d.ok?(em.textContent='已修改',em.style.color='#27ae60',setTimeout(function(){document.getElementById('pwdModal').style.display='none'},1500)):(em.textContent=d.detail||'失败',em.style.color='#e74c3c');em.style.display='block'})}</script>"""
    print(f'Extra size: {len(extra)}')
    print(f'After adding: {len(c2) + len(extra)}')
    
    if len(c2) + len(extra) <= 86000:
        print('FITS!')
    else:
        print(f'Over by {len(c2) + len(extra) - 86000} bytes')
