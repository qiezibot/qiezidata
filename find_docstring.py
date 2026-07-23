import sys

with open('railway_file_server_local.py', 'r', encoding='utf-8') as f:
    original = f.read()

# Find all triple-quotes
lines = original.split('\n')
for i, line in enumerate(lines):
    if line.strip().startswith('"""'):
        print(f'Line {i+1}: {line[:80]}')
