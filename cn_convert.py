with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find template boundaries: _LOGIN, _ADMIN, _USER
login_assign_end = content.find('"""\n\n_ADMIN = ')
admin_assign_end = content.find('"""\n\n_USER = ')
user_assign_end = content.find('"""\n\n\nif __name__')
if user_assign_end == -1:
    user_assign_end = content.find('"""\n\nif __name__')

# Get template start offsets (after the """\ marker)
login_val_start = content.find('"""\\') + 4
admin_val_start = content.find('"""\\', login_assign_end) + 4
user_val_start = content.find('"""\\', admin_assign_end) + 4

# Extract text
login_inner = content[login_val_start:login_assign_end]
admin_inner = content[admin_val_start:admin_assign_end]
user_inner = content[user_val_start:user_assign_end]

print(f"Sizes: login={len(login_inner)}, admin={len(admin_inner)}, user={len(user_inner)}")
print(f"Total file: {len(content)}")

# ========== LOGIN replacement ==========
l = login_inner

# All replacements for LOGIN
login_map = {
    'Eggplant Data</title>': '\u8304\u5b50\u6570\u636e</title>',
    'File Manager v2.1</p>': '\u6587\u4ef6\u7ba1\u7406 v2.1</p>',
    'Login</div>': '\u767b\u5f55</div>',
    'Register</div>': '\u6ce8\u518c</div>',
    'Enter username': '\u8f93\u5165\u7528\u6237\u540d',
    'Enter password': '\u8f93\u5165\u5bc6\u7801',
    'Login</button>': '\u767b\u5f55</button>',
    'Wrong username or password': '\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef',
    'Register</button>': '\u6ce8\u518c</button>',
    'Registered OK, please login': '\u6ce8\u518c\u6210\u529f\uff0c\u8bf7\u767b\u5f55',
}

# Context-aware replacements (need to match the full attribute text)
# For login form username label+input
for old, new in {
    '<label>Username</label><input type="text" name="username" placeholder="Enter username" required autofocus>': '<label>\u7528\u6237\u540d</label><input type="text" name="username" placeholder="\u8f93\u5165\u7528\u6237\u540d" required autofocus>',
    '<label>Password</label><input type="password" name="password" placeholder="Enter password" required>': '<label>\u5bc6\u7801</label><input type="password" name="password" placeholder="\u8f93\u5165\u5bc6\u7801" required>',
    '<label>Username</label><input type="text" name="username" id="regUser" placeholder="2-20 chars" required minlength="2" maxlength="20" pattern="^[a-zA-Z0-9_]+$">': '<label>\u7528\u6237\u540d</label><input type="text" name="username" id="regUser" placeholder="2-20\u4e2a\u5b57\u7b26" required minlength="2" maxlength="20" pattern="^[a-zA-Z0-9_]+$">',
    '<label>Display Name</label><input type="text" name="display_name" placeholder="Optional" maxlength="30">': '<label>\u663e\u793a\u540d\u79f0</label><input type="text" name="display_name" placeholder="\u9009\u586b" maxlength="30">',
    '<label>Password</label><input type="password" name="password" id="regPass" placeholder="Min 4 chars" required minlength="4">': '<label>\u5bc6\u7801</label><input type="password" name="password" id="regPass" placeholder="\u81f3\u5c114\u4e2a\u5b57\u7b26" required minlength="4">',
}.items():
    assert old in l, f"Login missing: {old[:50]}"
    l = l.replace(old, new)

for old, new in login_map.items():
    if old in l:
        l = l.replace(old, new)
    else:
        print(f"Login SKIP (not found): {old[:40]}")

print(f"Login: {len(login_inner)} -> {len(l)}")

# ========== ADMIN replacement ==========
a = admin_inner

# Remove the corrupted emoji prefix before each keyword
admin_map = {
    'Dashboard</div>': '\u4eea\u8868\u76d8</div>',
    'Files</div>': '\u6587\u4ef6\u7ba1\u7406</div>',
    'Upload</div>': '\u4e0a\u4f20</div>',
    'Users</div>': '\u7528\u6237\u7ba1\u7406</div>',
    'Logout</a>': '\u9000\u51fa</a>',
    'All Files': '\u5168\u90e8\u6587\u4ef6',
    'Users</h2>': '\u7528\u6237\u5217\u8868</h2>',
    'No files': '\u6682\u65e0\u6587\u4ef6',
    'My Files': '\u6211\u7684\u6587\u4ef6',
    'None</p>': '\u6682\u65e0\u6587\u4ef6</p>',
    "Toast('Uploaded'": "Toast('\u4e0a\u4f20\u6210\u529f'",
    "Toast('Failed'": "Toast('\u4e0a\u4f20\u5931\u8d25'",
}

# Full context replacements  
admin_full = {
    '<title>Admin - Eggplant Data</title>': '<title>\u7ba1\u7406\u540e\u53f0 - \u8304\u5b50\u6570\u636e</title>',
    '<div class="label">Users</div>': '<div class="label">\u7528\u6237\u6570</div>',
    '<div class="label">Files</div>': '<div class="label">\u6587\u4ef6\u6570</div>',
    '<div class="label">Storage</div>': '<div class="label">\u5b58\u50a8\u91cf</div>',
    '<div class="label">Admins</div>': '<div class="label">\u7ba1\u7406\u5458</div>',
    '<p>Drag & drop or click</p>': '<p>\u62d6\u62fd\u6587\u4ef6\u5230\u6b64\u5904\u6216\u70b9\u51fb\u9009\u62e9</p>',
    '<th>ID</th><th>Username</th><th>Display</th><th>Role</th><th>Created</th>': '<th>ID</th><th>\u7528\u6237\u540d</th><th>\u663e\u793a\u540d\u79f0</th><th>\u89d2\u8272</th><th>\u521b\u5efa\u65f6\u95f4</th>',
    '<h2>Upload</h2>': '<h2>\u4e0a\u4f20\u6587\u4ef6</h2>',
}

for old, new in admin_full.items():
    assert old in a, f"Admin full missing: {old[:50]}"
    a = a.replace(old, new)

for old, new in admin_map.items():
    if old in a:
        a = a.replace(old, new)
    else:
        print(f"Admin SKIP (not found): {old[:40]}")

# Fix "B · owner"  
a = a.replace("B \u00b7 ", "B | ")

print(f"Admin: {len(admin_inner)} -> {len(a)}")

# ========== USER replacement ==========
u = user_inner

user_map = {
    'Logout</a>': '\u9000\u51fa</a>',
    'None</p>': '\u6682\u65e0\u6587\u4ef6</p>',
    "if(!confirm('Delete?'))": "if(!confirm('\u786e\u5b9a\u5220\u9664\uff1f'))",
    "Toast('Uploaded'": "Toast('\u4e0a\u4f20\u6210\u529f'",
    "Toast('Failed'": "Toast('\u4e0a\u4f20\u5931\u8d25'",
    "Toast('Deleted'": "Toast('\u5220\u9664\u6210\u529f'",
}

user_full = {
    '<title>Eggplant Data - My Files</title>': '<title>\u6211\u7684\u6587\u4ef6 - \u8304\u5b50\u6570\u636e</title>',
    '<p>Drag & drop or click</p>': '<p>\u62d6\u62fd\u6587\u4ef6\u5230\u6b64\u5904\u6216\u70b9\u51fb\u9009\u62e9</p>',
    '<h2>Upload</h2>': '<h2>\u4e0a\u4f20\u6587\u4ef6</h2>',
    '<h2>My Files</h2>': '<h2>\u6211\u7684\u6587\u4ef6</h2>',
}

for old, new in user_full.items():
    assert old in u, f"User full missing: {old[:50]}"
    u = u.replace(old, new)

for old, new in user_map.items():
    if old in u:
        u = u.replace(old, new)
    else:
        print(f"User SKIP (not found): {old[:40]}")

# Fix download/delete icon references
u = u.replace('download>\u9983\u9233</a>', 'download>\u4e0b\u8f7d</a>')
u = u.replace('">\u9983\u9233</button>', '">\u5220\u9664</button>')

print(f"User: {len(user_inner)} -> {len(u)}")

# ========== Rebuild ==========
new_content = (content[:login_val_start] + l +
               content[login_assign_end:admin_val_start] + a +
               content[admin_assign_end:user_val_start] + u +
               content[user_assign_end:])

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Final: {len(content)} -> {len(new_content)} bytes")

# Verify markers
v = new_content
assert '_LOGIN = """\\' in v, "Missing _LOGIN"
assert '_ADMIN = """\\' in v, "Missing _ADMIN"
assert '_USER = """\\' in v, "Missing _USER"
assert "if __name__ == '__main__':" in v, "Missing __main__"

# Verify Chinese
cn = ['\u767b\u5f55', '\u6ce8\u518c', '\u4eea\u8868\u76d8', '\u6587\u4ef6\u7ba1\u7406', '\u7528\u6237\u7ba1\u7406', '\u4e0a\u4f20', '\u6211\u7684\u6587\u4ef6']
for t in cn:
    assert t in v, f"Missing Chinese: {t}"
print("All Chinese terms present!")

# Verify no broken emoji sequences
count_broken = sum(1 for c in v if ord(c) == 0x9983)
print(f"Corrupted emoji remaining: {count_broken}")
