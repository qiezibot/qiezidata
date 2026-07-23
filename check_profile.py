import requests
s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

# Extract the real profileModal content
pos = html.find('id="profileModal"')
if pos >= 0:
    # Find the closing div (matching nested divs)
    content = html[pos:]
    # Print first 2000 chars to see all fields
    print(content[:2000])
