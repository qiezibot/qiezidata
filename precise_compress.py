import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# 压缩空行
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
c = '\n'.join(result)

print(f'After compression: {len(c)}')

# Find _ADMIN exactly: _ADMIN = """\<!DOCTYPE... ...</html>"""
# The opening is _ADMIN = """\  (or _ADMIN = """\)
m = re.search(r'_ADMIN\s*=\s*"""', c)
open_start = m.end()  # position after """
# Actually _ADMIN = """\<!, the content starts after the backslash
content_start = open_start + 1  # skip the \

# Find closing: html>"""
close_marker = 'html>"""'
close_pos = c.find(close_marker, content_start)
if close_pos >= 0:
    content_end = close_pos  # before html>"""
    html = c[content_start:content_end]
    print(f'ADMIN content: {content_start}-{content_end}, {len(html)} chars')
    print(f'Ends with: {repr(html[-50:])}')
    
    # Trim leading spaces (safe for HTML)
    lines_h = html.split('\n')
    lines_h = [l.lstrip() for l in lines_h]
    html2 = '\n'.join(lines_h)
    
    c2 = c[:content_start] + html2 + c[content_end:]
    
    import ast
    try:
        ast.parse(c2)
        print('Syntax OK after trim!')
        
        # Now compress spaces
        html3 = re.sub(r'  +', ' ', html2)
        c3 = c[:content_start] + html3 + c[content_end:]
        
        try:
            ast.parse(c3)
            print('Syntax OK after space compress!')
            print(f'Final size: {len(c3)}')
        except SyntaxError as e:
            print(f'Space compress broke: line {e.lineno}: {e.msg}')
    except SyntaxError as e:
        print(f'Trim broke: line {e.lineno}: {e.msg}')
else:
    print('html>""" not found')
    # Try finding first """ after content_start
    pos = c.find('"""', content_start)
    print(f'First """ after content: {repr(c[pos-20:pos+20])}')
