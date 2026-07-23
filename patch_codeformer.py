filepath = r"C:\Users\lfy20\AppData\Roaming\Python\Python311\site-packages\codeformer\lib.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the import
old_import = "from basicsr.utils.misc import gpu_is_available, get_device"
new_import = "# patched: gpu_is_available and get_device not in basicsr 1.4.2\ndef gpu_is_available():\n    import torch\n    return torch.cuda.is_available()\ndef get_device():\n    import torch\n    return 'cuda' if torch.cuda.is_available() else 'cpu'"

content = content.replace(old_import, new_import)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched codeformer lib.py")
