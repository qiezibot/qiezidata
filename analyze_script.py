# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# Find the admin HTML template
idx = content.find(b'_ADMIN = ')
if idx >= 0:
    script_idx = content.find(b'<script>', idx)
    close_idx = content.find(b'</script>', script_idx)
    print(f'Admin script from {script_idx} to {close_idx}')
    print(f'Length: {close_idx - script_idx}')
    
    # Extract the script content (between <script> and </script>)
    script_start = script_idx + len(b'<script>')
    script_end = close_idx
    script = content[script_start:script_end]
    print(f'Script content length: {len(script)}')
    
    # Check for the loadUsers function
    if b'loadUsers' in script:
        # Find the async function declaration, not the call in switchPage
        lu_idx = script.find(b'async function loadUsers')
        print(f'async function loadUsers found at offset {lu_idx}')
        
        # Find the function boundaries
        # The function starts with 'async function loadUsers()' and ends with 'catch(e){}'
        end_of_func = script.find(b'catch(e){}', lu_idx)
        if end_of_func > 0:
            print(f'Function snippet: {repr(script[lu_idx:end_of_func+50])}')
            print(f'Function length: {end_of_func + 50 - lu_idx}')
        
        # Check for confirm in the function
        confirm_idx = script.find(b'confirm', lu_idx)
        if confirm_idx > 0 and confirm_idx < end_of_func:
            print(f'confirm at {confirm_idx}: {repr(script[confirm_idx-10:confirm_idx+80])}')
    
    # Check imnportant: is there a newline after loadUsers
    el_idx = script.find(b"document.getElementById('userTableBody')")
    if el_idx > 0:
        print(f'userTableBody found at {el_idx}')
        # Show 20 bytes before
        print(f'  before: {repr(script[el_idx-15:el_idx])}')
        print(f'  after:  {repr(script[el_idx:el_idx+50])}')
