import requests, base64, json
GH_TOKEN = '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'
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py?ref=d31360fdf3bf077d7db106ae2e378d6016761e2e', 
    headers={'Authorization': 'Bearer ' + GH_TOKEN, 'Accept': 'application/vnd.github.v3+json'})
d = r.json()
content = base64.b64decode(d['content']).decode('utf-8')
print('File size:', len(content))
print('Has initCloudData:', 'initCloudData' in content)
print('Has exportCD pid:', 'cdpSelect' in content)
print('Last 50 chars:', repr(content[-50:]))
