"""Show _ADMIN template start and check for modal content"""
import requests, base64

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
raw = base64.b64decode(r.json()['content']).decode('utf-8')

# Show the boundary between _LOGIN end and _ADMIN start
print('=== Boundary area ===')
print(raw[67800:68500])
print()

# Now find the actual _ADMIN content  
adm_start = raw.find('_ADMIN = """')
adm_cont_start = adm_start + len('_ADMIN = """')
# The template starts with \< (escape backslash-newline or something?)
first_chars = raw[adm_cont_start:adm_cont_start+200]
print('=== _ADMIN first 200 chars ===')
print(repr(first_chars))
print()

# Check if _ADMIN template ends before the full page
adm_end = raw.find('"""\n# ===== ', adm_cont_start + 50000)
if adm_end < 0:
    adm_end = raw.find('"""\n\n\n\n', adm_cont_start + 50000)
if adm_end < 0:
    adm_end = raw.rfind('"""')
print(f'_ADMIN template: {adm_cont_start} to {adm_end}')
print(f'Length: {adm_end - adm_cont_start}')

# Show template ending
print('\n=== _ADMIN last 200 chars ===')
print(repr(raw[adm_end-200:adm_end+50]))
