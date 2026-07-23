import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
lines = c.split('\n')
result = []
empty_run = 0
for line in lines:
    if not line.strip():
        empty_run += 1
        if empty_run <= 2:
            result.append('')
    else:
        empty_run = 0
        result.append(line)
c2 = '\n'.join(result)

# Also compress _ADMIN template HTML: collapse 3+ spaces to 1, trim leading spaces
m = re.search(r'_ADMIN\s*=\s*"""', c2)
start = m.end()
end_m = re.search(r'\n"""', c2[start:])
end = start + end_m.start()
html = c2[start:end]
html2 = re.sub(r'  +', ' ', html)  # 3+ spaces -> 1
lines_h = html2.split('\n')
lines_h = [l.lstrip() for l in lines_h]
html2 = '\n'.join(lines_h)

c2 = c2[:start] + html2 + c2[end:]

print(f'Original: {len(c)} bytes')
print(f'Max compress: {len(c2)} bytes')
print(f'Saved: {len(c) - len(c2)} bytes')
print(f'Available space: {86000 - len(c2)} bytes')
