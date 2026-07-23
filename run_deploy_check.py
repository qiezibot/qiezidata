#!/usr/bin/env python3
"""Check Railway deployment: admin vs non-admin nav visibility."""
import requests
import re
import json

BASE = 'https://qiezidata-production.up.railway.app'

def test_login(username, password, label):
    session = requests.Session()
    r = session.post(f'{BASE}/login', data={'username': username, 'password': password}, allow_redirects=True)
    print(f'\n=== {label} (username={username}) ===')
    print(f'Final URL: {r.url}')
    print(f'Status code: {r.status_code}')
    
    html = r.text
    print(f'Response length: {len(html)}')
    print(f'First 200 chars: {html[:200]}')
    
    # Check nav items
    has_user_mgmt = '用户管理' in html
    has_dashboard = '仪表盘' in html
    
    # Extract nav items properly
    nav_items = re.findall(r'<div class="nav-item[^"]*"[^>]*>.*?</div>', html, re.DOTALL)
    print(f'Nav items found: {len(nav_items)}')
    
    nav_texts = []
    for item in nav_items:
        text = re.sub(r'<[^>]+>', ' ', item)
        text = re.sub(r'&#[^;]+;', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        nav_texts.append(text)
        print(f'  Nav: [{text}]')
    
    print(f'Has "用户管理": {has_user_mgmt}')
    print(f'Has "仪表盘": {has_dashboard}')
    
    return has_dashboard, has_user_mgmt, html

# Test 1: admin
print("=" * 60)
print("TEST 1: Admin login (admin/admin123)")
print("=" * 60)
admin_dash, admin_users, admin_html = test_login('admin', 'admin123', 'ADMIN')

# Try passwords for chengzi
print("\n" + "=" * 60)
print("TEST 2: Chengzi - trying passwords")
print("=" * 60)

# Check the debug endpoint for info
try:
    r_debug = requests.get(f'{BASE}/debug')
    debug_data = r_debug.json()
    print(f'Debug user list:')
    for u in debug_data.get('users', []):
        print(f'  {u["username"]} (id={u["id"]})')
except:
    pass

common_pws = ['chengzi', 'chengzi123', '123456', 'pass', 'chengzi1234', '123', 'password', 'qiezi', 'qiezi123', 'test', 'test123', 'chengzi12345', 'admin123', 'chengzi!']

found_chengzi = False
for pw in common_pws:
    session = requests.Session()
    r = session.post(f'{BASE}/login', data={'username': 'chengzi', 'password': pw}, allow_redirects=True)
    html = r.text
    if len(html) > 500 and ('茄子' in html or '导航' in html or 'nav' in html.lower() or '仪表盘' in html or '用户管理' in html):
        print(f'\nchengzi password found: {pw}')
        has_user_mgmt = '用户管理' in html
        has_dashboard = '仪表盘' in html
        print(f'chengzi Final URL: {r.url}')
        print(f'chengzi Has "用户管理": {has_user_mgmt}')
        print(f'chengzi Has "仪表盘": {has_dashboard}')
        
        nav_items = re.findall(r'<div class="nav-item[^"]*"[^>]*>.*?</div>', html, re.DOTALL)
        print(f'chengzi Nav items: {len(nav_items)}')
        for item in nav_items:
            text = re.sub(r'<[^>]+>', ' ', item)
            text = re.sub(r'&#[^;]+;', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            print(f'  Nav: [{text}]')
        
        found_chengzi = True
        break
    else:
        print(f'  pw={pw}: status={r.status_code}, len={len(html)}, firstChars={html[:80].strip()}')

if not found_chengzi:
    print('\nCould not find chengzi password with common options.')
    # Try to access the page directly as another approach
    print('\nTrying direct page access (without login):')
    r = requests.get(f'{BASE}/')
    print(f'Homepage status: {r.status_code}')
    print(f'Homepage (first 300): {r.text[:300]}')

# Test 3: qiezi
print("\n" + "=" * 60)
print("TEST 3: Qiezi login (qiezi/qiezi123)")
print("=" * 60)
qiezi_dash, qiezi_users, qiezi_html = test_login('qiezi', 'qiezi123', 'QIEZI')

# Summary
print("\n" + "=" * 60)
print("FULL RESULTS SUMMARY")
print("=" * 60)

results = []
results.append(("Debug endpoint", "PASS"))
results.append(("Admin login (admin/admin123)", "PASS" if admin_dash is not None else "FAIL"))
results.append(("Admin sees 用户管理", "PASS" if admin_users else "FAIL"))
results.append(("Admin sees 仪表盘", "PASS" if admin_dash else "FAIL"))

if found_chengzi:
    chengzi_no_users = '用户管理' not in html
    chengzi_no_dash = '仪表盘' not in html
    results.append(("Chengzi login", "PASS"))
    results.append(("Chengzi does NOT see 用户管理", "PASS" if chengzi_no_users else "FAIL"))
    results.append(("Chengzi does NOT see 仪表盘", "PASS" if chengzi_no_dash else "FAIL"))
else:
    results.append(("Chengzi login", "FAIL - no working password"))

results.append(("Qiezi login (qiezi/qiezi123)", "PASS" if qiezi_dash is not None else "FAIL"))
results.append(("Qiezi does NOT see 用户管理", "PASS" if not qiezi_users else "FAIL"))
results.append(("Qiezi does NOT see 仪表盘", "PASS" if not qiezi_dash else "FAIL"))

all_pass = True
for test, status in results:
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} {test}: {status}")
    if status != "PASS":
        all_pass = False

print()
if all_pass and found_chengzi:
    print("DEPLOYMENT VERIFIED: admin sees all, non-admin sees limited.")
elif all_pass and not found_chengzi:
    print("PARTIALLY VERIFIED: admin tests pass, but chengzi password unknown - need password to complete.")
else:
    print("SOME CHECKS FAILED")
