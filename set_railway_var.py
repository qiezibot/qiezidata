"""添加 Railway 环境变量 SECRET_KEY"""
import requests, json

railway_token = 'HtDR2fKWVj3NXxpnxWF9lWxVmNYoA1FTBdRs1G5iPkjNQ6UfJLp2h6Dgg3rfgE6a'
url = 'https://api.railway.app/graphql/v2'

# 先查项目
query = {"query": "{ projects { id name } }"}
r = requests.post(url, json=query, headers={
    'Authorization': f'Bearer {railway_token}',
    'Content-Type': 'application/json'
})
print(f'Query: {r.status_code}')
try:
    data = r.json()
    print(json.dumps(data, indent=2)[:500])
except:
    print(r.text[:500])
