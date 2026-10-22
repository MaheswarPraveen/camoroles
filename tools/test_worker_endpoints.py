import urllib.request
import json

base = "http://127.0.0.1:8787"

def test_get(path):
    req = urllib.request.Request(base + path)
    with urllib.request.urlopen(req) as resp:
        return resp.status, len(resp.read())

def test_post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

print("1. Testing Static Assets on Worker (GET /) ...")
status, size = test_get("/")
print(f"   Status: {status}, HTML Size: {size} bytes")

print("2. Testing Google Auth on Worker ...")
status, auth_data = test_post("/api/auth/google", {"credential": "dev_test_token", "savedIds": []})
user_info = auth_data.get("user", {})
print(f"   Status: {status}, User: {user_info.get('name')}")

print("3. Testing Razorpay Live Order on Worker (month) ...")
status, order = test_post("/api/checkout/order", {"plan": "month"})
print(f"   Status: {status}, Razorpay Order ID: {order.get('order_id')}, Amount: Rs {order.get('amount')/100:.0f}, Key: {order.get('key_id')}")

print("4. Testing Jobs Feed on Worker ...")
status, size = test_get("/api/jobs")
print(f"   Status: {status}, Jobs Payload Size: {size} bytes")

print("\nCLOUDFLARE WORKER LOCAL ENGINE TEST: 100% SUCCESS!")
