# -*- coding: utf-8 -*-
import re

with open('railway_file_server.py', 'rb') as f:
    raw = f.read()

content = raw.decode('utf-8', 'replace')

# Fix _USER template: /my/ -> /  and /my/file/delete/ -> /delete/
# Find the _USER template string
# Pattern: _USER = """\ ... """ 
start = content.find('_USER = """\\')
if start < 0:
    start = content.find('_USER = """')
    
if start >= 0:
    print(f'_USER found at {start}')
    # End of _USER template: find the closing """ after _LOGIN
    user_end_content = content[start:]
    # Find _LOGIN after _USER
    login_start = user_end_content.find('_LOGIN = """\\')
    if login_start < 0:
        login_start = user_end_content.find('_LOGIN = """')
    
    if login_start >= 0:
        user_template = user_end_content[:login_start]
        # Replace /my/ with / (but not /my/ in URLs where it's part of a path)
        # /my/files -> /files
        # /my/file/delete/ -> /delete/
        old_user = user_template
        user_template = user_template.replace("/my/files", "/files")
        user_template = user_template.replace("/my/file/delete/", "/delete/")
        
        if old_user != user_template:
            new_content = content[:start] + '_USER = """\\' + user_template + content[start + len(old_user):]
            with open('railway_file_server.py', 'wb') as f:
                f.write(new_content.encode('utf-8'))
            print('Fixed /my/ routes in _USER template')
        else:
            print('No /my/ routes found to fix')
    else:
        print('Cannot find _LOGIN marker')
else:
    print('_USER not found')
    # Also check if delMyFile exists
    if '/my/' in content:
        print('But /my/ exists in content')
