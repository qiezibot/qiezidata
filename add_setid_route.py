import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the delete user route and add a set_id route after it
idx = content.find('@app.delete')
while idx >= 0:
    end = content.find('\n@app.', idx + 1)
    snippet = content[idx:end]
    if 'admin/user' in snippet:
        print(f'Found route: {snippet[:200]}')
        idx2 = content.find('def delete_user', idx)
        line_end = content.find('\n', idx2)
        print(f'Function starts: {content[idx2:line_end]}')
        
        # Show the complete function
        func_start = content.find('async def', idx2)
        func_end = content.find('\n@app.', func_start + 1)
        if func_end < 0:
            func_end = content.find('\n#', func_start + 1)
        print(f'\nFull delete_user function:')
        print(content[func_start:func_end])
        
        # Add set_id route after this function
        new_route = '''

@app.post('/admin/user/{uid}/set_id')
async def set_user_id(uid: int, new_id: int = Body(...), request: Request = None):
    if not request:
        return JSONResponse({'ok': False, 'detail': '无权限'}, status_code=403)
    admin_uid = request.state.user_id
    async with db_pool.acquire() as conn:
        # Check if admin
        row = await conn.fetchrow('SELECT role FROM users WHERE id=$1', admin_uid)
        if not row or row['role'] != 'admin':
            return JSONResponse({'ok': False, 'detail': '无权限'}, status_code=403)
        # Check target user exists
        target = await conn.fetchrow('SELECT id, username FROM users WHERE id=$1', uid)
        if not target:
            return JSONResponse({'ok': False, 'detail': '用户不存在'}, status_code=404)
        # Check new_id not taken
        conflict = await conn.fetchrow('SELECT id FROM users WHERE id=$1', new_id)
        if conflict:
            return JSONResponse({'ok': False, 'detail': f'ID {new_id} 已被占用'}, status_code=400)
        # Update ID
        await conn.execute('UPDATE users SET id=$1 WHERE id=$2', new_id, uid)
        # Also update files table
        await conn.execute('UPDATE files SET user_id=$1 WHERE user_id=$2', new_id, uid)
        return JSONResponse({'ok': True, 'msg': f'用户ID {uid} 已改为 {new_id}'})

'''
        content = content[:func_end] + new_route + content[func_end:]
        break
    idx = content.find('\n@app.', end)
    if idx < 0:
        break

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added set_id route')
