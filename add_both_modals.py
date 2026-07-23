import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'Size: {len(content)}, SHA: {sha}')

adm_marker = '_ADMIN = """'
adm_start = content.find(adm_marker)
adm_content_start = content.index('"""', adm_start) + 3
adm_end = content.find('"""\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n# ---- CloudData', adm_content_start)
adm = content[adm_content_start:adm_end]

body_end = adm.find('</body></html>')

# Add pwdModal (admin change password)
pwd_html = '''
<div id="pwdModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center">
<div style="background:#fff;border-radius:12px;padding:24px;width:380px;max-width:90%;box-shadow:0 10px 40px rgba(0,0,0,.3)">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
<h3 id="pwdModalTitle" style="margin:0;font-size:16px;color:#333">修改密码</h3><button onclick="closePwdModal()" style="background:none;border:none;font-size:20px;cursor:pointer;color:#999">&times;</button>
</div>
<p style="font-size:13px;color:#555;margin-bottom:12px">为用户设置新密码</p>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">新密码</label><input id="pwdNewInput" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="至少4个字符"></div>
<div class="input-group" style="margin-bottom:16px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">确认新密码</label><input id="pwdConfirmInput" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="再次输入新密码"></div>
<button id="pwdModalBtn" onclick="submitPwdModal()" style="padding:10px 24px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px">确认修改</button>
<p id="pwdModalMsg" style="font-size:13px;margin-top:8px;display:none"></p>
</div>
</div>
'''

# Add profileModal (self profile edit + change password)
profile_html = '''
<div id="profileModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center">
<div style="background:#fff;border-radius:12px;padding:24px;width:420px;max-width:90%;box-shadow:0 10px 40px rgba(0,0,0,.3)">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
<h3 style="margin:0;font-size:16px;color:#333">修改资料</h3><button onclick="closeProfile()" style="background:none;border:none;font-size:20px;cursor:pointer;color:#999">&times;</button>
</div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">用户名</label><input id="profModalUser" type="text" disabled style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;background:#f9f9f9"></div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">显示名称</label><input id="profModalDN" type="text" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="输入显示名称"></div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">角色</label><input id="profModalRole" type="text" disabled style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;background:#f9f9f9"></div>
<button onclick="saveProfileModal()" style="padding:10px 24px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;margin-top:4px">保存</button>
<p id="profModalSaveMsg" style="font-size:13px;margin-top:8px;display:none"></p>
<hr style="margin:16px 0;border:none;border-top:1px solid #eee">
<h4 style="margin:0 0 12px 0;font-size:14px;color:#333">修改密码</h4>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">旧密码</label><input id="profModalOldPwd" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="输入当前密码"></div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">新密码</label><input id="profModalNewPwd" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="至少4个字符"></div>
<div class="input-group" style="margin-bottom:16px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">确认新密码</label><input id="profModalNewPwd2" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="再次输入新密码"></div>
<button onclick="submitProfilePwdModal()" style="padding:10px 24px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px">修改密码</button>
<p id="profModalPwdMsg" style="font-size:13px;margin-top:8px;display:none"></p>
</div>
</div>
'''

# Insert both before </body></html>, pwdModal first then profileModal
all_html = pwd_html + profile_html
adm = adm[:body_end] + all_html + adm[body_end:]
print(f'Both modal HTMLs inserted')

result = content[:adm_content_start] + adm + content[adm_end:]
final = result.encode('utf-8')
print(f'Final size: {len(final)}')

# Verify
t = final.decode('utf-8')
has_prof = 'id="profileModal"' in t
has_pwd = 'id="pwdModal"' in t
print(f'Has id="profileModal": {has_prof}')
print(f'Has id="pwdModal": {has_pwd}')

# Python syntax
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

# Push
payload = {
    'message': 'Add pwdModal + profileModal HTML to admin template',
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
