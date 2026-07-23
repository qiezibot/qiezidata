import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = r'C:\u-claw\portable\data\.openclaw\workspace\delta_apk_analysis'
for f in sorted(os.listdir(d)):
    path = os.path.join(d, f)
    if not (os.path.isfile(path) and f.endswith('.md')):
        continue
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    keywords = ['检测', 'detect', '反作弊', 'anti-cheat', 'ace', 'root', 'frida', 'xposed', '注入', 'hook', 'integrity', 'tamper']
    if not any(kw in content.lower() for kw in keywords):
        continue
    print(f'=== {f} ({len(content)} chars) ===')
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in keywords):
            # strip emoji and non-gbk chars
            clean = ''.join(c if ord(c) < 0x10000 else '?' for c in line)
            print(f'  L{i}: {clean[:200]}')
    print()
