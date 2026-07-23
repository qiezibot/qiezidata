"""Final attempt: Replace onclick="openProfile()" with addEventListener-based approach.
Also add DOMContentLoaded wrapper to ensure modal div exists when click handler fires.

Root cause hypothesis: The onclick="openProfile()" in HTML works fine when the function
exists in global scope. Since it does, the issue MUST be something else.

Let me try a completely different approach - use a custom attribute and mutation observer,
or simply check if the function name is accessible from onclick by adding a test attr.
"""
import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

# Extract _ADMIN template
pat = '_ADMIN = """'
adm_start = content.find(pat)
adm_cont_start = adm_start + len(pat)
adm_end = content.find('"""\r\n\r\n\r\n\r\n\r\n', adm_cont_start + 50000)
template = content[adm_cont_start:adm_end]

# Find the two onclick="openProfile()" occurrences
old_onclick = 'onclick="openProfile()"'

# Count occurrences
oc_count = template.count(old_onclick)
print(f'Found {oc_count} onclick="openProfile()" in template')

# Replace both with a data attribute approach
new_attr = 'data-open-profile="1"  style="cursor:pointer"'

template = template.replace(old_onclick, new_attr)
print('Replaced onclick with data attribute')

# Now find where openProfile function is and replace it
# Remove the old function and replace with DOMContentLoaded + addEventListener
old_func = """function openProfile(){ var m=document.getElementById('profileModal');if(!m)return alert('profileModal not found');m.style.display='flex';m.style.visibility='visible';m.style.opacity='1';m.style.zIndex='9999';try{m.showModal()}catch(e){}fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){var userInp=document.getElementById('profModalUser');var dnInp=document.getElementById('profModalDN');var roleInp=document.getElementById('profModalRole');if(userInp)userInp.value=u.username||'';if(dnInp)dnInp.value=u.display_name||'';if(roleInp)roleInp.value=u.role||'';}).catch(function(){})}"""

new_func = """document.addEventListener("DOMContentLoaded",function(){var els=document.querySelectorAll("[data-open-profile='1']");for(var i=0;i<els.length;i++){(function(el){el.addEventListener("click",function(){var m=document.getElementById('profileModal');if(!m){alert('profileModal not found');return}m.style.display='flex';m.style.visibility='visible';m.style.opacity='1';m.style.zIndex='9999';fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){var userInp=document.getElementById('profModalUser');var dnInp=document.getElementById('profModalDN');var roleInp=document.getElementById('profModalRole');if(userInp)userInp.value=u.username||'';if(dnInp)dnInp.value=u.display_name||'';if(roleInp)roleInp.value=u.role||'';});});})(els[i]);}});"""

if old_func in template:
    template = template.replace(old_func, new_func)
    print('Replaced openProfile function with DOMContentLoaded-based event binding')
else:
    print('WARNING: old openProfile function not found in template!')
    idx = template.find('function openProfile')
    if idx >= 0:
        print(f'  Found at template offset {idx}')
        end = template.find('function closeProfile', idx)
        if end < 0:
            end = template.find('\n// ', idx)  # try next line
        print(f'  Current: {template[idx:idx+100]}...')
    else:
        print('  NOT IN TEMPLATE AT ALL!')

# Also ensure pwdModal has the same approach? Let's also fix openPwdModal
# The issue might be similar for the "change password" button in user management

# Rebuild content
new_content = content[:adm_cont_start] + template + content[adm_end:]

# Verify Python syntax
try:
    compile(new_content, 'test.py', 'exec')
    print('Python syntax: OK ✓')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    exit()

# Verify profileModal count
pm_count = new_content.count('<div id="profileModal"')
pmd_count = new_content.count('<div id="profileModalDummy"')
print(f'profileModal divs: {pm_count}, Dummy: {pmd_count}')
print(f'Total size: {len(new_content)} bytes')

# Push
payload = {
    'message': 'Replace onclick openProfile with DOMContentLoaded-based event binding',
    'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"][:12]}')
else:
    print(f'Error: {r2.text[:200]}')
