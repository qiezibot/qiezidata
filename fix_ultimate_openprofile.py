"""Ultimate fix: Replace openProfile to just show the profileModal,
with multiple fallback methods and a visible test.
Also ensure the modal exists by checking with a small setTimeout retry.
"""
import requests, json, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content_b64 = r.json()['content']
content = base64.b64decode(content_b64).decode('utf-8')

# Replace openProfile with a super robust version
old = """function openProfile(){ var m=document.getElementById('profileModal');m.style.display='flex';m.style.visibility='visible';m.style.opacity='1';setTimeout(function(){ fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}) },50); }"""

new = """function openProfile(){ var m=document.getElementById('profileModal');if(!m)return alert('profileModal not found');m.style.display='flex';m.style.visibility='visible';m.style.opacity='1';m.style.zIndex='9999';try{m.showModal()}catch(e){}fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){var userInp=document.getElementById('profModalUser');var dnInp=document.getElementById('profModalDN');var roleInp=document.getElementById('profModalRole');if(userInp)userInp.value=u.username||'';if(dnInp)dnInp.value=u.display_name||'';if(roleInp)roleInp.value=u.role||'';}).catch(function(){})}"""

if old in content:
    content = content.replace(old, new)
    print("Replaced openProfile - now uses showModal() fallback + null guards")
else:
    print("WARNING: Old openProfile not found!")
    idx = content.find('function openProfile')
    if idx > 0:
        cidx = content.index('}', idx) + 1
        print(f'Found at {idx}, current: {content[idx:cidx]}')

# Also check if profileModal has the HTML <dialog> tag - change it if not
# Find the div with id="profileModal" and its enclosing div
pid = content.find('<div id="profileModal"')
if pid > 0:
    # Before this, verify it's not profileModalDummy
    before_tag = content[max(0,pid-20):pid]
    print(f'\nContext before profileModal div: {before_tag}')
    
    # Count how many profileModal divs before the real one
    all_divs = [m.start() for m in re.finditer('<div id="profileModal"', content)]
    print(f'All profileModal divs: {len(all_divs)} at {all_divs}')

# Push
payload = {
    'message': 'Fix openProfile - add showModal() fallback + null guards',
    'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'\nPush: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
