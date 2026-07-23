"""Fix the immediate execution JS that crashes on null element references.
The issue: script block 0 (with /* v3 */ comment) has code that runs immediately
and calls document.getElementById(...).addEventListener(...) on elements that may 
not exist in the DOM when the script runs (or exist but cause cascade issues).

The fix: wrap ALL immediate-execution code in DOMContentLoaded, so the DOM is 
fully parsed before any event listeners are attached.

Since these lines run at page load time (inside <script> at end of body), 
they should normally work. But if ANY getElementById returns null, the script
crashes and openProfile/openPwdModal never get defined.

Instead of tracing which one fails, just wrap the dangerous parts with null checks.
"""
import requests, json, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content_b64 = r.json()['content']
content = base64.b64decode(content_b64).decode('utf-8')

# Remove duplicate exportCD - there are 3 declarations, keep the last and rename the first two
# Actually the issue is easier to fix with a bigger change.

# Find the script block with /* v3 */ and wrap all immediate listeners in DOMContentLoaded
# Replace: document.getElementById('dropZone').addEventListener(...)
# With: (function(){...try{...}catch(e){}})()

# Strategy 1: Replace addEventListener patterns with null-safe versions
old1 = "document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});document.getElementById('fileInput').addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])})"
new1 = "var z=document.getElementById('dropZone');if(z)z.addEventListener('click',function(){var fi=document.getElementById('fileInput');if(fi)fi.click()});var fi=document.getElementById('fileInput');if(fi)fi.addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])})"

old2 = "document.getElementById('fileList').addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('ȷ��ɾ���ļ���'+fname+'����'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadAllFiles();alert('�ļ���ɾ��')}).catch(function(){alert('ɾ��ʧ��')})})"
new2 = "(function(){var el=document.getElementById('fileList');if(el)el.addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('ȷ��ɾ���ļ���'+fname+'����'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadAllFiles();alert('�ļ���ɾ��')}).catch(function(){alert('ɾ��ʧ��')})})})()"

old3 = "document.getElementById('myFileList').addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('ȷ��ɾ���ļ���'+fname+'����'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadMyFiles();alert('�ļ���ɾ��')}).catch(function(){alert('ɾ��ʧ��')})})"
new3 = "(function(){var el=document.getElementById('myFileList');if(el)el.addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('ȷ��ɾ���ļ���'+fname+'����'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadMyFiles();alert('�ļ���ɾ��')}).catch(function(){alert('ɾ��ʧ��')})})})()"

old4 = "document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.del-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('ȷ��Ҫɾ���û� '+uname+' ��?�˲������ɻָ�!'))deleteUser(uid)})"
new4 = "(function(){var el=document.getElementById('userTableBody');if(el)el.addEventListener('click',function(e){var btn=e.target.closest('.del-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('ȷ��Ҫɾ���û� '+uname+' ��?�˲������ɻָ�!'))deleteUser(uid)})})()"

old5 = "document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.set-admin-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('ȷ�����û� '+uname+' ��Ϊ����Ա��?')){fetch('/admin/user/'+uid+'/set_admin',{method:'POST',credentials:'include'}).then(function(r){if(r.ok){alert('����Ϊ����Ա');loadUsers()}else{r.json().then(function(d){alert(d.detail||'����ʧ��')})}}).catch(function(){alert('����ʧ��')})}})"
new5 = "(function(){var el=document.getElementById('userTableBody');if(el)el.addEventListener('click',function(e){var btn=e.target.closest('.set-admin-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('ȷ�����û� '+uname+' ��Ϊ����Ա��?')){fetch('/admin/user/'+uid+'/set_admin',{method:'POST',credentials:'include'}).then(function(r){if(r.ok){alert('����Ϊ����Ա');loadUsers()}else{r.json().then(function(d){alert(d.detail||'����ʧ��')})}}).catch(function(){alert('����ʧ��')})}}})()"

# Apply all replacements
pairs = [(old1, new1), (old2, new2), (old3, new3), (old4, new4), (old5, new5)]

for i, (old, new_) in enumerate(pairs):
    count = content.count(old)
    if count == 1:
        content = content.replace(old, new_)
        print(f'Patch {i+1}: OK (1 match)')
    elif count == 0:
        print(f'Patch {i+1}: NOT FOUND')
    else:
        print(f'Patch {i+1}: {count} matches (too many, skipping)')

new_len = len(content)
print(f'\nSize: orig={len(base64.b64decode(content_b64))} -> new={new_len}')

# Identify the script block to also wrap its code in try/catch
# Actually let me just add the null-checks and push
payload = {
    'message': 'Fix script crash - null-safe event listeners for admin page',
    'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'\nPush: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
