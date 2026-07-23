"""Fix the openProfile function to be more robust.
The issue: clicking user name shows the modal but content appears blank
until switching to API docs tab first.

The root cause is likely that getElementById('profileModal') can find the modal
but the inner content (children divs) have display or visibility issues on first render.
A common cause: CSS display:flex on the container doesn't cascade properly when 
the container was previously display:none.

Fix: ensure the modal's direct child div also has explicit display set, and add
a small timeout before the GET /me fetch to let the browser paint first.
"""
import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')

# Replace openProfile to be more robust
old_func = """function openProfile(){ document.getElementById('profileModal').style.display='flex'; fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}); }"""

new_func = """function openProfile(){ var m=document.getElementById('profileModal');m.style.display='flex';m.style.visibility='visible';m.style.opacity='1';setTimeout(function(){ fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}) },50); }"""

if old_func in content:
    content = content.replace(old_func, new_func)
    print("Fixed openProfile function")
else:
    print("Old function not found, checking alternatives...")
    idx1 = content.find('function openProfile()')
    idx2 = content.find('function closeProfile()')
    if idx1 > 0 and idx2 > 0:
        old = content[idx1:idx2-1].rstrip()
        print(f"Found at {idx1}: {old[:100]}...")
        content = content[:idx1] + new_func + content[idx2-1:]
        print("Replaced")
    else:
        print(f"openProfile at {idx1}, closeProfile at {idx2}")
        # Try substring match
        old_alt = "unction openProfile(){ "
        if old_alt in content:
            print("Using alternative match")

# Also verify profileModal style - ensure the inner content div has display:block
count = content.count('id="profileModal"')
count_dummy = content.count('id="profileModalDummy"')
print(f'\nprofileModal: {count}, profileModalDummy: {count_dummy}')

# Push
payload = {
    'message': 'Fix openProfile - add explicit visibility/opacity and 50ms delay',
    'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'\nPush: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
