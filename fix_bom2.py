# -*- coding: utf-8 -*-
import re

c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'r', encoding='utf-8').read()

# The problematic characters are '无权' followed by a malformed char
# Let's find all instances of the pattern
# Using the Unicode REPLACEMENT CHARACTER (U+FFFD) or other broken chars

# Strategy: find all places where "detail": '...' contains broken chars
# Replace with proper Chinese

# Pattern 1: '无权' + broken char
# First, find the actual broken character
idx = c.find("'detail': '无权")
while idx >= 0:
    # Find the closing quote
    end_quote = c.find("'", idx + 15)
    if end_quote >= 0:
        broken = c[idx:end_quote+1]
        print(f"Found: {repr(broken)}")
        # Replace with '无权限'
        new_str = "'detail': '无权限'"
        c = c[:idx] + new_str + c[end_quote+1:]
        print(f"  -> {repr(new_str)}")
    idx = c.find("'detail': '无权", idx + 5)

# Also find where '无权' appears in route strings (not dict values)
idx = c.find("'无权限'")
if idx >= 0:
    print(f"\nFound correct '无权限' at {idx}: {repr(c[idx-20:idx+30])}")

open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'w', encoding='utf-8').write(c)
print("\nDone")
