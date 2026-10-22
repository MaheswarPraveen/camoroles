import httpx
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

query = """
query GetRoles($searchQueryInput: RoleSearchQueryInput!) {
  roleSearch(searchQueryInput: $searchQueryInput) {
    totalCount
    items {
      roleId
      corporateTitle
      jobTitle
      jobFunction
      locations {
        primary
        state
        country
        city
      }
      status
      division
      skills
    }
  }
}
"""

payload = {
    "operationName": "GetRoles",
    "variables": {
        "searchQueryInput": {
            "page": {
                "pageSize": 50,
                "pageNumber": 0
            },
            "experiences": ["EARLY_CAREER", "PROFESSIONAL"],
            "searchTerm": ""
        }
    },
    "query": query
}

r = httpx.post("https://api-higher.gs.com/gateway/api/v1/graphql", headers=headers, json=payload, timeout=10.0)
print("GS Gateway GraphQL Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    items = data.get("data", {}).get("roleSearch", {}).get("items", [])
    total = data.get("data", {}).get("roleSearch", {}).get("totalCount", 0)
    print(f"TOTAL REAL GOLDMAN SACHS ROLES LIVE: {total}, fetched {len(items)}")
    for it in items[:10]:
        locs = ", ".join([f"{l.get('city')}, {l.get('country')}" for l in (it.get('locations') or [])])
        print(f"  [{it.get('roleId')}] {it.get('jobTitle')} ({it.get('corporateTitle')}) | {it.get('division')} | {locs}")
else:
    print("Response:", r.text[:300])
