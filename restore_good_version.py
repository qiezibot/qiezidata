"""Fix the broken triple-quote in the file by restoring the previous version and redoing the fix safely"""
import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get the commit BEFORE my broken fix
# The previous good commit was 83a0a4d0c2a2 (from move_modals_correct.py)
# Let me get the file from that commit
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py?ref=83a0a4d0c2a2', 
    headers=headers)
if r.status_code == 200:
    content = base64.b64decode(r.json()['content']).decode('utf-8')
    sha = r.json()['sha']
    print(f'Restored to commit 83a0a4d0: {len(content)} bytes, SHA: {sha[:12]}')
    
    # Verify syntax
    try:
        compile(content, 'test.py', 'exec')
        print('Python syntax: OK ✓')
    except SyntaxError as e:
        print(f'Syntax error: {e}')
    
    # Push this restored version
    payload = {
        'message': 'Restore to working version (83a0a4d)',
        'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        'sha': (requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', 
                headers=headers).json())['sha'],
        'branch': 'main'
    }
    r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', 
                      headers=headers, json=payload)
    print(f'Push: {r2.status_code}')
    if r2.status_code in (200, 201):
        print(f'Restored to 83a0a4d0 commit')
else:
    print(f'Error fetching old commit: {r.status_code}')
    # Try an even earlier commit
    for ref in ['d35a9839', 'ca5fb4b4']:
        r = requests.get(f'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py?ref={ref}',
            headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            try:
                compile(content, 'test.py', 'exec')
                print(f'{ref}: OK ✓ ({len(content)} bytes)')
                break
            except SyntaxError as e:
                print(f'{ref}: Syntax error: {e}')
