with open('railway_file_server.py','r',encoding='utf-8') as f:
    c = f.read()

lines = c.split('\n')

# 1. 插入 cpwUser 函数
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith('async function loadUsers'):
        lines.insert(i, "function cpwUser(uid){var np=prompt('新密码(>4位)');if(!np||np.length<4){if(np)alert('需>=4字符');return}fetch('/admin/user/'+uid+'/change_password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:np}),credentials:'include'}).then(function(r){return r.json()}).then(function(d){alert(d.detail||'成功');loadUsers()})}")
        lines.insert(i+1, "")
        print(f"Inserted cpwUser before line {i}")
        break

# 2. 在 loadUsers 的行模板加按钮
for i, l in enumerate(lines):
    s = l.strip()
    # 找 loadUsers 里的 HTML 行 - 辨识: 包含 class="set-admin-btn"
    if 'loadUsers' not in s and 'cpwUser' not in s and 'set-admin-btn' in s:
        # 在 </button> 前找到 set-admin-btn 那个按钮
        # 找到 set-admin-btn 关闭按钮
        idx = s.find('设为管理员</button>')
        if idx > 0:
            # 在它后面加改密码按钮
            insert_btn = '<button onclick="cpwUser('+"'"+'+u.id+'+"'"+')" style="margin-left:5px;cursor:pointer">改密码</button>'
            new_s = s[:idx] + '设为管理员</button>' + insert_btn + s[idx+len('设为管理员</button>'):]
            lines[i] = l.replace(s, new_s)
            print(f"loadUsers row at line {i}: added cpw btn")
            break

# 3. 在 deleteUser 的行模板加按钮
for i, l in enumerate(lines):
    s = l.strip()
    if 'deleteUser' in s and 'del-btn' in s and 'cpwUser' not in s:
        idx = s.find('删除</button>')
        if idx > 0:
            # 找到第二个删除按钮（deleteUser行有两个 删除</button> 但第一个是 del-btn 按钮）
            # 实际上只有1个删除按钮在这个行
            insert_btn = '<button onclick="cpwUser('+"'"+'+u.id+'+"'"+')" style="margin-left:5px;cursor:pointer">改密码</button>'
            new_s = s[:idx] + '删除</button>' + insert_btn + s[idx+len('删除</button>'):]
            lines[i] = l.replace(s, new_s)
            print(f"deleteUser at line {i}: added cpw btn")
            break

c = '\n'.join(lines)
with open('railway_file_server.py','w',encoding='utf-8') as f:
    f.write(c)

# Verify
with open('railway_file_server.py','rb') as f:
    raw = f.read()
utf8 = c.encode('utf-8')
print(f"\nFinal size: {len(utf8)} bytes (UTF-8)")
print(f"CRLF file: {len(raw)} bytes")
has_cpw = 'function cpwUser' in c
has_route = "@app.post('/admin/user/{uid}/change_password')" in c
has_ui = 'cpwUser(' in c  # at least one onclick reference
print(f"cpwUser function: {'✅' if has_cpw else '❌'}")
print(f"change_password route: {'✅' if has_route else '❌'}")
print(f"UI button references: {'✅' if has_ui else '❌'}")
