c_clean = open('railway_file_server.py', encoding='utf-8').read()
c_mod = open('railway_file_server_modified.py', encoding='utf-8').read()

keywords = ['@app.on_event', 'async def startup', 'init_db()', 'async def home', 'if __name__', 'uvicorn.run', 'clouddata']

for kw in keywords:
    cc = c_clean.count(kw)
    cm = c_mod.count(kw)
    if cc != cm:
        print(f'DIFF: {kw}: clean={cc}, mod={cm}')
    else:
        print(f'OK: {kw}: {cc}')
