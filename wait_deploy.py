import time, urllib.request, ssl
ctx = ssl.create_default_context()
print('start:', time.strftime('%H:%M:%S'))
for i in range(60):
    try:
        r = urllib.request.urlopen('https://qiezidata-production.up.railway.app/', timeout=10, context=ctx)
        body = r.read().decode('utf-8')
        if 'cpwUser' in body:
            print(f'DEPLOYED OK at {time.strftime("%H:%M:%S")}')
            break
        else:
            print(f'#{i} old')
    except Exception as e:
        s = str(e)
        print(f'#{i} {s[:20]}')
    time.sleep(10)
