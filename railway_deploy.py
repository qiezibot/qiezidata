import requests, json, base64

GH_TOKEN = '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'

# Railway's GraphQL to create a deployment
query = """
mutation {
  deploymentCreate(
    input: {
      projectId: "2501b9b9-59c8-4422-95e4-f52f19e1f9b6",
      environmentId: "d1adc694-af40-4d18-a352-d642a1f327c9"
    }
  ) {
    id
  }
}
"""

# Try Railway API
r = requests.post(
    'https://backboard.railway.com/graphql/v2',
    headers={'Authorization': 'Bearer ' + GH_TOKEN, 'Content-Type': 'application/json'},
    json={'query': query}
)
print('Railway API:', r.status_code)
print(r.text[:300])
