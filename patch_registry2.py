filepath = r"C:\Users\lfy20\AppData\Roaming\Python\Python311\site-packages\basicsr\utils\registry.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_method = '''    def _do_register(self, name, obj, suffix=None):
        if isinstance(suffix, str):
            name = name + '_' + suffix

        if name in self._obj_map: continue  # skip duplicate registration
                                             f"in '{self._name}' registry!")
        self._obj_map[name] = obj'''

new_method = '''    def _do_register(self, name, obj, suffix=None):
        if isinstance(suffix, str):
            name = name + '_' + suffix

        # skip duplicate registrations (compatibility between gfpgan/facexlib/basicsr)
        if name in self._obj_map:
            return
        self._obj_map[name] = obj'''

content = content.replace(old_method, new_method)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched _do_register cleanly")
