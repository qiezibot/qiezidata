import re

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end = c.find('\n"""', start)
html = c[start:end]
print(f'_ADMIN total: {len(html)} chars')

scripts = re.findall(r'<script[^>]*>.*?</script>', html, re.DOTALL)
total_js = sum(len(s) for s in scripts)
print(f'Total <script>: {len(scripts)} blocks, {total_js} chars')

styles = re.findall(r'<style[^>]*>.*?</style>', html, re.DOTALL)
total_css = sum(len(s) for s in styles)
print(f'Total <style>: {len(styles)} blocks, {total_css} chars')

# 看看有没有多出来的空格可以压缩
space_lines = 0
for line in html.split('\n'):
    stripped = line.strip()
    if not stripped or (len(stripped) < 5 and not stripped.startswith('<') and not stripped.startswith('var') and not stripped.startswith('//')):
        space_lines += 1
print(f'Empty/minimal lines: {space_lines}')
