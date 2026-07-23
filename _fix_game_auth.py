# -*- coding: utf-8 -*-
import pathlib

path = pathlib.Path('game_auth_server.py')
content = path.read_bytes()
# Strip BOM
if content[:3] == b'\xef\xbb\xbf':
    content = content[3:]
text = content.decode('utf-8')
# Replace hardcoded paths
text = text.replace("'/data/game_auth.db'", "os.path.join(DATA_DIR, 'game_auth.db')")
text = text.replace("'/data/files.db'", "os.path.join(DATA_DIR, 'game_auth.db')")
# Write back as UTF-8 without BOM
path.write_bytes(text.encode('utf-8'))
print('OK')

import ast
ast.parse(open('game_auth_server.py', encoding='utf-8').read())
print('Syntax OK')
