# -*- coding: utf-8 -*-
c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'r', encoding='utf-8').read()

idx = c.find("@app.get('/me')")
print('GET /me at', idx)
end = c.find('\n\n\n@app', idx+10)
if end < 0:
    end = c.find('\n\n@app', idx+10)
print('End at', end)
print(c[idx:end+50])
print('---')
print('change_password count:', c.count('change_password'))
print('update_me:', c.count('update_me'))
