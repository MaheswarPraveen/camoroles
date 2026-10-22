for path in ["static/index.html", "web/index.html"]:
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    c = c.replace("7,400+", "7,540+").replace("7,271", "7,540")
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print(f"Updated {path}")
