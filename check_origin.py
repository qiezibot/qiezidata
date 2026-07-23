raw = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_original.py', 'rb').read()
text = raw.decode('utf-8')

idx = text.find('_ADMIN = """')
content_start = idx + len('_ADMIN = """')
print(f'ADMIN content starts at {content_start}')

# Find the closing marker
end_marker = text.find('"""\n\n\n\n\n\n\n\n\n\n\n\n\n# ---- CloudData', content_start)
if end_marker < 0:
    end_marker = text.find('"""\n\n# ---- CloudData', content_start)
if end_marker < 0:
    # Look for any """ after content_start that precedes CloudData section
    pos = text.find('CloudData', content_start)
    # Look backwards for """
    end_marker = text.rfind('"""', content_start, pos)

print(f'End marker at {end_marker}')
adm = text[content_start:end_marker]
print(f'ADMIN length: {len(adm)}')
has_pwd = 'pwdModal' in adm
has_id = 'id="pwdModal"' in adm
print(f'Has pwdModal: {has_pwd}')
print(f'Has id="pwdModal": {has_id}')

# Show the last 200 chars of admin
print(f'Last 200 chars: {repr(adm[-200:])}')
