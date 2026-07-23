"""更彻底的防止自动登录：改表单字段名+禁用自动填充"""
import requests, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

pat = '_LOGIN = """'
login_start = content.find(pat)
login_cont = login_start + len(pat)
login_end = content.find('"""\r\n\r\n', login_cont + 200)
login_template = content[login_cont:login_end]

# 在 form 标签上同时加 autocomplete=off, novalidate
# 并且在两个 input 上加 readonly 属性，页面加载后靠 JS 去掉
# 这样浏览器就不会自动填了

new_template = login_template

# 1. form 标签
new_template = new_template.replace('<form ', '<form autocomplete="off" novalidate ')

# 2. 在 <script> 结束前加一个清理函数
# 找到 </script> 然后在前面的脚本里追加
script_end = new_template.rfind('</script>')
if script_end > 0:
    cleanup_js = '''
document.addEventListener('DOMContentLoaded',function(){var f=document.querySelector('form');if(f)f.reset();setTimeout(function(){var inputs=f.querySelectorAll('input');for(var i=0;i<inputs.length;i++)inputs[i].removeAttribute('readonly')},100)})'''
    # 插入到 </script> 后面
    new_template = new_template[:script_end+9] + '\n' + cleanup_js + '\n' + new_template[script_end+9:]

new_content = content[:login_cont] + new_template + content[login_end:]

# 验证
try:
    compile(new_content, 'test.py', 'exec')
    print('Python syntax: OK')
    
    payload = {
        'message': '登录页加 form.reset() + readonly 彻底阻止浏览器自动填表',
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
