with open('railway_file_server.py','r',encoding='utf-8') as f:
    c = f.read()

lines = c.split('\n')

# 找到 set_admin 和 set_id
set_admin_line = None
set_id_line = None
for i, l in enumerate(lines):
    if l.startswith("@app.post('/admin/user/{uid}/set_admin')"):
        set_admin_line = i
    elif l.startswith("@app.post('/admin/user/{uid}/set_id')"):
        set_id_line = i
        break

print(f'set_admin at {set_admin_line}, set_id at {set_id_line}')

# 替换 set_admin 到 set_id 之间的内容
new_lines = lines[:set_admin_line]
new_lines.append("@app.post('/admin/user/{uid}/change_password')")
new_lines.append("async def cpw_admin(uid: int, request: Request):")
new_lines.append("    admin = await _user(_require(request))")
new_lines.append("    if not admin or admin['role'] != 'admin':")
new_lines.append("        return JSONResponse({'ok': False, 'detail': '无权限'})")
new_lines.append("    data = await request.json()")
new_lines.append("    np = data.get('new_password', '')")
new_lines.append("    if not np or len(np) < 4:")
new_lines.append("        return JSONResponse({'ok': False, 'detail': '密码需至少4个字符'})")
new_lines.append("    if use_pg:")
new_lines.append("        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(np), uid)")
new_lines.append("    else:")
new_lines.append("        _DB[uid]['password_hash'] = _hash(np)")
new_lines.append("    return JSONResponse({'ok': True, 'detail': '密码已修改'})")
new_lines.append("")
new_lines.append(lines[set_admin_line])  # set_admin original
new_lines.extend(lines[set_admin_line+1:set_id_line])
new_lines.extend(lines[set_id_line:])

c = '\n'.join(new_lines)
with open('railway_file_server.py','w',encoding='utf-8') as f2:
    f2.write(c)
print("Done! Wrote new route.")
