"""
Update company filters for Meta and Apple in app.js
"""

for path in [r"C:\Claude Work\camoroles\static\app.js", r"C:\Claude Work\camoroles\web\app.js"]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    old = "if (compLower === 'scale ai') return c.includes('scale ai') || c.includes('scale');"
    new = """if (compLower === 'scale ai') return c.includes('scale ai') || c.includes('scale');
      if (compLower === 'meta') return c.includes('meta') || c.includes('facebook') || c.includes('reality labs');
      if (compLower === 'apple') return c.includes('apple');"""
    if old in content:
        content = content.replace(old, new)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated company filter in {path}")
    else:
        print(f"Warning: target not found in {path}")
