"""Replace all openProfile handlers with a single reliable one.
The _LOGIN template also has a DOMContentLoaded listener that binds click events
with preventDefault. This might interfere with the _ADMIN template's onclick.

Solution: Remove the _LOGIN template's listener and keep only the _ADMIN version.
"""
import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

# Find and remove the _LOGIN's DOMContentLoaded listener for openProfile
old_listener = """<script>
document.addEventListener("DOMContentLoaded",function(){
  var els=document.querySelectorAll("[onclick*='openProfile']");
  for(var i=0;i<els.length;i++){
    els[i].addEventListener("click",function(e){
      e.preventDefault();
      var m=document.getElementById("profileModal");
      if(m){m.style.display="flex";}
      fetch("/me",{credentials:"include"}).then(function(r){return r.json();}).then(function(u){
        var i1=document.getElementById("profModalUser");if(i1)i1.value=u.username||"";
        var i2=document.getElementById("profModalDN");if(i2)i2.value=u.display_name||"";
        var i3=document.getElementById("profModalRole");if(i3)i3.value=u.role||"";
      }).catch(function(){});
    });
  }
});
</script>"""

# This old listener should only appear once (in _LOGIN)
count = content.count(old_listener)
print(f'Old listener found: {count} times')

if count >= 1:
    content = content.replace(old_listener, '', 1)
    print('Removed old listener from _LOGIN')
else:
    print('Listener not found exactly - check for partial match')
    # Try partial match
    parts = ['document.addEventListener("DOMContentLoaded",function(){',
             'var els=document.querySelectorAll("[onclick*=\'openProfile\']");',
             'els[i].addEventListener("click",function(e){',
             'e.preventDefault();']
    for part in parts:
        c = content.count(part)
        print(f'  Part "{part[:40]}": {c}')
    
    # Find and remove by pattern
    start = content.find('document.addEventListener("DOMContentLoaded"')
    if start >= 0:
        # Check it has openProfile reference
        near = content[start:start+600]
        if 'openProfile' in near:
            end = content.find('</script>', start)
            full = content[start-8:end+9]  # include <script>...</script>
            print(f'\nFound listener at {start}:')
            print(full[:200])
            
            # Remove it
            old_start = content.rfind('<script>', 0, start)
            if old_start >= 0:
                old_start = old_start
            else:
                old_start = content.rfind('<script>\n', 0, start)
            end_tag = content.find('</script>', start) + 9
            removed = content[old_start:end_tag]
            content = content[:old_start] + content[end_tag:]
            print(f'Removed: {len(removed)} chars')

# Also make openProfile more robust - it should work with OR without the listener
old_op = """function openProfile(){ var m=document.getElementById('profileModal');if(!m)return alert('profileModal not found');m.style.display='flex';m.style.visibility='visible';m.style.opacity='1';m.style.zIndex='9999';fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){var userInp=document.getElementById('profModalUser');var dnInp=document.getElementById('profModalDN');var roleInp=document.getElementById('profModalRole');if(userInp)userInp.value=u.username||'';if(dnInp)dnInp.value=u.display_name||'';if(roleInp)roleInp.value=u.role||'';}).catch(function(){})}"""

new_op = """function openProfile(){ alert('openProfile called');var m=document.getElementById('profileModal');if(!m){alert('profileModal not found');return}m.style.display='flex';m.style.visibility='visible';m.style.opacity='1';m.style.zIndex='9999';fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){var userInp=document.getElementById('profModalUser');var dnInp=document.getElementById('profModalDN');var roleInp=document.getElementById('profModalRole');if(userInp)userInp.value=u.username||'';if(dnInp)dnInp.value=u.display_name||'';if(roleInp)roleInp.value=u.role||'';}).catch(function(){})}"""

if old_op in content:
    content = content.replace(old_op, new_op)
    print('Replaced openProfile with debug version')
else:
    print('openProfile version not matched')
    # Try to find and replace with broader search
    idx = content.find('function openProfile()')
    if idx >= 0:
        end_idx = content.find('function closeProfile()', idx)
        if end_idx < 0:
            end_idx = content.find('\nfunction closeProfile()', idx)
        print(f'openProfile at {idx}, ends at {end_idx}')
        print(f'Current: {content[idx:min(idx+200, end_idx)]}')

new_len = len(content)
print(f'\nSize: {new_len} (prev: {len(base64.b64decode(r.json()["content"]))})')

# Push
payload = {
    'message': 'Remove duplicate profile click listener, add debug alert',
    'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"][:12]}')
