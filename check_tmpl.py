content = open('railway_file_server.py', 'r', encoding='utf-8').read()
idx = content.find('_ADMIN = ')
print('_ADMIN at:', idx)
print('After =:', repr(content[idx:idx+15]))

after = content[idx+8:]
quote = after[0]
print('First char:', repr(quote))

rest = after[4:]
end_pos = rest.find('"""')
if end_pos >= 0:
    print('Template end at relative:', end_pos)
    print('Absolute:', idx+8+4+end_pos)
    print('Total file length:', len(content))
    remaining = content[idx+8+4+end_pos+3:]
    print('After template:', repr(remaining[:100]))
else:
    print('No closing triple quote!')
    print('Last 500 chars of file:')
    print(content[-500:])
