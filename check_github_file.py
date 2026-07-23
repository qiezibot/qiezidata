import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get the current file from GitHub
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'GitHub file: {len(content)} bytes, SHA: {sha}')

# Find admin template
adm_marker = '_ADMIN = """'
adm_start = content.find(adm_marker)
adm_content_start = content.index('"""', adm_start) + 3
adm_end = content.find('"""\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n# ---- CloudData', adm_content_start)
adm = content[adm_content_start:adm_end]
print(f'Admin template: {len(adm)} bytes')

# Check what's in the admin template
has_prof_div = 'id="profileModal"' in adm
has_pwd_div = 'id="pwdModal"' in adm
has_dcl = 'DOMContentLoaded' in adm
print(f'Has profileModal div: {has_prof_div}')
print(f'Has pwdModal div: {has_pwd_div}')
print(f'Has DOMContentLoaded: {has_dcl}')

# Count profileModal references
prof_count = content.count('profileModal')
pwd_count = content.count('pwdModal')
print(f'profileModal total: {prof_count}')
print(f'pwdModal total: {pwd_count}')
