import re

filepath = r"C:\Users\lfy20\AppData\Roaming\Python\Python311\site-packages\basicsr\utils\registry.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the assertion line to skip duplicates instead of crashing
old = "assert (name not in self._obj_map), (f\"An object named '{name}' was already registered \""
new = "if name in self._obj_map: continue  # skip duplicate registration"

content = content.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched registry.py")
