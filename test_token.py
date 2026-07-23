import urllib.request, json
TOKEN = "Bot 1904006743.iItV7kO2hM2jQ8qZJ3oaM9wkZOE4vnfY"
req = urllib.request.Request("https://api.sgroup.qq.com/gateway")
req.add_header("Authorization", TOKEN)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    print("Status:", resp.status)
    data = json.loads(resp.read())
    print("URL:", data.get("url"))
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.read().decode())
except Exception as e:
    print("Error:", e)
