import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')

# Find the clouddata table HTML (the thead)
idx = content.find('<thead><tr>')
while idx >= 0:
    end = content.find('</tr>', idx) + 5
    html = content[idx:end]
    print(f'Table header at {idx}: {html[:200]}')
    idx = content.find('<thead><tr>', end)

# Find the JS that builds clouddata rows
idx2 = content.find('var cdHtml')
if idx2 >= 0:
    end2 = content.find('}', idx2)
    print(f'\nJS row template:')
    print(content[idx2:min(end2+2, idx2+1000)])
else:
    # Look for how rows are built
    idx3 = content.find("cdHtml+=")
    if idx3 >= 0:
        end3 = content.find(');', idx3)
        print(f'\ncdHtml build:')
        print(content[idx3:end3+2][:500])
