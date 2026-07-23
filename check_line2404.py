import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
# Check lines 2400-2420
lines = c.split('\n')
print(f'Total lines: {len(lines)}')
for i in range(2399, min(2421, len(lines))):
    print(f'{i}: {repr(lines[i][:100])}')
