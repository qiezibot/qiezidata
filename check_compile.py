import sys, ast

with open('step1_nav.py', 'r', encoding='utf-8') as f:
    c = f.read()

idx1 = c.find('"""')
idx2 = c.find('"""', idx1+3) + 3
code = c[idx2:]

try:
    tree = ast.parse(code)
    print('Step1 AST: OK')
except SyntaxError as e:
    print(f'Step1 ERROR line {e.lineno}: {e.msg}')

# Also try compile (what FastAPI/Uvicorn does)
try:
    compile(code, 'step1', 'exec')
    print('Step1 compile: OK')
except SyntaxError as e:
    print(f'Step1 compile ERROR line {e.lineno}: {e.msg}')
