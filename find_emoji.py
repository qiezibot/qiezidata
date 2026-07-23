with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact two-char sequences
import re

# Build replacement map: find all unique broken emoji sequences
blobs = set()
for m in re.finditer(r'[\u9000-\uFFFF]{2}', content):
    blobs.add(m.group(0))

print("Broken emoji sequences found:")
for b in sorted(blobs):
    print(f'  {repr(b)} (U+{ord(b[0]):04X} U+{ord(b[1]):04X})')

# Replacement mapping: broken_emoji -> text
reps = {
    '\u9983\u5d0b': '\U0001f346',     # 🍆
    '\u9983\u9233': '',  # should be the generic "icon" used for 📊📁📤👤👥
}

# Need to identify each context...
# From the check above:
# Pos 17468: h1>🍆 Eggplan  -> eggplant emoji
# Pos 23013: an>👤 <!--U-->  -> user icon  
# Pos 23180: )">📊 Dashboard -> chart/dashboard
# Pos 23255: )">📁 Files     -> folder
# Pos 23327: )">📤 Upload    -> upload
# Pos 23399: )">👥 Users     -> users

# But the SECOND char for 5/6 of them is the same U+9233.
# Only the eggplant has U+5D0B. Let's check:
for b in sorted(blobs):
    first, second = ord(b[0]), ord(b[1])
    print(f'  {repr(b)} -> U+{first:04X} U+{second:04X}')
