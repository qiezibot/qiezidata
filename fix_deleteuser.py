import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
print(f'Current size: {len(c)} bytes')

# 缩短 pwok 函数（更短的变量名）
# 当前 pwok 很冗长，可以缩
# 并且 deleteUser 中的 render 还没改

# 1. Fix deleteUser render also
pos = c.find('async function deleteUser')
if pos >= 0:
    # find the h+= render in deleteUser
    hpos = c.find(';h+=', pos)
    if hpos < 0:
        hpos = c.find("h+=", pos)
    if hpos >= 0:
        endpos = c.find("}catch", hpos)
        render = c[hpos:endpos]
        print(f'deleteUser render:')
        print(render[:300])
        print('...')
        print(render[-200:])
        # Check if it already has the pwdm button
        if 'pwdm' not in render:
            # Add button before the final </td></tr>
            old_end = ")+'</td></tr>';"
            if old_end in render:
                new_end = ")+'</td><td><a onclick=\"pwdm('+u.id+')\" style=margin-right:4px>\u6539\u5bc6</a></td></tr>';"
                c = c[:hpos] + render.replace(old_end, new_end) + c[endpos:]
                print('Fixed deleteUser render')
