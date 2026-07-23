with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Check all templates
for name in ['_LOGIN', '_ADMIN', '_USER']:
    start = text.find(f'{name} = """')
    end = text.find('"""', start + 10)
    if start < 0:
        print(f'{name}: NOT FOUND')
        continue
    tpl = text[start:end+3]
    print(f'{name}: {len(tpl)} bytes')
    if '<!--U-->' in tpl:
        print(f'  Has <!--U-->')
    else:
        print(f'  MISSING <!--U-->')
    # Check if template contains expected content
    if 'Eggplant Data' in tpl:
        print(f'  Has Eggplant Data')
    print()
