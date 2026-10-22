import urllib.request
import json

base = "http://127.0.0.1:8000"

def test_get(path):
    req = urllib.request.Request(base + path)
    with urllib.request.urlopen(req) as resp:
        return resp.status, len(resp.read())

def test_post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

print("1. Testing GET / (Landing Page)...")
status, size = test_get("/")
print(f"   Status: {status}, HTML Size: {size} bytes")

print("2. Testing GET /api/jobs (Job Database)...")
status, size = test_get("/api/jobs")
print(f"   Status: {status}, Payload Size: {size} bytes")

print("3. Testing POST /api/auth/google (OAuth)...")
status, auth_data = test_post("/api/auth/google", {"credential": "dev_test_token", "savedIds": []})
user_info = auth_data.get("user", {})
print(f"   Status: {status}, Authenticated User: {user_info.get('name')} ({user_info.get('email')})")

print("4. Testing POST /api/checkout/order (Monthly Pro - Rs 99)...")
status, order_m = test_post("/api/checkout/order", {"plan": "month"})
print(f"   Status: {status}, Order ID: {order_m.get('order_id')}, Amount: Rs {order_m.get('amount')/100:.0f}, Key ID: {order_m.get('key_id')}")

print("5. Testing POST /api/checkout/order (Weekly Pass - Rs 49)...")
status, order_w = test_post("/api/checkout/order", {"plan": "week"})
print(f"   Status: {status}, Order ID: {order_w.get('order_id')}, Amount: Rs {order_w.get('amount')/100:.0f}, Key ID: {order_w.get('key_id')}")

print("\nALL MONETIZATION & AUTH ENDPOINTS VERIFIED OPERATIONAL!")
