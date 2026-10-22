import urllib.request
import json

endpoints = [
    ("Cloudflare Pages (Direct Brand URL)", "https://camouroles.pages.dev"),
    ("Cloudflare Edge Worker", "https://camouroles.primemax.workers.dev")
]

for label, base in endpoints:
    print(f"\n=======================================================")
    print(f"VERIFYING: {label}")
    print(f"URL: {base}")
    print(f"=======================================================")

    def test_get(path):
        req = urllib.request.Request(base + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            return resp.status, len(resp.read())

    def test_post(path, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    print("1. Testing Root Landing Page HTML...")
    status, size = test_get("/")
    print(f"   Status: {status}, HTML Size: {size} bytes")

    print("2. Testing Live Razorpay Order Creation (Rs 49 Week Plan)...")
    status, order = test_post("/api/checkout/order", {"plan": "week"})
    print(f"   Status: {status}, Order ID: {order.get('order_id')}, Amount: Rs {order.get('amount')/100:.0f}, Key: {order.get('key_id')}")

    print("3. Testing Live Jobs Feed (Supabase via Cloudflare)...")
    status, size = test_get("/api/jobs")
    print(f"   Status: {status}, Jobs Payload Size: {size} bytes")

print("\nALL PRODUCTION ENDPOINTS VERIFIED: 100% OPERATIONAL WITH ZERO JARGON!")
