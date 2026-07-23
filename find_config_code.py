import requests, re

r = requests.get('https://raw.githubusercontent.com/qiezibot/qiezidata/main/railway_file_server.py')
c = r.text

# Find config save/load related code
for pat in ['save_config', 'read_config', 'config_file', 'CONFIG_FILE', 'config_data', 'CONFIG_JSON', 'load_config']:
    for m in re.finditer(pat, c, re.IGNORECASE):
        start = max(0, m.start()-80)
        end = min(len(c), m.end()+160)
        print(f'--- {m.group()} at {m.start()} ---')
        print(c[start:end])
        print()
