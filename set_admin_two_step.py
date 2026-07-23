import urllib.request, json, ssl, http.cookiejar, urllib.parse

ctx = ssl.create_default_context()
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
r = opener.open("https://qiezidata-production.up.railway.app/login", data=login_data)
print("Login:", r.status)

# The real solution: just do it in two calls through set_id
# Step 1: create a dummy user with id=1 via register
# But register creates auto-increment ids...
# 
# OR: Use set_id in two steps via the buggy POST to manipulate the order
# 
# Actually the simplest: just drop and re-add the FK in the set_id function
# But that requires ALTER TABLE permission which it has
# 
# EVEN SIMPLER: directly patch the code to do BEGIN/COMMIT with DEFERRABLE constraints

# Let me try another approach entirely:
# Send raw SQL through a different endpoint
# Check admin.html for any db_query endpoint
r = opener.open("https://qiezidata-production.up.railway.app/")
html = r.read().decode("utf-8")
if "db" in html.lower() and ("query" in html.lower() or "exec" in html.lower() or "sql" in html.lower()):
    print("Found DB-related interface")
else:
    print("No DB admin interface in HTML")

# Let me look for routes
import re
routes = re.findall(r"@app\.(?:get|post|put|delete)\('([^']+)'\)", html)
for rt in routes:
    print(f"Route: {rt}")
