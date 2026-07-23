import base64, os

# Read b64 from the saved file
with open('E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/workspace/cover_small_b64.txt') as f:
    b64 = f.read()

# Split into ~2000 char chunks for browser injection
chunk_size = 2000
chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

# Write each chunk as a file
for i, c in enumerate(chunks):
    with open(f'C:/Users/lfy20/Downloads/b64_c{i}.txt', 'w') as f:
        f.write(c)

# Create the complete data URL  
data_url = 'data:image/jpeg;base64,' + b64
with open('C:/Users/lfy20/Downloads/cover_dataurl.txt', 'w') as f:
    f.write(data_url)

print(f'{len(chunks)} chunks created')
print(f'Data URL length: {len(data_url)}')
print(f'First 50 chars: {b64[:50]}')
