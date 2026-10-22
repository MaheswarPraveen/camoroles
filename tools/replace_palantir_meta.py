"""
Replace Palantir with Meta in static/index.html and web/index.html.
"""

import os

for path in [r"C:\Claude Work\camoroles\static\index.html", r"C:\Claude Work\camoroles\web\index.html"]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    old_palantir = """        <div class="company-showcase-item" data-company="palantir" onclick="setCompanyFilter('Palantir')" title="Filter Palantir Openings">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><circle cx="12" cy="12" r="3.5"/></svg>
          <span>Palantir</span>
        </div>"""

    new_meta = """        <div class="company-showcase-item" data-company="meta" onclick="setCompanyFilter('Meta')" title="Filter Meta Openings">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="#0081FB"><path d="M23.998 12c0-3.23-1.48-5.69-3.69-5.69-2.02 0-3.32 1.57-4.99 3.8-1.57-2.11-2.9-3.8-4.92-3.8-2.22 0-3.7 2.46-3.7 5.69 0 3.89 2.05 7.14 5.09 7.14 1.76 0 3.03-1.07 4.15-2.73 1.13 1.66 2.4 2.73 4.16 2.73 3.04 0 4.9-3.25 4.9-7.14zm-4.73 4.54c-1.39 0-2.42-1.28-3.33-2.82 1.09-1.85 2.1-3.2 3.25-3.2 1.34 0 2.21 1.48 2.21 3.52 0 1.96-.8 2.5-2.13 2.5zm-11.23 0c-1.33 0-2.13-.54-2.13-2.5 0-2.04.87-3.52 2.21-3.52 1.15 0 2.16 1.35 3.25 3.2-.91 1.54-1.94 2.82-3.33 2.82z"/></svg>
          <span>Meta</span>
        </div>"""

    if old_palantir in content:
        content = content.replace(old_palantir, new_meta)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Replaced Palantir with Meta in {path}")
    else:
        print(f"Warning: old_palantir not found in {path}")

print("Replacement complete!")
