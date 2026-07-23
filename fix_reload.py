# -*- coding: utf-8 -*-
"""Fix deleteUser to use location.reload() instead of calling loadUsers() which is not in window scope"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# Find deleteUser function
idx = content.find(b'async function deleteUser')
if idx < 0:
    print("deleteUser not found!")
    exit()

# Find the showToast calls in deleteUser and replace with direct approach
# showToast not defined in the script, so remove it
target = b"showToast('\xe5\x88\xa0\xe9\x99\xa4\xe6\x88\x90\xe5\x8a\x9f','success');location.reload()"
replacement = b"location.reload()"

# Also handle the old loadUsers version if still present
target_old = b"showToast('\xe5\x88\xa0\xe9\x99\xa4\xe6\x88\x90\xe5\x8a\x9f','success');loadUsers()"
replacement_old = b"location.reload()"

if target in content:
    content = content.replace(target, replacement)
    with open('railway_file_server.py', 'wb') as f:
        f.write(content)
    print("Replaced loadUsers() with location.reload() in deleteUser")
else:
    print("Pattern not found, trying different encoding")
    # Show bytes around deleteUser
    end = content.find(b'async function loadMyFiles', idx)
    section = content[idx:end]
    if b'loadUsers()' in section:
        print("loadUsers() found in deleteUser, but showToast pattern didn't match")
        print(repr(section[section.find(b'loadUsers()')-30:section.find(b'loadUsers()')+15]))
    else:
        print("No loadUsers() call in deleteUser function")
        print(repr(section[:300]))
