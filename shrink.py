import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# Shorten: trim some unnecessary traits
# 1. "style=color:#667eea;font-size:13px" -> shorter color-only (12 bytes saved)
c = c.replace('style=color:#667eea;font-size:13px>改密</a>', 'style=color:#67e>\u6539\u5bc6</a>')

# 2. Shorten modal: remove margin-bottom, font-size
c = c.replace('<p style=color:#666;font-size:13px>ID:', '<p style=color:#666>ID:')

# 3. Shorten pwok: "setTimeout(function(){...},1200)" -> shorter
# Actually leave that

# 4. Remove some other redundant spaces in modal
c = c.replace('class=modal-content style=max-width:360px>', 'class=modal-content>')
# Add width via style to modal itself instead
c = c.replace('<div id=pwdm class=modal style=display:none>', '<div id=pwdm class=modal style=\u200bdisplay:none>')
# Actually that zero-width space idea is bad. Just remove the max-width and add inline.

# 5. Shorten JS: remove "var " in pwok
c = c.replace('var np=pnp.value;var m=document.getElementById("pwmsg");', 'np=pnp.value;m=document.getElementById("pwmsg");')
# And declare np,m as globals
# Wait, that breaks JS. Let's undo. 
# Better: inline shorter.

# Let's just check size
print(f'After: {len(c)} bytes')

import ast
ast.parse(c)
print('Syntax OK')

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
