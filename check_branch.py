import urllib.request, json

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/branches/main', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
print(f'Branch main SHA: {r["commit"]["sha"]}')
print(f'Commit: {r["commit"]["commit"]["message"]}')
