import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 找 _ADMIN
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
# 找到真正的结束：下一个单独成行的 """
end_match = re.search(r'\n"""', c[start:])
end = start + end_match.start()

print(f'_ADMIN: {start}-{end}')

# 检查结束符
print(f'End marker: {repr(c[end:end+10])}')

html = c[start:end]

# 1. 侧边栏加个人资料
html = html.replace(
    'data-page="page-users"',
    'data-page="page-profile" onclick="openProfile()"><span class="nav-icon">\U0001f464</span><span class="nav-text">个人资料</span></li><li class="nav-item" data-page="page-users"'
)
# 2. 用户表格加密码列
html = html.replace('</thead>', '<th style="width:100px">密码</th></thead>')
# 3. 每行加密码按钮
html = html.replace(
    'onclick="deleteUser(',
    '<button class="btn-small btn-pwd" onclick="adminChangePwd(${user.id})" style="margin-right:4px">修改密码</button> <button onclick="deleteUser('
)
# 4. 用户名可点击
html = html.replace(
    '"><span class="user-area">\U0001f464; <!--U--></span>',
    '"><span class="user-area"><a onclick="openProfile()" style="cursor:pointer;color:inherit;text-decoration:none">\U0001f464; <!--U--></a></span>'
)
# 5. body前加模态框 + JS
modal_js = "\n<div id=\"profileModal\" class=\"modal\" style=\"display:none\"><div class=\"modal-content\" style=\"max-width:420px\"><span class=\"modal-close\" onclick=\"closeProfile()\">&times;</span><h3>\u4e2a\u4eba\u8d44\u6599</h3><div class=\"form-group\"><label>\u7528\u6237\u540d</label><input id=\"profModalUser\" type=\"text\" readonly style=\"background:#f5f5f5;cursor:not-allowed\"></div><div class=\"form-group\"><label>\u663e\u793a\u540d\u79f0</label><input id=\"profModalDN\" type=\"text\" placeholder=\"\u8f93\u5165\u663e\u793a\u540d\u79f0\"></div><div class=\"form-group\"><label>\u89d2\u8272</label><input id=\"profModalRole\" type=\"text\" readonly style=\"background:#f5f5f5;cursor:not-allowed\"></div><button class=\"btn\" onclick=\"saveProfileModal()\">\u4fdd\u5b58</button><div id=\"profModalSaveMsg\" class=\"msg\" style=\"display:none\"></div><hr style=\"margin:16px 0\"><h4>\u4fee\u6539\u5bc6\u7801</h4><div class=\"form-group\"><label>\u65e7\u5bc6\u7801</label><input id=\"profModalOldPwd\" type=\"password\" placeholder=\"\u8f93\u5165\u65e7\u5bc6\u7801\"></div><div class=\"form-group\"><label>\u65b0\u5bc6\u7801</label><input id=\"profModalNewPwd\" type=\"password\" placeholder=\"\u81f3\u5c114\u4e2a\u5b57\u7b26\"></div><div class=\"form-group\"><label>\u786e\u8ba4\u65b0\u5bc6\u7801</label><input id=\"profModalNewPwd2\" type=\"password\" placeholder=\"\u518d\u6b21\u8f93\u5165\"></div><button class=\"btn\" onclick=\"submitProfilePwdModal()\">\u4fee\u6539\u5bc6\u7801</button><div id=\"profModalPwdMsg\" class=\"msg\" style=\"display:none\"></div></div></div>\n<div id=\"changePasswordModal\" class=\"modal\" style=\"display:none\"><div class=\"modal-content\" style=\"max-width:380px\"><span class=\"modal-close\" onclick=\"document.getElementById('changePasswordModal').style.display='none'\">&times;</span><h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3><p id=\"cpUserInfo\" style=\"color:#666;margin-bottom:12px;font-size:13px\"></p><div class=\"form-group\"><label>\u65b0\u5bc6\u7801</label><input id=\"cpNewPwd\" type=\"password\" placeholder=\"\u81f3\u5c114\u4e2a\u5b57\u7b26\"></div><button class=\"btn\" onclick=\"submitAdminChangePwd()\">\u786e\u8ba4\u4fee\u6539</button><div id=\"cpMsg\" class=\"msg\" style=\"display:none\"></div></div></div>\n"
html = html.replace('</body>', modal_js + '</body>')

# 只压缩 _ADMIN 内部的多余空行（保留代码结构）
# 不要碰结束标记附近
html = re.sub(r'\n\s*\n\s*\n\s*\n', '\n\n\n', html)  # 4+空行缩成3

c = c[:start] + html + c[end:]

# Python 代码区域压缩到最多3个连续空行
lines = c.split('\n')
result = []
empty_count = 0
for line in lines:
    if not line.strip():
        empty_count += 1
        if empty_count <= 3:
            result.append('')
    else:
        empty_count = 0
        result.append(line)

c = '\n'.join(result)

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
orig = 85619
print(f'Before: {orig} bytes')
print(f'After: {len(c)} bytes')
print(f'Saved: {orig - len(c)} bytes')
print(f'Total lines: {len(c.splitlines())}')
