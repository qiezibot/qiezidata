import requests, json

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Update ref to trigger deploy
url = 'https://api.github.com/repos/qiezibot/qiezidata/git/refs/heads/main'
payload = {'sha': 'c1cdd187ef87de9af82915e2740c90da4ff918be', 'force': True}
r = requests.patch(url, headers=headers, json=payload)
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2)[:300])
