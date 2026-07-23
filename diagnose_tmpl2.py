with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('_ADMIN = ')
print('_ADMIN at:', idx)
print(repr(content[idx:idx+20]))

# 跳过 _ADMIN = 后找第一个不是空格的字符
pos = idx + 8
while pos < len(content) and content[pos] in ' \t':
    pos += 1
print('First non-space:', repr(content[pos]), 'at', pos)

if content[pos] == '"':
    # 三双引号
    if content[pos:pos+3] == '"""':
        tmpl_start = pos + 3
    else:
        tmpl_start = pos + 1
else:
    print('Not double quote')
    exit()

tmpl_end = content.find('"""', tmpl_start)
print('Template:', tmpl_start, 'to', tmpl_end)
print('Length:', tmpl_end - tmpl_start)

tmpl = content[tmpl_start:tmpl_end]

sc_count = tmpl.count('<script>')
se_count = tmpl.count('</script>')
st_count = tmpl.count('<style>')
print('script open:', sc_count, 'close:', se_count, 'style:', st_count)

sc_positions = []
p = 0
while True:
    p = tmpl.find('<script>', p)
    if p < 0:
        break
    sc_positions.append(p)
    p += 1

print('Script at:', sc_positions)

for sp in sc_positions:
    ep = tmpl.find('</script>', sp)
    if ep < 0:
        ep = len(tmpl)
    inner = tmpl[sp+8:ep]
    has_css = 'padding:0;box-sizing' in inner
    print(f'  [{sp}] ends at {ep}, has CSS: {has_css}, len: {len(inner)}')
    if has_css:
        css_idx = inner.find('padding:0;box-sizing')
        print('  CSS at offset:', css_idx)
        print('  Before CSS:', repr(inner[css_idx-30:css_idx]))
        print('  All script ends:', ep)
        print('  After script:', repr(tmpl[ep:ep+50]))
