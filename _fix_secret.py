import pathlib

path = pathlib.Path('railway_file_server.py')
text = path.read_text(encoding='utf-8')

# Fix SECRET_KEY
text = text.replace(
    "SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))",
    "SECRET_KEY = os.environ.get('SECRET_KEY', 'c3adc9837be6a1ad025450a8568e77bb19d3db42221875e2afa7d98c4706af2a')"
)

path.write_bytes(text.encode('utf-8'))
print('Fixed SECRET_KEY')

import ast
ast.parse(text)
print('Syntax OK')
