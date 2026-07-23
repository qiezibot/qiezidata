import requests, re

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

# Extract script block 0
pos = html.find('/* v3 */')
if pos > 0:
    # Find start of the script tag
    start = html.rfind('<script>', 0, pos)
    end = html.find('</script>', pos)
    js = html[start+8:end]
    
    print(f'JS block: {len(js)} bytes')
    
    # Check for syntax errors using Python's AST-like analysis
    # Look for unbalanced braces
    lines = js.split('\n')
    brace_depth = 0
    paren_depth = 0
    in_string = False
    string_char = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('//'):
            continue
        
        # Count braces, but skip strings
        # (simplified - just check gross counts)
        opens = stripped.count('{')
        closes = stripped.count('}')
        if opens != closes:
            print(f'Line {i}: brace mismatch ({opens} open, {closes} close): {stripped[:80]}')
    
    # Check for specific issues
    # 1. Missing closing brace at end
    total_open = js.count('{')
    total_close = js.count('}')
    print(f'\nTotal braces: {{ {total_open}, }} {total_close}')
    
    # 2. Check for 'function' without matching close
    func_starts = [m.start() for m in re.finditer(r'function\s+\w+\s*\(', js)]
    print(f'Function definitions: {len(func_starts)}')
    
    # 3. Print lines near each function boundary
    # Find where each function starts and ends
    for m in re.finditer(r'function\s+(\w+)\s*\(', js):
        name = m.group(1)
        fstart = m.start()
        # Find matching closing brace (simplified)
        depth = 0
        for j in range(fstart, len(js)):
            if js[j] == '{': depth += 1
            elif js[j] == '}': 
                depth -= 1
                if depth == 0:
                    func_body = js[fstart:j+1]
                    # Check if body ends properly
                    if not func_body.endswith('}'):
                        print(f'\n!!! Function {name} at {fstart}: body does not end with }}')
                        print(func_body[-100:])
                    break
        if depth > 0:
            print(f'\n!!! Function {name} at {fstart}: UNCLOSED (depth={depth})')
    
    # Check for 'openPwdModal' - is it properly terminated?
    pwd_pos = js.find('function openPwdModal(')
    if pwd_pos >= 0:
        print(f'\nopenPwdModal at {pwd_pos}')
        # Print the whole function
        depth = 0
        started = False
        for j in range(pwd_pos, pwd_pos + 2000):
            if js[j] == '{' and not started:
                depth = 1
                started = True
            elif js[j] == '{':
                depth += 1
            elif js[j] == '}':
                depth -= 1
                if depth == 0:
                    print(f'Function ends at {j} (length {j-pwd_pos})')
                    print(f'Last 200 chars: {js[j-200:j+1]}')
                    break
