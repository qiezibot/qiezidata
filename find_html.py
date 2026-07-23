with open('railway_file_server_local.py','r',encoding='utf-8') as f:
    content = f.read()

# Look for the first HTML page occurrence
idx = content.find('admin/')
print(f'admin/ at pos {idx}')
print(content[max(0,idx-50):idx+200])
print('---')

# Find last occurrence of nav items area
idx2 = content.find('a.nav-item')
print(f'a.nav-item at pos {idx2}')
print(content[max(0,idx2-50):idx2+200])
print('---')

# Find the HTML string that contains the admin pages
idx3 = content.find('tab-page')
while idx3 >= 0:
    print(f'tab-page at pos {idx3}')
    print(content[max(0,idx3-70):idx3+80])
    print('---')
    idx3 = content.find('tab-page', idx3+1)
    if content.count('tab-page', idx3+1) > 3:
        break
