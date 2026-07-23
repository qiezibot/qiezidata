import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'Size: {len(content)}, SHA: {sha}')

# Find the last <script> before </body> and add DOMContentLoaded event binding
body_end = content.find('</body>')
last_script = content.rfind('<script>', 0, body_end)
print(f'Last script at {last_script}')

# Find where this script ends
script_end = content.find('</script>', last_script)
print(f'Script ends at {script_end}')

# Add event listeners after last script
dom_ready_script = '''
<script>
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
</script>
'''

content = content[:script_end+9] + dom_ready_script + content[script_end+9:]
print('DOMContentLoaded event listeners added')

final = content.encode('utf-8')
print(f'Final size: {len(final)}')

import py_compile, tempfile, os
tmp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
tmp.write(final)
tmp.close()
try:
    py_compile.compile(tmp.name, doraise=True)
    print('Python syntax: OK')
except Exception as e:
    print(f'Python syntax error: {e}')
os.unlink(tmp.name)

payload = {
    'message': 'Add DOMContentLoaded event listeners for openProfile',
    'content': base64.b64encode(final).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push status: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
else:
    print(r2.text[:300])
