import requests
base = 'https://qiezidata-production.up.railway.app'
s = requests.Session()
s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'})
html = s.get(base + '/').text
print('Version:', 'd28cb9b' in html)
print('Script len:', len(html[html.find('<script>')+8:html.find('</script>')]))
print('Has loadDashboard:', 'function loadDashboard' in html)

# 用旧的确认模式检查
print('Has old nested quote:', "if(confirm('确定删除?'))" in html)
print('Has fixed quote:', 'confirm("确定删除?")' in html)
