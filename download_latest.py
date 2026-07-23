import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')
sha = r['sha']
print(f'SHA: {sha}, Size: {len(content)}B')

# Save locally so we can upload to Railway
with open('D:\\u-claw-backup-20260703\\portable\\data\\.openclaw\\workspace\\railway_file_server_latest.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Saved to workspace/railway_file_server_latest.py')
