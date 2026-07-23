with open('railway_file_server_local.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where the Python code starts (after the docstring)
idx1 = content.find('"""')
idx2 = content.find('"""', idx1+3) + 3
code = content[idx2:]
print(f'Docstring: {idx1} to {idx2}')
print(f'Python code: {len(code)} bytes')

# Check for HTML injection into Python code
# Look for HTML tags in the code part (should only be in strings)
html_in_code = code.count('<div') + code.count('<a ') + code.count('<button') + code.count('<table')
print(f'HTML tags in code portion: {html_in_code}')

# Check for f-string issues with {token}
if '{token}' in code:
    # Find in what context
    idx = code.find('{token}')
    print(f'\nFound {{token}} at pos {idx} in code')
    print(repr(code[idx-100:idx+100]))

# Check double curly braces (for literal {})
print(f'\nSingle {{ before token: {code.count("{token}")}')
print(f'Double {{ before token: {code.count("{{token")}')

# Look for where emoji appears in the file
emoji_count = content.count('\U0001f4d6')
print(f'\nEmoji count: {emoji_count}')
idx = content.find('\U0001f4d6')
if idx >= 0:
    print(f'First emoji at pos {idx}')
    print(repr(content[idx-5:idx+50]))
