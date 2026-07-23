import urllib.request, json

TOKEN = "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"
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "push-script"}

# Force rollback to 632789c - the known good version
roll_to = "632789cb7a35597984c7e61fc77c1668afd00238"

req = urllib.request.Request(
    "https://api.github.com/repos/qiezibot/qiezidata/git/refs/heads/main",
    data=json.dumps({"sha": roll_to, "force": True}).encode(),
    method="PATCH",
    headers={**headers, "Content-Type": "application/json"}
)
try:
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f"Rollback to {roll_to[:12]}: {data['object']['sha'][:12]}")
except urllib.error.HTTPError as e:
    err = e.read().decode()
    print(f"Error {e.code}: {err[:300]}")
    # Try getting the exact commit object
    req2 = urllib.request.Request(f"https://api.github.com/repos/qiezibot/qiezidata/git/commits/{roll_to}", headers=headers)
    try:
        r2 = urllib.request.urlopen(req2)
        data2 = json.loads(r2.read())
        print(f"Commit found: tree={data2['tree']['sha'][:12]}")
        print(f"Parents: {[p['sha'][:12] for p in data2.get('parents', [])]}")
    except Exception as e2:
        print(f"Cannot find commit: {e2}")
