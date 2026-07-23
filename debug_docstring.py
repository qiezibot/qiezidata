with open('railway_file_server_local.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx1 = content.find('"""')  # first occurrence
idx2 = content.find('"""', idx1+3)  # second occurrence
print(f'idx1 = {idx1} (line position)')
print(f'idx2 = {idx2}')

# Show what's at those positions
pre = content[:idx1]
print(f'Before idx1: {repr(pre[-30:])}')
print(f'At idx1: {repr(content[idx1:idx1+10])}')
print(f'At idx2: {repr(content[idx2:idx2+10])}')
print(f'After idx2: {repr(content[idx2+3:idx2+50])}')
print()

code = content[idx2+3:]
print(f'Code starts with: {repr(code[:80])}')
