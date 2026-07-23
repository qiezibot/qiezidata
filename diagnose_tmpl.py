with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('_ADMIN = ')
tmpl_start = idx + 8  # after '= '
# 确定是三引号
quote = content[tmpl_start]
print('Quote char:', repr(quote), 'at pos', tmpl_start)
if quote == '"':
    tmpl_start += 3
    close = '"""'
elif quote == "'":
    tmpl_start += 3
    close = "'''"
else:
    print('Not a string!')
    exit()

# 找到模板结束
tmpl_end = content.find(close, tmpl_start)
print('Template:', tmpl_start, 'to', tmpl_end)

tmpl = content[tmpl_start:tmpl_end]

# 统计标签
sc_count = tmpl.count('<script>')
se_count = tmpl.count('</script>')
st_count = tmpl.count('<style>')
print('script open:', sc_count, 'close:', se_count, 'style:', st_count)

# 查找是否有一个 script 标签内包含 CSS
sc_positions = []
pos = 0
while True:
    p = tmpl.find('<script>', pos)
    if p < 0:
        break
    sc_positions.append(p)
    pos = p + 1

print('Script positions:', sc_positions)

for sp in sc_positions:
    ep = tmpl.find('</script>', sp)
    if ep < 0:
        ep = len(tmpl)
    inner = tmpl[sp+8:ep]
    has_css = 'padding:0;box-sizing' in inner
    if has_css:
        print('CSS in script at', sp, 'script ends at', ep)
        # 找开头
        print('Before:', repr(tmpl[sp-20:sp]))
        print('After:', repr(tmpl[ep:ep+30]))
