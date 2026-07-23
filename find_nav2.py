with open('railway_file_server_local.py','r',encoding='utf-8') as f:
    content = f.read()

# Search for the actual nav patterns
for pat in ['<span class="icon">', '<span class="nav-text">', 'class="nav-item"']:
    idx = content.find(pat)
    print(f'{pat}: at pos {idx}')
    if idx >= 0:
        print(f'  Context: {repr(content[idx-30:idx+80])}')

# Show actual nav items
idx = content.find('class="nav-item"')
while idx >= 0:
    line_end = content.find('\n', idx)
    print(f'\n  {content[idx:line_end]}')
    idx = content.find('class="nav-item"', line_end)
    if idx > 37000 + 2000:  # only in sidebar area
        break

# Now see what string <span class="nav-text"> matches
idx2 = content.find('<span class="nav-text">')
if idx2 >= 0:
    print(f'\nMATCH FOUND at {idx2}')
    print(content[idx2-50:idx2+200])
else:
    print('\nNo <span class="nav-text"> in file')

# Also check </a> patterns
idx3 = content.find('</a>', 37000)
count = 0
while idx3 >= 0 and count < 5:
    print(f'</a> at {idx3}: {repr(content[max(0,idx3-20):idx3+20])}')
    idx3 = content.find('</a>', idx3+1)
    count += 1
