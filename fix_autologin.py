"""在登录页面加 autocomplete=off 和阻止浏览器自动提交"""
import requests, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

# 在登录页面的 form 标签上加 autocomplete="off" 和 autofill 阻止
# 找 login 页面的 HTML 模板里的 <form
# 登录页是 _LOGIN 模板

pat = '_LOGIN = """'
login_start = content.find(pat)
login_cont = login_start + len(pat)

# 找到 login 模板结束
login_end = content.find('"""\r\n\r\n', login_cont + 200)
login_template = content[login_cont:login_end]
print(f'Login template: {len(login_template)} chars')

# 在 form 标签上加 autocomplete="off"
if 'autocomplete="off"' not in login_template:
    new_template = login_template.replace('<form ', '<form autocomplete="off" ')
    new_content = content[:login_cont] + new_template + content[login_end:]
    
    # 验证 Python 语法
    try:
        compile(new_content, 'test.py', 'exec')
        print('Python syntax: OK')
        
        payload = {
            'message': '登录页加 autocomplete=off 阻止浏览器自动填表提交',
            'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            'sha': sha,
            'branch': 'main'
        }
        r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
        print(f'Push: {r2.status_code}')
        if r2.status_code in (200, 201):
            print(f'Commit: {r2.json()["commit"]["sha"][:12]}')
        else:
            print(f'Error: {r2.text[:300]}')
    except SyntaxError as e:
        print(f'Error: {e}')
else:
    print('已有 autocomplete="off"')
    # 找找有没有别的办法
    # 在 <body> 上加 onload 重置表单
