import shutil, os

# Read the fresh sdk index from the tgz
src = r'E:\openclaw压缩包及启动教程\u-claw\portable\data\.openclaw\workspace\tmp_oc\package\dist\plugin-sdk\index.js'
dst = r'E:\openclaw压缩包及启动教程\u-claw\portable\app\core\node_modules\openclaw\dist\plugin-sdk\index.js'

with open(src, 'r', encoding='utf8') as f:
    content = f.read()

# Now add the shim exports for qqbot compatibility
shim = """// Shim exports for qqbot plugin compatibility (added by qqbot plugin)
const applyAccountNameToChannelSection = (section, name) => {};
const deleteAccountFromConfigSection = (section, accountId) => {};
const setAccountEnabledInConfigSection = (section, accountId, enabled) => {};
export { applyAccountNameToChannelSection, deleteAccountFromConfigSection, setAccountEnabledInConfigSection };

"""

content = shim + content

with open(dst, 'w', encoding='utf8') as f:
    f.write(content)

print(f'Restored plugin-sdk/index.js ({len(content)} bytes)')
print(f'Added shim exports: applyAccountNameToChannelSection, deleteAccountFromConfigSection, setAccountEnabledInConfigSection')
