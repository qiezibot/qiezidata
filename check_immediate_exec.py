import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

pos = html.find('/* v3 */')
start = html.rfind('<script>', 0, pos)
end = html.find('</script>', pos)
js = html[start+8:end]

# Print all lines that are NOT inside function definitions
lines = js.split('\n')
in_function = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if not stripped:
        continue
    
    # Track function depth
    if 'function ' in stripped and stripped.endswith('{'):
        in_function += 1
        # Also need to check if the brace is on same line
        opens = stripped.count('{')
        closes = stripped.count('}')
        in_function += opens - closes
        continue
    
    opens = stripped.count('{')
    closes = stripped.count('}')
    in_function += opens - closes
    
    if in_function == 0 and not stripped.startswith('//') and not stripped.startswith('/*'):
        print(f'Line {i} (depth={in_function}): {stripped[:120]}')

print(f'\n--- Total immediate execution lines: ---')

# Also show lines before first 'function' keyword
first_func = js.find('function ')
before = js[:first_func]
print(f'\nCode BEFORE first function ({first_func} chars):')
print(before[:2000])
