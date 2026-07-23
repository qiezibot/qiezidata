# -*- coding: utf-8 -*-
c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'rb').read()

# Find the problematic byte sequence for "无权" + broken char
# "无权" in UTF-8 is: e6 97 a0 e6 9d 83
target = b'\xe6\x97\xa0\xe6\x9d\x83\xef\xbf\xbd\xef\xbc\x9f'
# But the broken char might be different bytes
# Let's find "无权" in raw bytes
idx = c.find(b'\xe6\x97\xa0\xe6\x9d\x83')
count = 0
fixes = []
while idx >= 0 and count < 10:
    # Show the 10 bytes after "无权"
    after = c[idx+6:idx+20]
    print(f"Found '无权' at byte {idx}: after = {after.hex()} = {after}")
    # Find the next single-quote that closes the string
    quote_pos = c.find(b"'", idx + 6)
    if quote_pos >= 0:
        print(f"  Next single-quote at {quote_pos}, value: '{c[idx:quote_pos+1]}'")
        # Replace "无权...'" with "无权限'"
        old_bytes = c[idx:quote_pos+1]
        new_bytes = '\u65e0\u6743\u9650'.encode('utf-8') + b"'"
        fixes.append((idx, quote_pos+1, old_bytes, new_bytes))
    idx = c.find(b'\xe6\x97\xa0\xe6\x9d\x83', idx + 6)
    count += 1

# Apply fixes in reverse order
for start, end, old, new in reversed(fixes):
    c = c[:start] + new + c[end:]
    print(f"Fixed: {old} -> {new}")

print(f"\nFile size: {len(c)} bytes")
out = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py'
open(out, 'wb').write(c)
print("Written")
