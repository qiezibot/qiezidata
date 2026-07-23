with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('async def script_cd_get')
# Get context before
print(f"Position {idx}")
print(f"Before: {repr(content[idx-100:idx])}")
print(f"After:  {repr(content[idx:idx+150])}")
