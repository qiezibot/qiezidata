import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

# Print entire HTML structure from last script to end
# Find all </script> positions
es = []
i = 0
while True:
    e = html.find('</script>', i)
    if e < 0: break
    es.append(e)
    i = e + 1

print("</script> positions:")
for e in es:
    print(f'  {e}: ...{html[max(0,e-30):e+20]}...')

last_script_end = es[-1] + 9
print(f'\nContent AFTER last </script> ({last_script_end}):')
print(html[last_script_end:last_script_end+1000])
print('...')
print(html[-500:])
