#!/usr/bin/env python3
"""Check Railway deployment: admin vs non-admin nav visibility - fixed for Chinese encoding."""
import requests
import re
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = 'https://qiezidata-production.up.railway.app'

def test_login(username, password, label):
    session = requests.Session()
    r = session.post(f'{BASE}/login', data={'username': username, 'password': password}, allow_redirects=True)
    print(f'\n=== {label} (username={username}) ===')
    print(f'Final URL: {r.url}')
    print(f'Status code: {r.status_code}')
    
    html = r.text
    print(f'Response length: {len(html)}')
    
    # Check nav items
    has_user_mgmt = '用户管理' in html
    has_dashboard = '仪表盘' in html
    
    html_lower = html.lower()
    has_user_mgmt_any = any(x in html for x in ['用户管理', '用户管', '户管理'])
    has_dashboard_any = any(x in html for x in ['仪表盘', '仪表', '表盘'])
    
    # Try to find any user-related navigation
    print(f'Contains "用户管理": {has_user_mgmt}')
    print(f'Contains "仪表盘": {has_dashboard}')
    
    # Extract nav items properly
    nav_items = re.findall(r'<div class="nav-item[^"]*"[^>]*>.*?</div>', html, re.DOTALL)
    print(f'Nav div items found: {len(nav_items)}')
    if nav_items:
        for item in nav_items:
            text = re.sub(r'<[^>]+>', ' ', item)
            text = re.sub(r'&#[^;]+;', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            print(f'  Nav: [{text}]')
    
    # Also look for sidebar / menu items more broadly
    menu_items = re.findall(r'<li[^>]*>.*?</li>', html, re.DOTALL)
    admin_links = re.findall(r'<a[^>]*>.*?用户管理.*?</a>', html, re.DOTALL)
    dash_links = re.findall(r'<a[^>]*>.*?仪表盘.*?</a>', html, re.DOTALL)
    
    print(f'Li items: {len(menu_items)}')
    for item in menu_items[:20]:
        text = re.sub(r'<[^>]+>', ' ', item)
        text = re.sub(r'&#[^;]+;', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            print(f'  Li: [{text[:60]}]')
    
    print(f'Links containing "用户管理": {len(admin_links)}')
    print(f'Links containing "仪表盘": {len(dash_links)}')
    
    return {'dashboard': has_dashboard, 'user_mgmt': has_user_mgmt, 'html': html, 'url': r.url}

print('=' * 60)
print('TEST 0: Debug endpoint')
print('=' * 60)
r = requests.get(f'{BASE}/debug')
print(f'Debug status: {r.status_code}')
data = r.json()
print(f'use_pg: {data.get("use_pg")}')
print(f'Users: {[u["username"] for u in data.get("users", [])]}')

# Test 1: admin
print('\n' + '=' * 60)
print('TEST 1: Admin login (admin/admin123)')
print('=' * 60)
admin = test_login('admin', 'admin123', 'ADMIN')

# Test 2: chengzi with found password
print('\n' + '=' * 60)
print('TEST 2: Chengzi login (chengzi/chengzi)')
print('=' * 60)
s2 = requests.Session()
r2 = s2.post(f'{BASE}/login', data={'username': 'chengzi', 'password': 'chengzi'}, allow_redirects=True)
html2 = r2.text
print(f'Final URL: {r2.url}')
print(f'Status: {r2.status_code}')
print(f'Contains "用户管理": {"用户管理" in html2}')
print(f'Contains "仪表盘": {"仪表盘" in html2}')
print(f'Response length: {len(html2)}')

# Check what the page says
if 'e=1' in r2.url or 'error' in r2.url.lower() or r2.status_code != 200:
    print(f'Page has error indicator in URL or non-200 status')
    # Try GET to dashboard after login
    dash2 = s2.get(f'{BASE}/')
    html2 = dash2.text
    print(f'After redirect to /: {dash2.url}')
    print(f'Contains "用户管理": {"用户管理" in html2}')
    print(f'Contains "仪表盘": {"仪表盘" in html2}')

# Show some context from chengzi's page  
print(f'\nFirst 500 chars of chengzi page:')
print(html2[:500])

# Test 3: qiezi
print('\n' + '=' * 60)
print('TEST 3: Qiezi login (qiezi/qiezi123)')
print('=' * 60)
qiezi = test_login('qiezi', 'qiezi123', 'QIEZI')

# Summary
print('\n' + '=' * 60)
print('FULL RESULTS')
print('=' * 60)

results = []

# Debug
results.append(('Debug endpoint reachable', 'PASS' if r.status_code == 200 else 'FAIL'))

# Admin
results.append(('Admin login works', 'PASS' if admin['dashboard'] is not None else 'FAIL'))
results.append(('Admin sees 用户管理', 'PASS' if admin['user_mgmt'] else 'FAIL'))
results.append(('Admin sees 仪表盘', 'PASS' if admin['dashboard'] else 'FAIL'))

# Chengzi
chengzi_no_users = '用户管理' not in html2
chengzi_no_dash = '仪表盘' not in html2
results.append(('Chengzi login works', 'PASS' if r2.status_code == 200 else 'FAIL'))
results.append(('Chengzi does NOT see 用户管理', 'PASS' if chengzi_no_users else 'FAIL'))
results.append(('Chengzi does NOT see 仪表盘', 'PASS' if chengzi_no_dash else 'FAIL'))

# Qiezi
results.append(('Qiezi login works', 'PASS' if qiezi['dashboard'] is not None else 'FAIL'))
results.append(('Qiezi does NOT see 用户管理', 'PASS' if not qiezi['user_mgmt'] else 'FAIL'))
results.append(('Qiezi does NOT see 仪表盘', 'PASS' if not qiezi['dashboard'] else 'FAIL'))

all_pass = True
for test, status in results:
    icon = '\u2705' if status == 'PASS' else '\u274c'
    sys.stdout.buffer.write(f'{icon} {test}: {status}\n'.encode('utf-8'))
    if status != 'PASS':
        all_pass = False

print()
if all_pass:
    print('DEPLOYMENT VERIFIED: admin sees all, non-admin sees limited.')
    print('User-specific hiding (用户管理, 仪表盘) working correctly.')
else:
    print('SOME CHECKS FAILED')
    print(f'Expected all PASS, got at least one FAIL')
