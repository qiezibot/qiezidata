c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\apply_patches.py','r',encoding='utf-8').read()
idx = c.find('openPwdModal(')
print(c[idx-20:idx+100])
