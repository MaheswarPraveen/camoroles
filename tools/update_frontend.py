import os
import sys

APP_JS = r"C:\Claude Work\camoroles\static\app.js"
with open(APP_JS, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Strip remaining emojis
content = content.replace("★ Synced", "Synced")
content = content.replace("'✨ Active'", "'Active'")
content = content.replace("'✨ Chat'", "'Chat'")
content = content.replace("<p>📄 <strong>Uploaded CV:</strong>", "<p><strong>Uploaded CV:</strong>")

# 2. Add matchesSearchQuery function before applyFiltersAndRender
search_func = """// High-Precision Tokenized Search Across All Fields (Title, Company, Skills, Description, Location, Discipline, Portal)
function matchesSearchQuery(job, query) {
  if (!query || !query.trim()) return true;
  const qClean = query.trim().toLowerCase();
  const tokens = qClean.split(/[\s,+/|]+/).filter(Boolean);
  if (!tokens.length) return true;

  const title = (job.title || '').toLowerCase();
  const company = (job.company || '').toLowerCase();
  const desc = (job.description || '').toLowerCase();
  const loc = (job.location || '').toLowerCase();
  const discipline = (job.discipline || '').toLowerCase();
  const portal = (job.portal || job.ats_type || '').toLowerCase();
  const skills = Array.isArray(job.skills) ? job.skills.join(' ').toLowerCase() : String(job.skills || '').toLowerCase();

  // Instant substring match across any core field
  if (title.includes(qClean) || company.includes(qClean) || skills.includes(qClean) || loc.includes(qClean) || desc.includes(qClean)) {
    return true;
  }

  // Composite search corpus
  const fullText = `${title} ${company} ${discipline} ${skills} ${loc} ${portal} ${desc}`;
  return tokens.every(token => fullText.includes(token));
}

// Batch rendering to avoid overwhelming the DOM and maintain natural scroll velocity"""

if "// High-Precision Tokenized Search" not in content:
    content = content.replace("// Batch rendering to avoid overwhelming the DOM and maintain natural scroll velocity", search_func)

# 3. Update applyFiltersAndRender search filtering
old_filter = """  // 1. Keyword Search
  if (activeFilters.q) {
    const qLower = activeFilters.q.toLowerCase();
    filtered = filtered.filter(j => {
      const titleMatch = (j.title || '').toLowerCase().includes(qLower);
      const compMatch = (j.company || '').toLowerCase().includes(qLower);
      const skillMatch = (j.skills || []).some(s => s.toLowerCase().includes(qLower));
      return titleMatch || compMatch || skillMatch;
    });
  }"""

new_filter = """  // 1. Keyword Search (Deep Tokenized Multi-Field Search)
  if (activeFilters.q) {
    filtered = filtered.filter(j => matchesSearchQuery(j, activeFilters.q));
  }"""

if old_filter in content:
    content = content.replace(old_filter, new_filter)
    print("Replaced filter logic successfully")
else:
    print("Warning: old_filter not found directly")

# 4. Update updateHeroChatCount matching logic
old_hero_q = """    if (heroChatCriteria.keywords) {
      const q = heroChatCriteria.keywords.toLowerCase();
      const title = (j.title || '').toLowerCase();
      const comp = (j.company || '').toLowerCase();
      const skills = (j.skills || []).map(s => String(s).toLowerCase());
      if (!title.includes(q) && !comp.includes(q) && !skills.some(s => s.includes(q))) continue;
    }"""

new_hero_q = """    if (heroChatCriteria.keywords) {
      if (!matchesSearchQuery(j, heroChatCriteria.keywords)) continue;
    }"""

if old_hero_q in content:
    content = content.replace(old_hero_q, new_hero_q)
    print("Replaced hero chat count logic successfully")
else:
    print("Warning: old_hero_q not found")

# 5. Replace renderCompanyVectorLogo with Authentic Vector SVGs + Corporate Monogram Pills
logo_start = "// Render Authentic Vector Brand Logos for Companies (Original Full Colors)\nfunction renderCompanyVectorLogo(company, portal) {"
logo_end = "function renderPortalSvg(portal) {"

new_logo_func = """// Helper to produce clean corporate monogram
function getCompanyMonogram(name) {
  if (!name) return 'CO';
  const clean = name.replace(/[^a-zA-Z0-9\\s]/g, '').trim();
  const words = clean.split(/\\s+/).filter(Boolean);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase() || 'CO';
}

function getCompanyBadgeColor(name) {
  const palette = [
    '#1E3A8A', '#1E40AF', '#1D4ED8', '#0F766E', '#047857',
    '#312E81', '#3730A3', '#4338CA', '#0369A1', '#0E7490',
    '#334155', '#1F2937', '#111827', '#1E293B', '#2563EB'
  ];
  let hash = 0;
  for (let i = 0; i < (name || '').length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) & 0xffffffff;
  }
  return palette[Math.abs(hash) % palette.length];
}

// Render Authentic Vector Brand Logos for Tech Giants & Crisp Typography Pills for Enterprise
function renderCompanyVectorLogo(company, portal) {
  const c = String(company || '').toLowerCase().trim();
  const p = String(portal || '').toLowerCase().trim();

  // 1. Tesla
  if (c.includes('tesla')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 340 340" fill="#E82127"><path d="M170 36.8c38.7 0 74 13.5 101.9 36.2l18.4-32C256.4 15.6 215.1 0 170 0 124.9 0 83.6 15.6 49.7 41l18.4 32C96 50.3 131.3 36.8 170 36.8zm-82.7 54.3l-26-8.5c-9.6 28.5-14.8 59-14.8 90.7 0 46.9 11.2 91.2 31 130.7l27.1-12.7c-17.2-35.3-26.9-74.8-26.9-116.5 0-28.7 4.7-56.3 13.6-82.2zm165.4 0c8.9 25.9 13.6 53.5 13.6 82.2 0 41.7-9.7 81.2-26.9 116.5l27.1 12.7c19.8-39.5 31-83.8 31-130.7 0-31.7-5.2-62.2-14.8-90.7l-26 8.5zM170 82.5c-30.8 0-58.8 11.7-80 30.9l17.7 20.3c16.3-14.7 38.1-23.7 62.3-23.7s46 9 62.3 23.7l17.7-20.3c-21.2-19.2-49.2-30.9-80-30.9zm0 54.7c-16.1 0-29.1 13.1-29.1 29.1v173.7h58.3V166.3c-.1-16-13.1-29.1-29.2-29.1z"/></svg>`;
  }

  // 2. NVIDIA
  if (c.includes('nvidia')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="#76B900"><path d="M8.9 7.6c1.6-1.2 3.6-1.7 5.7-1.5 2.1.2 4 1.1 5.3 2.6 1.2 1.4 1.8 3.2 1.8 5.1 0 1.9-.7 3.7-1.9 5.1-1.3 1.5-3.1 2.4-5.2 2.6-2.1.2-4.1-.4-5.7-1.6-.3-.2-.5-.6-.5-1s.3-.8.7-.9c.4-.1.8 0 1 .3 1.3.9 2.8 1.4 4.4 1.3 1.6-.1 3-.8 4.1-1.9 1-1.1 1.5-2.5 1.5-4 0-1.5-.5-2.9-1.5-4-1-1.1-2.4-1.8-4-1.9-1.6-.1-3.1.3-4.4 1.3-.3.2-.8.2-1.1 0-.3-.2-.4-.6-.3-1 .1-.2.2-.3.3-.4zm-3 2.4c2.3-1.8 5.2-2.6 8.2-2.3 3 .3 5.7 1.7 7.6 3.9 1.8 2.1 2.7 4.9 2.7 7.7 0 2.8-1 5.5-2.8 7.7-1.9 2.2-4.6 3.6-7.6 3.9-3 .3-5.9-.5-8.2-2.4-.4-.3-.6-.7-.5-1.2.1-.5.5-.8 1-.8.4 0 .8.2 1 .4 1.9 1.6 4.3 2.2 6.8 2 2.4-.2 4.6-1.4 6.2-3.1 1.5-1.8 2.3-4 2.3-6.4 0-2.3-.8-4.6-2.3-6.4-1.5-1.8-3.7-3-6.1-3.2-2.5-.2-4.9.4-6.8 2-.4.3-.9.3-1.2 0-.4-.2-.5-.7-.4-1.2.1-.2.2-.4.4-.5zm-3.6 2.8c3.2-2.5 7.1-3.6 11.2-3.1 4 .4 7.7 2.3 10.3 5.3 2.5 2.9 3.7 6.6 3.7 10.5s-1.3 7.5-3.8 10.4c-2.6 3-6.3 4.9-10.3 5.3-4.1.4-8.1-.7-11.2-3.2-.4-.3-.6-.8-.5-1.3.1-.5.6-.9 1.1-.8.4.1.8.3 1.1.5 2.7 2.1 6.1 3 9.6 2.7 3.4-.4 6.6-2 8.8-4.5 2.1-2.5 3.2-5.7 3.2-9.1s-1.1-6.5-3.2-9c-2.2-2.6-5.3-4.2-8.8-4.5-3.5-.3-6.9.6-9.6 2.7-.4.3-1 .3-1.3-.1-.3-.4-.3-1 0-1.4.1-.1.3-.3.4-.4z"/></svg>`;
  }

  // 3. Apple
  if (c.includes('apple')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.62-.75 1.04-1.8 0.92-2.85-.9.04-1.99.6-2.63 1.35-.56.65-.96 1.71-.83 2.73 1.01.08 2.02-.48 2.54-1.23z"/></svg>`;
  }

  // 4. Microsoft
  if (c.includes('microsoft')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24"><rect x="1" y="1" width="10" height="10" fill="#F25022"/><rect x="13" y="1" width="10" height="10" fill="#7FBA00"/><rect x="1" y="13" width="10" height="10" fill="#00A4EF"/><rect x="13" y="13" width="10" height="10" fill="#FFB900"/></svg>`;
  }

  // 5. Google / Alphabet / Waymo
  if (c.includes('google') || c.includes('alphabet') || c.includes('waymo')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>`;
  }

  // 6. Amazon / AWS
  if (c.includes('amazon') || c.includes('aws') || c.includes('adci') || p.includes('amazon')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="none"><path fill="#FF9900" d="M17.6 15.6c-.3.4-1.2 1-1.9 1.2-.2 0-.2.3 0 .4.8.4 2.1.3 2.6-.2.5-.5.2-1.8-.3-2.4-.2-.2-.4 0-.4.2.1.3.1.8 0 .8z"/><path fill="#FF9900" d="M3.2 17.8C7.8 20.8 14 20 18.3 16.9c.3-.2.2-.6-.2-.4-4 2.6-9.7 3.1-14.3-.2-.4-.3-.6.1-.2.5z"/><path fill="currentColor" d="M14.2 12.1c-.6 0-1.2.2-1.6.5-.4.3-.6.8-.6 1.3 0 .5.2.9.5 1.2.3.3.8.4 1.4.4.8 0 1.4-.3 1.8-.8.4-.5.6-1.2.6-2v-.6h-2.1zm3.8 3.9c-.2.2-.5.3-.8.3-.3 0-.5-.1-.7-.3l-.2-.4c-.5.4-1.1.7-1.7.9-.6.2-1.2.2-1.9.2-1 0-1.8-.3-2.4-.8-.6-.5-.9-1.3-.9-2.3 0-1 .4-1.8 1.1-2.4.7-.6 1.7-.9 3-.9h1.7v-.7c0-.7-.2-1.2-.5-1.6-.3-.4-.9-.5-1.6-.5-.7 0-1.4.2-1.8.6-.4.4-.6 1-.7 1.8l-1.9-.2c.2-1.1.7-1.9 1.4-2.5.7-.6 1.8-.9 3.2-.9 1.3 0 2.3.3 3 1 .7.6 1.1 1.6 1.1 2.8v4.5c0 .6.1 1.1.4 1.3l-1.4.2z"/></svg>`;
  }

  // 7. Meta / Facebook
  if (c.includes('meta') || c.includes('facebook')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="#0081FB"><path d="M12 2C6.48 2 2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V14.9H7.5V12H10V9.8c0-2.48 1.48-3.85 3.74-3.85 1.08 0 2.22.19 2.22.19v2.44h-1.25c-1.23 0-1.61.76-1.61 1.54V12h2.74l-.44 2.9H13.1v6.9c4.56-.93 8-4.96 8-9.8 0-5.52-4.48-10-10-10z"/></svg>`;
  }

  // 8. Stripe
  if (c.includes('stripe')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="#635BFF"><path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.96 15.688.5 12.522.5 6.782.5 2.68 3.518 2.68 8.622c0 5.493 5.494 6.72 8.444 7.825 2.502.936 3.376 1.696 3.376 2.736 0 1.056-.994 1.58-2.409 1.58-2.673 0-5.617-1.196-7.382-2.138l-.946 5.568C5.234 24.89 8.358 25.5 12.032 25.5c6.048 0 10.368-2.912 10.368-8.22 0-5.836-5.712-7.078-8.424-8.13z"/></svg>`;
  }

  // 9. Cloudflare
  if (c.includes('cloudflare')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="#F38020"><path d="M18.2 8.7c-.5-2.7-2.8-4.7-5.6-4.7-2.4 0-4.4 1.5-5.3 3.6C6.7 7.8 6.1 8 5.6 8.4 4 9.6 3 11.4 3 13.5c0 3 2.5 5.5 5.5 5.5h10c2.5 0 4.5-2 4.5-4.5 0-2.3-1.7-4.1-3.9-4.4-.3-.5-.6-.9-.9-1.4z"/></svg>`;
  }

  // 10. Palantir
  if (c.includes('palantir')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><circle cx="12" cy="12" r="3.5"/></svg>`;
  }

  // 11. OpenAI
  if (c.includes('openai')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="#10A37F"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="3"/></svg>`;
  }

  // 12. Anthropic
  if (c.includes('anthropic')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="#CC785C"><path d="M14.5 3L22 19h-3.8l-1.6-3.7H7.4L5.8 19H2L9.5 3h5zm-2.5 5.2L9.1 13h5.8L12 8.2z"/></svg>`;
  }

  // 13. Spotify
  if (c.includes('spotify')) {
    return `<svg class="company-brand-icon" width="16" height="16" viewBox="0 0 24 24" fill="#1DB954"><circle cx="12" cy="12" r="10"/><path d="M7 9c3-1 7-1 10 1M7.5 12c2.5-.8 5.8-.7 8.2.8M8 15c2-.5 4.5-.4 6.5.7" stroke="#fff" stroke-width="1.3" fill="none"/></svg>`;
  }

  // 14. Y Combinator
  if (p.includes('ycombinator') || c.includes('yc') || c.includes('y combinator')) {
    return `<span class="company-monogram-pill" style="background:#FF6600; color:#FFFFFF;">Y</span>`;
  }

  // 15. Financial & Enterprise Giants (Clean Monogram Badges)
  if (c.includes('goldman')) {
    return `<span class="company-monogram-pill" style="background:#1E3A8A; color:#FFFFFF;">GS</span>`;
  }
  if (c.includes('ey ') || c === 'ey' || c.includes('ernst')) {
    return `<span class="company-monogram-pill" style="background:#2E2E38; color:#FFE600;">EY</span>`;
  }
  if (c.includes('infosys')) {
    return `<span class="company-monogram-pill" style="background:#007CC3; color:#FFFFFF;">INF</span>`;
  }
  if (c.includes('jpmorgan') || c.includes('chase')) {
    return `<span class="company-monogram-pill" style="background:#11365F; color:#FFFFFF;">JPM</span>`;
  }
  if (c.includes('mckinsey')) {
    return `<span class="company-monogram-pill" style="background:#051C2C; color:#FFFFFF;">MCK</span>`;
  }
  if (c.includes('bcg') || c.includes('boston consulting')) {
    return `<span class="company-monogram-pill" style="background:#005A36; color:#FFFFFF;">BCG</span>`;
  }
  if (c.includes('deloitte')) {
    return `<span class="company-monogram-pill" style="background:#000000; color:#86BC25;">D.</span>`;
  }
  if (c.includes('morgan stanley')) {
    return `<span class="company-monogram-pill" style="background:#002C6C; color:#FFFFFF;">MS</span>`;
  }

  // Clean Typography Monogram Pill for all other verified companies
  const monogram = getCompanyMonogram(company);
  const bgColor = getCompanyBadgeColor(company);
  return `<span class="company-monogram-pill" style="background:${bgColor}; color:#FFFFFF;">${escapeHtml(monogram)}</span>`;
}

"""

if logo_start in content and logo_end in content:
    idx1 = content.find(logo_start)
    idx2 = content.find(logo_end)
    content = content[:idx1] + new_logo_func + content[idx2:]
    print("Replaced renderCompanyVectorLogo successfully")
else:
    print("Warning: logo block not found")

with open(APP_JS, "w", encoding="utf-8") as f:
    f.write(content)

# Also synchronize to web/app.js
WEB_APP_JS = r"C:\Claude Work\camoroles\web\app.js"
if os.path.exists(WEB_APP_JS):
    with open(WEB_APP_JS, "w", encoding="utf-8") as f:
        f.write(content)
    print("Synchronized to web/app.js")

print("All frontend updates applied successfully.")
