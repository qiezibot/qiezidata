filepath = r"C:\Users\lfy20\AppData\Roaming\Python\Python311\site-packages\basicsr\utils\misc.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add compatibility functions at the end
addon = '''

# --- compatibility shims for GFPGAN/CodeFormer/facexlib ---
def gpu_is_available():
    import torch
    return torch.cuda.is_available()

def get_device():
    import torch
    return 'cuda' if torch.cuda.is_available() else 'cpu'
'''

if 'def gpu_is_available' not in content:
    content += addon

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added gpu_is_available/get_device to basicsr misc.py")
