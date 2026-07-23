# -*- coding: utf-8 -*-
c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'r', encoding='utf-8').read()

print('change_password:', c.count('change_password'))
print('update_me:', c.count('update_me'))

# Find GET /me
idx = c.find("@app.get('/me')")
if idx >= 0:
    print(f'\nGET /me at {idx}')
    # Show next 1500 chars
    segment = c[idx:idx+1500]
    # Find what comes after
    end = segment.find('\n@app')
    print('Segment until next @app:')
    print(segment[:end if end > 0 else len(segment)])
