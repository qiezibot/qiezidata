import requests
base = 'https://qiezidata-production.up.railway.app'
s = requests.Session()
s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'})

# 检查 script 长度
html = s.get(base + '/').text
sc_pos = html.find('<script>')
sc_end = html.find('</script>')
script_len = sc_end - sc_pos - 8
print('Script length:', script_len)

# 检查 style 标签
st_pos = html.find('<style>')
st_end = html.find('</style>')
style_len = st_end - st_pos - 7
print('Style length:', style_len)

# 判断版本
css_in_script = 'padding:0;box-sizing' in html[sc_pos:sc_end]
print('CSS in script:', css_in_script)
if not css_in_script and script_len < 2000:
    # 新版登录页脚本应该很短
    print('Version: NEW (login page)')
    # 登录后看 admin 页面
    print('Logged in, checking admin page script...')
    # 检查 script 内容
    script_content = html[sc_pos+8:sc_end]
    print('First 100 chars:', repr(script_content[:100]))
elif css_in_script:
    print('Version: OLD (CSS in script bug)')
else:
    print('Unknown version')
