with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

def find_template(name):
    pos = text.find(f'{name} = """')
    if pos < 0:
        print(f'{name}: NOT FOUND')
        return
    end_pos = text.find('"""', pos + len(name) + 5)
    if end_pos < 0:
        print(f'{name}: NO CLOSING """')
    else:
        seg = text[pos:end_pos+3]
        print(f'{name}: pos={pos} -> {end_pos}, length={len(seg)}')
        print(f'  Ends with: ...{seg[-50:]}')
    print()

find_template('_LOGIN')
find_template('_ADMIN')
find_template('_USER')

# Also check total """ distribution
print("\nAll triple-quote positions:")
idx = 0
count = 0
while True:
    idx = text.find('"""', idx)
    if idx < 0:
        break
    count += 1
    context = text[max(0,idx-20):idx+25]
    print(f'  #{count} at char {idx}: ...{repr(context)}...')
    idx += 1
