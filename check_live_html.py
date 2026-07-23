import requests as r
base = 'https://qiezidata-production.up.railway.app'
s = r.Session()
s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'})

# 看页面源码里 script 和 style 是否分开
html = s.get(base + '/').text
sc = '<script>'
st = '<style>'
sc_pos = html.find(sc)
st_pos = html.find(st)
sc_end = html.find('</script>') + 9
st_end = html.find('</style>') + 7

print('script:', sc_pos, 'to', sc_end)
print('style:', st_pos, 'to', st_end)
print('CSS in script:', 'padding:0;box-sizing' in html[sc_pos:sc_end])
print('CSS in style:', 'padding:0;box-sizing' in html[st_pos:st_end])
print('style before script:', st_pos < sc_pos)

# 确认线上版本
ver = '49c4146a' in html
print('New version deployed:', ver)
