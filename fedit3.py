with open('railway_file_server.py','r',encoding='utf-8') as f:
    c = f.read()

# 1. 在 loadUsers 行里：在 设为管理员</button> 后面加改密码按钮
old_lu = '设为管理员</button>\')+\'</td></tr>'
new_lu = '设为管理员</button>\'+\'<button onclick="cpwUser('+"'"+'+u.id+'+"'"+')" style="margin-left:5px;cursor:pointer">改密码</button>\')+\'</td></tr>'
if old_lu in c:
    c = c.replace(old_lu, new_lu, 1)
    print("loadUsers: patched")
else:
    print("loadUsers: NOT FOUND")
    # debug: find what's actually there
    idx = c.find('设为管理员')
    if idx > 0:
        print(f"  Found 设为管理员 at {idx}, context: {c[idx-20:idx+50]}")

# 2. 在 deleteUser 行里：在 删除</button> 后面加改密码按钮
# 注意：deleteUser 行有两个 '删除</button>' - 一个是 del-btn, 另一个是 .af-del
# 我们要找的是 del-btn 后面的那个
old_du = 'class="del-btn">删除</button>\')+\'</td></tr>'
new_du = 'class="del-btn">删除</button>\'+\'<button onclick="cpwUser('+"'"+'+u.id+'+"'"+')" style="margin-left:5px;cursor:pointer">改密码</button>\')+\'</td></tr>'
if old_du in c:
    c = c.replace(old_du, new_du, 1)
    print("deleteUser: patched")
else:
    print("deleteUser: NOT FOUND")
    idx = c.find('class="del-btn">删除</button>')
    if idx > 0:
        print(f"  Found at {idx}, context: {c[idx:idx+80]}")

# 3. 清理 - 把设管理员和改密码共用一行，使 UI 更紧凑
# 把 loadUsers 里的 '<button onclick=... style="...">改密码</button>' 放在 设为管理员 按钮旁边

with open('railway_file_server.py','w',encoding='utf-8') as f:
    f.write(c)

sz = len(c.encode('utf-8'))
print(f"\nFinal size: {sz} bytes (UTF-8)")
print(f"cpwUser function: {'Y' if 'function cpwUser' in c else 'N'}")
print(f"cpwUser( refs: {c.count('cpwUser(')}")  # function def + 2 UI refs = 3
print(f"change_password route: {'Y' if '/change_password' in c else 'N'}")
