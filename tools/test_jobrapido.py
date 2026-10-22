import httpx

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
r = httpx.get("https://in.jobrapido.com/?w=civil+engineer&l=Bengaluru", headers=headers, timeout=10.0)
print(r.text[1000:3000])
