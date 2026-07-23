import re

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find Login template
login_pat = re.compile(r'_LOGIN = """\\(.*?)"""\n\n_ADMIN', re.DOTALL)
m = login_pat.search(content)
if m:
    t = m.group(1)
    print("=== LOGIN template ===")
    checks = [
        'Eggplant Data</title>',
        'Login</div>',
        'Register</div>',
        'Username</label>',
        'Enter username',
        'Password</label>',
        'Enter password',
        'Login</button>',
        'Register</button>',
        'Display Name',
        'Optional',
        'Min 4 chars',
        '2-20 chars',
        'Wrong username',
    ]
    for c in checks:
        print(f"  '{c[:50]}': {'found' if c in t else 'MISSING'}")

# Find Admin template
admin_pat = re.compile(r'_ADMIN = """\\(.*?)"""\n\n_USER = """\\', re.DOTALL)
m2 = admin_pat.search(content)
if m2:
    t = m2.group(1)
    print("\n=== ADMIN template ===")
    checks = [
        'Admin - Eggplant Data</title>',
        'Eggplant Data</a>',
        'Logout</a>',
        'Dashboard</div>',
        'Files</div>',
        'Upload</div>',
        'Users</div>',
        'Users</div>',  # stat label
        'Files</div>',
        'Storage</div>',
        'Admins</div>',
        'All Files',
        'Upload</h2>',
        'Users</h2>',
        'No files',
        'Drag & drop',
        'My Files',
        '<th>ID</th><th>Username</th><th>Display</th><th>Role</th><th>Created</th>',
        'None</p>',
        "Uploaded','success'",
        "Failed','error'",
        "Delete?",
        "Deleted','success'",
        "B · ",
    ]
    for c in checks:
        print(f"  '{c[:60]}': {'found' if c in t else 'MISSING'}")

# Find User template
user_pat = re.compile(r'_USER = """\\(.*?)"""\n\n\n+if __name__', re.DOTALL)
m3 = user_pat.search(content)
if not m3:
    user_pat = re.compile(r'_USER = """\\(.*?)"""\n\nif __name__', re.DOTALL)
    m3 = user_pat.search(content)
if m3:
    t = m3.group(1)
    print("\n=== USER template ===")
    checks = [
        'My Files</title>',
        'Eggplant Data</a>',
        'Logout</a>',
        'Upload</h2>',
        'Drag & drop',
        'My Files</h2>',
        'None</p>',
        "Delete?",
        "Uploaded','success'",
        "Failed','error'",
        "Deleted','success'",
        '\U0001f4e5</a>',
        '\U0001f5d1</button>',
    ]
    for c in checks:
        print(f"  '{c[:50]}': {'found' if c in t else 'MISSING'}")
