import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', 'rb') as f:
    content = f.read()

target = '确定要删除用户'.encode('utf-8')
idx = content.find(target)
print(f'Found at {idx}')
print(repr(content[idx:idx+100]))
print('Bytes around exclamation:', [hex(b) for b in content[idx+15:idx+25]])
