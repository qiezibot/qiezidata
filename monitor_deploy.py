import time, urllib.request, ssl
ctx = ssl.create_default_context()
f = open('C:\\temp\\deploy_log.txt', 'a')
f.write(f'{time.strftime("%H:%M:%S")} monitoring start\n')
for i in range(120):
    time.sleep(15)
    try:
        r = urllib.request.urlopen('https://qiezidata-production.up.railway.app/', timeout=10, context=ctx)
        body = r.read().decode('utf-8')
        ok = 'cpwUser' in body
        f.write(f'{time.strftime("%H:%M:%S")} {i}: {r.status} cpwUser={ok}\n')
        f.flush()
        if ok:
            print('DONE')
            break
    except:
        f.write(f'{time.strftime("%H:%M:%S")} {i}: err\n')
        f.flush()
f.close()
