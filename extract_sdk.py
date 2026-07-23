import tarfile, os

tgz = r'E:\openclaw压缩包及启动教程\u-claw\portable\data\.openclaw\workspace\openclaw-2026.5.12.tgz'
outdir = r'E:\openclaw压缩包及启动教程\u-claw\portable\data\.openclaw\workspace\tmp_oc'

os.makedirs(outdir, exist_ok=True)

with tarfile.open(tgz, 'r:gz') as tar:
    for member in tar:
        if 'dist/plugin-sdk/index.js' in member.name:
            tar.extract(member, outdir)
            print(f'Extracted: {member.name}')

# Find the file
import glob
files = glob.glob(os.path.join(outdir, '**', 'index.js'), recursive=True)
for f in files:
    if 'plugin-sdk' in f:
        print(f'Found: {f}')
        with open(f, 'r', encoding='utf8') as fp:
            content = fp.read()
        print(f'Length: {len(content)} bytes')
        print(f'First 300 chars:\n{content[:300]}')
