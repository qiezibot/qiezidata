import urllib.request, json

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/commits?per_page=3', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
for c in r:
    sha = c['sha'][:10]
    msg = c['commit']['message']
    date = c['commit']['committer']['date']
    print(f'{sha} - {msg} - {date}')
