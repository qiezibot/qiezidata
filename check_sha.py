import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}
sha = '36ab4f69be'  # latest

req = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/blobs/{sha}', headers=headers)
try:
    r = json.loads(urllib.request.urlopen(req).read())
    print(f'Blob: {r.get("sha","?")} size={r.get("size","?")}')
except:
    # Get the full tree at this commit
    req2 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/commits/{sha}', headers=headers)
    r2 = json.loads(urllib.request.urlopen(req2).read())
    print(f'Commit tree: {r2.get("sha","?")}')
