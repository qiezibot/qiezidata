import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

# Get latest railway_file_server.py
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"File SHA: {sha}")

# Add a railway.json that rebuilds using the latest GitHub HEAD instead of cached
# Actually better: add a .railway/start_command that pulls latest before running

# Simplest: Add Deploy section to railway.json in repo
# Railway checks for railway.json in root

railway_json = json.dumps({
    "$schema": "https://railway.app/railway.schema.json",
    "build": {
        "builder": "nixpacks",
        "buildCommand": "pip install -r railway_requirements.txt && python railway_file_server.py",
        "watchPatterns": []
    },
    "deploy": {
        "startCommand": "pip install -r railway_requirements.txt && python railway_file_server.py",
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10
    }
}, ensure_ascii=False, indent=2)

# Add railway.json to repo
import urllib.request, json, base64

# Check if railway.json exists
try:
    req_check = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway.json', headers=headers)
    existing = json.loads(urllib.request.urlopen(req_check).read())
    existing_sha = existing['sha']
    print(f"railway.json exists, SHA: {existing_sha}")
except:
    existing_sha = None
    print("railway.json does not exist, creating new")

if existing_sha:
    body = json.dumps({
        "message": "chore: update railway.json start command",
        "content": base64.b64encode(railway_json.encode('utf-8')).decode(),
        "sha": existing_sha,
    }).encode()
else:
    body = json.dumps({
        "message": "chore: add railway.json for deploy config",
        "content": base64.b64encode(railway_json.encode('utf-8')).decode(),
    }).encode()

put_req = urllib.request.Request(
    "https://api.github.com/repos/qiezibot/qiezidata/contents/railway.json",
    data=body, method="PUT",
    headers={**headers, "Content-Type": "application/json"}
)
try:
    put_r = urllib.request.urlopen(put_req)
    resp = json.loads(put_r.read())
    print(f"railway.json push OK, SHA: {resp['content']['sha']}")
except urllib.error.HTTPError as e:
    print(f"Error: {e.code} {e.read().decode()[:200]}")
