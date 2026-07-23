import sys, json

# Compare local vs remote template
c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'rb').read()
# Find _ADMIN
adm_marker = b'_ADMIN = """'
idx = c.find(adm_marker)
if idx >= 0:
    start = idx + len(adm_marker)
    end = c.find(b'"""', start)
    adm = c[start:end]
    print(f'Local _ADMIN: {len(adm)} bytes')
    # Check for surrogates
    text = adm.decode('utf-8', errors='surrogateescape')
    for i, ch in enumerate(text):
        if ord(ch) >= 0xD800 and ord(ch) <= 0xDFFF:
            print(f'  Surrogate at {i}: byte {adm[i:i+4].hex()}')
        elif ord(ch) > 0xFFFF:
            print(f'  Non-BMP at {i}: U+{ord(ch):04X}')
