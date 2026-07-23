# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# Fix: replace JSON.stringify(u.username) with just u.username
# The problem is JSON.stringify adds quotes around the value, breaking HTML onclick
# We already have onclick wrapping in the outer template, so just use the raw username

# Find and replace in the JS block
old = b"JSON.stringify(u.username)"
new = b"u.username"

count = content.count(old)
print(f"Found {count} occurrences")

content = content.replace(old, new)

with open('railway_file_server.py', 'wb') as f:
    f.write(content)

# Verify
idx = content.find(b'confirmDelete')
if idx >= 0:
    # find the end of this line
    end = content.find(b'\n', idx)
    print(repr(content[idx:end+1]))
print("Done")
