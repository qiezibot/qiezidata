"""把 SECRET_KEY 写死在代码里，不用环境变量或文件"""
import requests, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

# 固定密钥（永不变）
FIXED_KEY = 'c3adc9837be6a1ad025450a8568e77bb19d3db42221875e2afa7d98c4706af2a'

# 替换整个 _get_secret 函数
old_text = '''# 持久化 SECRET_KEY，避免容器重启后登录失效
_SECRET_FILE = 'secret_key.txt'
def _get_secret():
    try:
        import os
        sk = os.environ.get('SECRET_KEY')
        if sk: return sk
        if os.path.exists(_SECRET_FILE):
            with open(_SECRET_FILE) as f: return f.read().strip()
    except: pass
    sk = secrets.token_hex(32)
    try:
        with open(_SECRET_FILE, 'w') as f: f.write(sk)
    except: pass
    return sk
SECRET_KEY = _get_secret()'''

new_text = f'''# 固定 SECRET_KEY，避免容器重启后需重新登录
SECRET_KEY = os.environ.get('SECRET_KEY', '{FIXED_KEY}')'''

if old_text in content:
    new_content = content.replace(old_text, new_text)
elif 'SECRET_KEY = _get_secret()' in content:
    new_content = content.replace('SECRET_KEY = _get_secret()', f'SECRET_KEY = os.environ.get(\'SECRET_KEY\', \'{FIXED_KEY}\')')
else:
    # 直接找原始行
    import re
    new_content = re.sub(
        r"SECRET_KEY\s*=\s*os\.environ\.get\([^,]+,\s*secrets\.token_hex\(32\)\)",
        f"SECRET_KEY = os.environ.get('SECRET_KEY', '{FIXED_KEY}')",
        content
    )
    if content == new_content:
        # 找备份_KEY 函数
        new_content = content.replace(
            "SECRET_KEY = _get_secret()\n\n\n",
            f"SECRET_KEY = '{FIXED_KEY}'\n\n\n"
        )

has_get = '_get_secret()' in content
print(f'old in content: {old_text in content}')
print(f'_get_secret in content: {has_get}')

# 验证
try:
    compile(new_content, 'test.py', 'exec')
    print('Python syntax: OK')
    
    payload = {
        'message': '固定 SECRET_KEY 为永久值，彻底解决重启登录失效问题',
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
    print(f'SYNTAX ERROR: {e}')
