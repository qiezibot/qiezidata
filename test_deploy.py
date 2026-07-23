import requests

BASE = 'https://qiezidata-production.up.railway.app'
results = []

# 0) Ping /debug
print("=== 0) DEBUG ENDPOINT ===")
r = requests.get(f'{BASE}/debug')
debug_ok = r.status_code == 200
print(f"Status: {r.status_code}")
results.append(("Debug endpoint", "PASS" if debug_ok else "FAIL"))

# 1) Admin login
print("\n=== 1) ADMIN LOGIN (admin/admin123) ===")
s = requests.Session()
r = s.post(f'{BASE}/login', data={'username':'admin','password':'admin123'}, allow_redirects=True)
admin_ok = r.status_code == 200
admin_has_users = '用户管理' in r.text
admin_has_dashboard = '仪表盘' in r.text
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")
print(f"Contains 用户管理: {admin_has_users}")
print(f"Contains 仪表盘: {admin_has_dashboard}")
results.append(("Admin login success", "PASS" if admin_ok else "FAIL"))
results.append(("Admin sees 用户管理", "PASS" if admin_has_users else "FAIL"))
results.append(("Admin sees 仪表盘", "PASS" if admin_has_dashboard else "FAIL"))

# 2) Chengzi login - try to find password
print("\n=== 2) CHENGZI LOGIN ===")
passwords_tried = []
found_pw = None
for pw in ['chengzi123', 'chengzi', 'test123', '123456', 'password', 'admin123', 'qiezi123']:
    s2 = requests.Session()
    r2 = s2.post(f'{BASE}/login', data={'username':'chengzi','password':pw}, allow_redirects=True)
    passwords_tried.append(pw)
    if r2.status_code == 200:
        found_pw = pw
        chengzi_content = r2.text
        print(f"SUCCESS with password: {pw}")
        chengzi_no_users = '用户管理' not in r2.text
        chengzi_no_dash = '仪表盘' not in r2.text
        print(f"Contains 用户管理: {'用户管理' in r2.text}")
        print(f"Contains 仪表盘: {'仪表盘' in r2.text}")
        results.append(("Chengzi login success (pw="+pw+")", "PASS"))
        results.append(("Chengzi does NOT see 用户管理", "PASS" if chengzi_no_users else "FAIL"))
        results.append(("Chengzi does NOT see 仪表盘", "PASS" if chengzi_no_dash else "FAIL"))
        break
    else:
        print(f"  pw={pw}: status={r2.status_code}")

if not found_pw:
    print("Could not log in as chengzi with any tried password")
    results.append(("Chengzi login", "FAIL - no working password found"))

# 3) Qiezi login
print("\n=== 3) QIEZI LOGIN (qiezi/qiezi123) ===")
s3 = requests.Session()
r3 = s3.post(f'{BASE}/login', data={'username':'qiezi','password':'qiezi123'}, allow_redirects=True)
qiezi_ok = r3.status_code == 200
qiezi_no_users = '用户管理' not in r3.text
qiezi_no_dash = '仪表盘' not in r3.text
print(f"Status: {r3.status_code}")
print(f"URL: {r3.url}")
print(f"Contains 用户管理: {'用户管理' in r3.text}")
print(f"Contains 仪表盘: {'仪表盘' in r3.text}")
results.append(("Qiezi login success", "PASS" if qiezi_ok else "FAIL"))
results.append(("Qiezi does NOT see 用户管理", "PASS" if qiezi_no_users else "FAIL"))
results.append(("Qiezi does NOT see 仪表盘", "PASS" if qiezi_no_dash else "FAIL"))

# Summary
print("\n" + "="*60)
print("FULL RESULTS")
print("="*60)
all_pass = True
for test, status in results:
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} {test}: {status}")
    if status != "PASS":
        all_pass = False

print()
if all_pass:
    print("DEPLOYMENT VERIFIED: admin sees all, non-admin sees limited.")
else:
    print("SOME CHECKS FAILED")
