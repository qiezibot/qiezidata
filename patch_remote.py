# -*- coding: utf-8 -*-
"""
Strategy: Download the original file from GitHub (raw), then apply surgical patches.
Don't re-encode anything, work in binary mode to preserve original bytes.
"""
import urllib.request

# Download original
url = 'https://raw.githubusercontent.com/qiezibot/qiezidata/main/railway_file_server.py'
resp = urllib.request.urlopen(url)
raw = resp.read()

# Save original for reference
open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_original.py', 'wb').write(raw)

# Parse as text to find locations
text = raw.decode('utf-8')
print(f"Downloaded {len(raw)} bytes")

# Find the _ADMIN template boundaries
adm_start = text.find('_ADMIN = """')
print(f"ADMIN starts at byte: {adm_start}")
# Find the closing triple quote of _ADMIN
# It's: """ followed by \n\n\n etc.
adm_end_marker = '"""\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n# ---- CloudData Project API ----'
adm_end = text.find('"""\n\n\n\n\n\n', text.find('# ---- CloudData'))
print(f"ADMIN ends at: {adm_end}")

# Find JS block boundaries
lu_start = text.find('function loadUsers')
print(f"loadUsers at: {lu_start}")

lu_before = text.find('function loadMyFiles')
print(f"loadMyFiles at: {lu_before}")

# Find me route
me_start = text.find("@app.get('/me')")
print(f"/me route at: {me_start}")

# Check encoding health
idx = text.find("'detail': '")
while idx >= 0:
    snippet = text[idx:idx+30]
    if any(ord(c) > 127 for c in snippet):
        print(f"  Non-ASCII in detail at {idx}: {repr(snippet)}")
    idx = text.find("'detail': '", idx + 1)

print("\nAll patches identified successfully")
