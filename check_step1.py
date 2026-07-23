with open('step1_nav.py', 'r', encoding='utf-8') as f:
    content = f.read()

emoji_count = content.count('\U0001f4d6')
print(f'Step1 emoji count: {emoji_count}')
idx = content.find('\U0001f4d6')
if idx >= 0:
    start = max(0, idx-10)
    print(repr(content[start:idx+20]))

# Check if emoji is inside docstring or inside code section
idx1 = content.find('"""')
idx2 = content.find('"""', idx1+3) + 3
docstring_region = content[:idx2]
code_region = content[idx2:]

emoji = '\U0001f4d6'
print(f'Emoji in docstring: {docstring_region.count(emoji)}')
print(f'Emoji in code: {code_region.count(emoji)}')

# Find the nav line
nav_idx = content.find('APIDOCS')
if nav_idx < 0:
    nav_idx = content.find('apidocs')
print(f'\nNav at pos {nav_idx}')
print(repr(content[nav_idx-3:nav_idx+50]))
