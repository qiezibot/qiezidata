with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ====== Identify ALL BMP "emoji-like" characters ======
import collections

# Collect all multi-char sequences that look like smashed emoji
# They appear as [char1][char2] space usually, like '\u9983\u5d0b '
# These are all in the range > U+9000
high_chars = [c for c in content if ord(c) > 0x9000]
freq = collections.Counter(high_chars)
print("High-range characters frequency:")
for c, n in freq.most_common(20):
    print(f"  U+{ord(c):04X} ({c}): {n} times")

# Find all adjacent pairs of high-range chars
pairs = collections.Counter()
prev = ''
for c in content:
    if ord(c) > 0x9000:
        if prev:
            pairs[prev + c] += 1
        prev = c
    else:
        prev = ''
print("\nAdjacent pairs:")
for p, n in pairs.most_common(20):
    print(f"  {repr(p)} (U+{ord(p[0]):04X}U+{ord(p[1]):04X}): {n}")
