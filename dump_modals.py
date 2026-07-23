import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

# Extract the real profileModal and surrounding content
pos = html.find('id="profileModal"')
if pos < 0:
    print("ERROR: Could not find profileModal")
    exit()

# Print everything from that point to the end of the modal div  
content = html[pos:]
# Find the closing of the outermost profileModal div
depth = 1
end = 0
for i in range(len('<div id="profileModal">'), len(content)):
    if content[i:i+3] == '<div':
        if 'profileModal' in content[i:i+50]:
            depth += 1
    elif content[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            end = i + 6
            break
        # Another </div> closes the outer modal too

# Simpler approach: just print with find of close pattern
# The modal is: <div id="profileModal" ...> ... </div>
# Then after it: <div id="pwdModal" ...> ... </div>
# After pwdModal, the next </div> closes something else

# Let me just print raw text between profileModal and the next </script> or </body>
idx1 = html.find('id="profileModal"')
idx2 = html.find('id="pwdModal"', idx1)
if idx2 > 0:
    # Content from profileModal to pwdModal
    modal_content = html[idx1:idx2]
    print("=== profileModal HTML ===")
    print(modal_content)
    print(f"\n=== Length: {len(modal_content)} chars ===")
    
    # Also check the pwdModal structure
    idx3 = html.find('id="pwdModal"', idx2+1)
    # Actually find where pwdModal ends
    pwd_start = html.find('<div id="pwdModal"', idx2-5)
    if pwd_start > 0:
        # Find where this div ends
        # Look for the pattern: </div>\n\n\n<div id="profileModal" or similar
        rest = html[pwd_start:]
        pwd_end = rest.find('</div>')
        rest2 = rest[pwd_end+6:]
        pwd_end2 = rest2.find('</div>')
        full_pwd = rest[:pwd_end+6+pwd_end2+6]
        print("\n=== pwdModal HTML ===")
        print(full_pwd[:500])
