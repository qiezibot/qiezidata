with open('railway_file_server_local.py','r',encoding='utf-8') as f:
    content = f.read()

# Find where the admin HTML string starts
# Look for <div class="sidebar"
idx = content.find('<div class="sidebar"')
print(f'<div class="sidebar" at pos {idx}')

# Show context - what variable is this assigned to
line_start = content.rfind('\n', 0, idx) + 1
print(f'Context: {repr(content[line_start-20:line_start+30])}')

# Find the start of the string containing this HTML
# Look backwards for = or + or (
start = idx - 500
pre = content[start:idx]
print(f'\nBefore sidebar (500 chars):')
print(pre)
print('=== SIDEBAR ===')

# Find nav-item in sidebar
nav_idx = content.find('class="nav-item"', idx)
print(f'\nNav items start at: {nav_idx}')
while nav_idx >= 0 and nav_idx < idx + 5000:
    line_end = content.find('\n', nav_idx)
    print(f'  {content[nav_idx:line_end]}')
    nav_idx = content.find('class="nav-item"', line_end)
