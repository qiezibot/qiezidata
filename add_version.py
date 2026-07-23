# -*- coding: utf-8 -*-
"""Add cache-busting version to script tag"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# Replace <script> with <script?ver=xxx> concept - actually we add a random hash query param
# Better: add a nonce/meta tag or just change a comment in the script

# Simplest: add a version comment at the top of the admin script
# Find the script in _ADMIN template
old = b'<script>\r\nfunction switchPage(id,el)'
new = b'<script>\r\n/* v3 */\r\nfunction switchPage(id,el)'

if old in content:
    content = content.replace(old, new)
    with open('railway_file_server.py', 'wb') as f:
        f.write(content)
    print('Added version comment v3')
else:
    print('Pattern not found')

# Verify
with open('railway_file_server.py', 'rb') as f:
    content = f.read()
    
if b'/* v3 */' in content:
    print('v3 comment confirmed in file')
