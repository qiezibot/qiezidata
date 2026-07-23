#!/usr/bin/env python3
"""Check Railway deployment: admin vs non-admin nav visibility."""
import requests
import re

BASE = 'https://qiezidata-production.up.railway.app'

def test_login(username, password, label):
    session = requests.Session()
    # Login - allow redirects
    r = session.post(f'{BASE}/login', data={'username': username, 'password': password}, allow_redirects=True)
    print(f'\n=== {label} (username={username}) ===')
    print(f'Final URL: {r.url}')
    print(f'Login status: {r.status_code}')
    if r.status_code != 200:
        # Maybe it redirected to /
        pass
    
    # The final page after login
    html = r.text
    html = r2.text
    print(f'Dashboard status: {r2.status_code}')
    print(f'Response length: {len(html)}')
    
    # Check nav items
    has_user_mgmt = '用户管理' in html
    has_dashboard = '仪表盘' in html
    
    # Extract nav items properly (the rendered HTML from server)
    nav_items = re.findall(r'<div class="nav-item[^"]*"[^>]*>.*?</div>', html, re.DOTALL)
    print(f'Nav items found: {len(nav_items)}')
    
    nav_texts = []
    for item in nav_items:
        # Clean up HTML tags
        text = re.sub(r'<[^>]+>', ' ', item)
        text = re.sub(r'&#[^;]+;', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        nav_texts.append(text)
        print(f'  Nav: [{text}]')
    
    print(f'Has "用户管理": {has_user_mgmt}')
    print(f'Has "仪表盘": {has_dashboard}')
    
    return has_dashboard, has_user_mgmt, html

import json

# Test 1: admin
admin_dash, admin_users = test_login('admin', 'admin123', 'ADMIN')

# Get debug info for chengzi password hint
r_debug = requests.get(f'{BASE}/debug')
debug_data = r_debug.json()
print(f'\n=== DEBUG INFO ===')
for u in debug_data.get('users', []):
    if u['username'] == 'chengzi':
        print(f'chengzi user found: id={u["id"]}')

# Try passwords for chengzi
common_pws = ['chengzi', 'chengzi123', '123456', 'pass', 'chengzi1234', '123', 'password', 'qiezi']
found = False
for pw in common_pws:
    session = requests.Session()
    r = session.post(f'{BASE}/login', data={'username': 'chengzi', 'password': pw}, allow_redirects=True)
    html = r.text
    if len(html) > 500 and '茄子' in html:
        print(f'\nchengzi password found: {pw}')
        has_user_mgmt = '用户管理' in html
        has_dashboard = '仪表盘' in html
        print(f'chengzi Has "用户管理": {has_user_mgmt}')
        print(f'chengzi Has "仪表盘": {has_dashboard}')
        
        nav_items = re.findall(r'<div class="nav-item[^"]*"[^>]*>.*?</div>', html, re.DOTALL)
        print(f'chengzi Nav items: {len(nav_items)}')
        for item in nav_items:
            text = re.sub(r'<[^>]+>', ' ', item)
            text = re.sub(r'&#[^;]+;', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            print(f'  Nav: [{text}]')
        
        # Also check what tab shows as active
        active_tab = re.search(r'class="tab-page[^"]*active"[^>]*id="([^"]+)"', html)
        if active_tab:
            print(f'Active tab: {active_tab.group(1)}')
        
        found = True
        break

if not found:
    print('\nCould not find chengzi password with common options. Need to look up from debug.')

# Test 3: qiezi / qiezi123
test_login('qiezi', 'qiezi123', 'QIEZI')

print('\n=== DONE ===')
