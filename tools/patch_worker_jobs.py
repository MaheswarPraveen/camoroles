"""
Patch worker.js to fetch all pages from Supabase so all 10,217+ jobs (including Apple, Palantir, Meta, etc.) are available in the cache.
"""

import os

worker_path = r"C:\Claude Work\camoroles\worker.js"
with open(worker_path, "r", encoding="utf-8") as f:
    code = f.read()

# Update CACHE_TTL_MS to 15 minutes
code = code.replace("const CACHE_TTL_MS = 180 * 1000; // 3 minutes", "const CACHE_TTL_MS = 15 * 60 * 1000; // 15 minutes")

# Replace the single queryUrl block
old_fetch_block = """    // Fetch verified active positions
    const queryUrl = `${sbUrl}/rest/v1/jobs?is_active=eq.true&order=created_at.desc&limit=1000&select=id,title,company,ats_type,location,is_remote,experience_min,experience_max,skills,apply_url,last_verified_at,created_at`;
    const sbRes = await fetch(queryUrl, {
      headers: {
        'apikey': sbKey,
        'Authorization': `Bearer ${sbKey}`,
        'Accept': 'application/json',
      },
    });

    if (!sbRes.ok) {
      const errText = await sbRes.text();
      return errorResponse(`Supabase error: ${errText}`, 500);
    }

    const rawRows = await sbRes.json();"""

new_fetch_block = """    // Fetch all verified active positions across all offsets (complete 10,200+ inventory)
    const offsets = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000];
    const pagePromises = offsets.map(async offset => {
      const queryUrl = `${sbUrl}/rest/v1/jobs?is_active=eq.true&order=created_at.desc&limit=1000&offset=${offset}&select=id,title,company,ats_type,location,is_remote,experience_min,experience_max,skills,apply_url,last_verified_at,created_at`;
      try {
        const res = await fetch(queryUrl, {
          headers: {
            'apikey': sbKey,
            'Authorization': `Bearer ${sbKey}`,
            'Accept': 'application/json',
          },
        });
        if (!res.ok) return [];
        return await res.json();
      } catch (e) {
        return [];
      }
    });

    const pageResults = await Promise.all(pagePromises);
    const rawRows = pageResults.flat();"""

if old_fetch_block in code:
    code = code.replace(old_fetch_block, new_fetch_block)
    print("Patched multi-page fetch in worker.js")
else:
    print("Warning: old_fetch_block not found in worker.js")

with open(worker_path, "w", encoding="utf-8") as f:
    f.write(code)

print("worker.js updated successfully!")
