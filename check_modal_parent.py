"""Check what profileModal's parent elements are in the deployed page"""
import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', 
    data={'username': 'admin', 'password': 'admin123'},
    allow_redirects=True)
html = s.get('https://qiezidata-production.up.railway.app/', headers={'Cache-Control': 'no-cache'}).text

# Find profileModal div and look backward to find its parent chain
pm_idx = html.find('<div id="profileModal"')
print(f'profileModal at page position: {pm_idx}')

# Look backward to find parent divs
# Find the closest preceding <div tag that hasn't been closed yet
depth = 0
pos = pm_idx
# Count how many divs are open by looking at tags between <body> and profileModal
body_idx = html.find('<body>')
section = html[body_idx:pm_idx]

# Count all <div> and </div> to find what's the immediate parent
div_open = 0
last_div_open = -1
# Track open divs
for m in __import__('re').finditer(r'</?div[^>]*>', section, __import__('re').IGNORECASE):
    tag = m.group()
    if tag.startswith('</div'):
        div_open -= 1
    else:
        div_open += 1
        last_div_open = m.start() + body_idx

print(f'Open divs before profileModal: {div_open}')
if last_div_open >= 0:
    print(f'Last <div> before profileModal is at pos {last_div_open}:')
    # Show its id or class
    print(html[last_div_open:min(last_div_open+200, pm_idx)])
    
# Now let me check if profileModal is inside a tab-page or anything with transform
for parent_id in ['tab-page', 'page-', 'sidebar', 'content', 'main']:
    # Check if profileModal is nested inside certain elements
    pass

# Check if any parent has transform computed style
# Instead, let me check the HTML structure
print('\n=== HTML around profileModal parent area ===')
# Show from the last 100 chars before profileModal
print(html[pm_idx-1000:pm_idx-500])
print('---')
print(html[pm_idx-500:pm_idx])
