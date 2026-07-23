# -*- coding: utf-8 -*-
c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'r', encoding='utf-8').read()

# Fix 1: loadUsers - add password column
idx = c.find('function loadUsers')
row_start = c.find("h+='<tr><td>'", idx)
row_end = c.find("}catch(e){}}", row_start) + 12

old_row = c[row_start:row_end]
print("Old loadUsers row part:")
print(old_row)
print()

# The old row ends with '</td></tr>', insert password cell before that
# Find the last occurrence of </td></tr>' 
old_end = old_row.rfind("'</td></tr>'")
new_part = old_row[:old_end] + "'+'<td><button onclick=\"openPwdModal(\"+u.id+\",'\"+u.username+\"')\" style=\"padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer\">修改密码</button></td>' + '</td></tr>'"
# But careful: the original already ends with '</td></tr>' 
# Let's be more precise: the original has ...+'</td></tr>'
# We want: ...+'</td>'+'<td>...modify pwd button...</td></tr>'

old_tail = "'+'</td></tr>'"
new_tail = "'+'<td><button onclick=\"openPwdModal(\"+u.id+\",'\"+u.username+\"')\" style=\"padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer\">修改密码</button></td>'+'</td></tr>'"

if old_row.endswith(old_tail):
    new_row = old_row[:-len(old_tail)] + new_tail
    c = c[:row_start] + new_row + c[row_end:]
    print("loadUsers row updated (tail replace)")
else:
    print("loadUsers row does NOT end with expected tail")
    print("Last 100 chars:", repr(old_row[-100:]))

# Fix 2: deleteUSer rebuild rows 
idx2 = c.find('async function deleteUser')
if idx2 >= 0:
    row_start2 = c.find("h+='<tr><td>'", idx2)
    row_end2 = c.find("}catch(e){}}", row_start2) + 12
    old_row2 = c[row_start2:row_end2]
    print()
    print("deleteUser row part:")
    print(old_row2[:300])
    print("...")
    print(old_row2[-100:])
    
    if old_row2.endswith(old_tail):
        new_row2 = old_row2[:-len(old_tail)] + new_tail
        c = c[:row_start2] + new_row2 + c[row_end2:]
        print("deleteUser rebuild rows updated")
    else:
        print("deleteUser row does NOT end with expected tail")
        print("Last 100 chars:", repr(old_row2[-100:]))
else:
    print("deleteUser not found")

# Fix 3: Check GET /me - might have been doubled
me_count = c.count('async def get_me')
print(f"\nasync def get_me count: {me_count}")
if me_count > 1:
    # There's a duplicate - remove the old one
    print("Need to check for duplicates")

# Check POST /me exists
if 'def update_me' in c:
    print("POST /me (update_me) exists: YES")
else:
    print("POST /me (update_me) exists: NO - adding it")
    # The get_me route should be before change_password routes
    # Add POST /me right after GET /me
    get_me_end = c.find('return user', c.find('def get_me')) + 11
    post_me = '''

@app.post('/me')


async def update_me(request: Request):


    uid = _require(request)


    data = await request.json()


    dn = data.get('display_name', '')


    if dn:


        if use_pg:


            await db_execute('UPDATE users SET display_name=$1 WHERE id=$2', dn, uid)


        else:


            await db_execute('UPDATE users SET display_name=? WHERE id=?', dn, uid)


    return JSONResponse({'ok': True})'''
    
    c = c[:get_me_end] + '\n\n' + post_me + c[get_me_end:]

# Write
open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'w', encoding='utf-8').write(c)
print("\nWritten!")
print("File size:", len(c), "bytes")
