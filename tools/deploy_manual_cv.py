"""
Deploy Manual Mode CV Upload and Real Match Probability Ranking.
"""

import os

BASE_DIR = r"C:\Claude Work\camoroles"

# 1. Update static/index.html
html_path = os.path.join(BASE_DIR, "static", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace manual-search-box with manual-search-container including Upload CV button & active banner
old_manual_box = """      <!-- Manual Keyword Search Bar (Shown when Manual Mode is active) -->
      <div class="chatgpt-search-box" id="manual-search-box" style="display:none;">
        <svg class="chatgpt-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" id="hero-search-input" class="chatgpt-search-input" placeholder="Search keywords: Game Dev, Product Design, SpaceTech, NVIDIA, Tesla..." oninput="onSearchInput(this.value)">
        <button class="search-clear-action" id="hero-search-clear" onclick="clearSearchInput()">&times;</button>
      </div>"""

new_manual_box = """      <!-- Manual Keyword Search Bar & CV Match in Manual Mode -->
      <div class="manual-search-container" id="manual-search-container" style="display:none;">
        <div class="chatgpt-search-box" id="manual-search-box">
          <svg class="chatgpt-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="hero-search-input" class="chatgpt-search-input" placeholder="Search keywords: Game Dev, Product Design, SpaceTech, NVIDIA, Tesla..." oninput="onSearchInput(this.value)">
          <button class="search-clear-action" id="hero-search-clear" onclick="clearSearchInput()">&times;</button>

          <!-- Upload CV Button in Manual Mode -->
          <button class="manual-cv-capsule-btn" id="manual-cv-capsule-btn" onclick="document.getElementById('manual-cv-file-input').click()" title="Attach CV for Instant Match Probability %">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
            <span id="manual-cv-capsule-text">Upload CV</span>
          </button>
          <input type="file" id="manual-cv-file-input" accept=".pdf" style="display:none;" onchange="onManualCvSelected(event)">
        </div>

        <!-- Active CV Match Status Banner in Manual Mode -->
        <div class="manual-cv-active-banner" id="manual-cv-active-banner" style="display:none;">
          <div class="manual-cv-banner-left">
            <span class="manual-cv-badge">CV MATCH ACTIVE</span>
            <span class="manual-cv-headline" id="manual-cv-headline">Senior Distributed Systems Engineer</span>
            <span class="manual-cv-sub" id="manual-cv-sub">Ranked by real match probability %</span>
          </div>
          <div class="manual-cv-banner-actions">
            <button class="manual-cv-action-link" onclick="document.getElementById('manual-cv-file-input').click()">Replace CV</button>
            <button class="manual-cv-action-link" onclick="clearManualCv()">Clear</button>
          </div>
        </div>
      </div>"""

if old_manual_box in html:
    html = html.replace(old_manual_box, new_manual_box)
    print("Replaced manual search box with container in index.html")
else:
    print("Warning: old_manual_box not found in index.html")

# Add Rail CV card at top of aside.filter-rail
old_rail_start = """    <aside class="filter-rail">
      <!-- Search Openings -->"""

new_rail_start = """    <aside class="filter-rail">
      <!-- Rail CV Upload / Match Status -->
      <div class="rail-section rail-cv-box-section">
        <div class="rail-section-header">
          <span class="rail-label">CV Match Probability</span>
          <span class="rail-link-clear" id="rail-clear-cv-link" onclick="clearManualCv()" style="display:none;">Clear</span>
        </div>
        <div class="rail-cv-card" id="rail-cv-card" onclick="document.getElementById('manual-cv-file-input').click()">
          <div class="rail-cv-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><polyline points="9 15 12 12 15 15"/></svg>
          </div>
          <div class="rail-cv-text">
            <div class="rail-cv-title" id="rail-cv-title-text">Upload Resume (PDF)</div>
            <div class="rail-cv-hint" id="rail-cv-hint-text">Rank jobs by probability %</div>
          </div>
        </div>
      </div>

      <!-- Search Openings -->"""

if old_rail_start in html:
    html = html.replace(old_rail_start, new_rail_start)
    print("Added rail CV upload card to filter rail in index.html")
else:
    print("Warning: old_rail_start not found in index.html")

# Clean stray emojis in disciplines
html = html.replace("<span> AI & Machine Learning</span>", "<span>AI & Machine Learning</span>")
html = html.replace("<span> Backend & Distributed</span>", "<span>Backend & Distributed</span>")
html = html.replace("<span> Robotics & Autonomy</span>", "<span>Robotics & Autonomy</span>")
html = html.replace("<span> Business, Finance & Ops</span>", "<span>Business, Finance & Ops</span>")
html = html.replace("<span> HR & People Ops</span>", "<span>HR & People Ops</span>")
html = html.replace("<span> Electrical & Hardware</span>", "<span>Electrical & Hardware</span>")
html = html.replace("<span>️ Civil & Construction</span>", "<span>Civil & Construction</span>")
html = html.replace("<span>️ Cloud, DevOps & SRE</span>", "<span>Cloud, DevOps & SRE</span>")
html = html.replace("<span> India (Blr/Hyd/Pune/NCR)</span>", "<span>India (Blr/Hyd/Pune/NCR)</span>")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)


# 2. Update static/styles.css
styles_path = os.path.join(BASE_DIR, "static", "styles.css")
with open(styles_path, "r", encoding="utf-8") as f:
    css = f.read()

manual_cv_css = """
/* MANUAL SEARCH MODE CV UPLOAD & ACTIVE BANNER */
.manual-search-container {
  display: none;
  width: 100%;
  flex-direction: column;
  gap: 8px;
}

.manual-cv-capsule-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(197, 160, 89, 0.12);
  border: 1px solid rgba(197, 160, 89, 0.3);
  color: #D8B26E;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  margin-right: 4px;
  transition: all 0.2s ease;
}

.manual-cv-capsule-btn:hover {
  background: rgba(197, 160, 89, 0.22);
  border-color: var(--gold);
}

.manual-cv-capsule-btn.cv-loaded {
  background: var(--gold);
  color: #0E0F12 !important;
  border-color: var(--gold);
}

[data-theme="light"] .manual-cv-capsule-btn {
  background: rgba(112, 26, 43, 0.08);
  border-color: rgba(112, 26, 43, 0.25);
  color: #701A2B;
}

[data-theme="light"] .manual-cv-capsule-btn:hover {
  background: rgba(112, 26, 43, 0.15);
  border-color: #701A2B;
}

[data-theme="light"] .manual-cv-capsule-btn.cv-loaded {
  background: #701A2B !important;
  color: #FFFFFF !important;
  border-color: #701A2B;
}

.manual-cv-active-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--gold-border);
  border-radius: 12px;
  padding: 8px 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  animation: fadeInDown 0.2s ease;
}

[data-theme="light"] .manual-cv-active-banner {
  border-color: rgba(112, 26, 43, 0.25);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
}

.manual-cv-banner-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-width: 0;
}

.manual-cv-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  background: rgba(197, 160, 89, 0.18);
  color: var(--gold);
  padding: 3px 8px;
  border-radius: 6px;
}

[data-theme="light"] .manual-cv-badge {
  background: rgba(112, 26, 43, 0.1);
  color: #701A2B;
}

.manual-cv-headline {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.manual-cv-sub {
  font-size: 12px;
  color: var(--muted);
}

.manual-cv-banner-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.manual-cv-action-link {
  background: transparent;
  border: none;
  font-size: 12px;
  color: var(--gold);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  padding: 2px 4px;
}

[data-theme="light"] .manual-cv-action-link {
  color: #701A2B;
}

.manual-cv-action-link:hover {
  filter: brightness(1.2);
}

/* RAIL CV SECTION */
.rail-cv-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--surface);
  border: 1px dashed var(--gold-border);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.rail-cv-card:hover {
  border-color: var(--gold);
  background: var(--surface-hover);
  transform: translateY(-1px);
}

.rail-cv-card.cv-loaded {
  border-style: solid;
  border-color: var(--gold);
  background: rgba(197, 160, 89, 0.06);
}

[data-theme="light"] .rail-cv-card {
  border-color: rgba(112, 26, 43, 0.25);
}

[data-theme="light"] .rail-cv-card:hover {
  border-color: #701A2B;
  background: rgba(112, 26, 43, 0.04);
}

[data-theme="light"] .rail-cv-card.cv-loaded {
  border-color: #701A2B;
  background: rgba(112, 26, 43, 0.06);
}

.rail-cv-icon {
  color: var(--gold);
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

[data-theme="light"] .rail-cv-icon {
  color: #701A2B;
}

.rail-cv-text {
  min-width: 0;
  flex: 1;
}

.rail-cv-title {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rail-cv-hint {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
"""

if ".manual-search-container" not in css:
    css += manual_cv_css
    with open(styles_path, "w", encoding="utf-8") as f:
        f.write(css)
    print("Added manual CV CSS to static/styles.css")


# 3. Update static/app.js
app_path = os.path.join(BASE_DIR, "static", "app.js")
with open(app_path, "r", encoding="utf-8") as f:
    app_js = f.read()

# Replace setSearchMode
old_set_search_mode = """function setSearchMode(mode) {
  searchMode = mode;
  const segAi = document.getElementById('seg-btn-ai');
  const segManual = document.getElementById('seg-btn-manual');
  const aiBar = document.getElementById('ai-agentic-search-bar');
  const aiPanel = document.getElementById('ai-chat-unfold-panel');
  const manualBox = document.getElementById('manual-search-box');
  const heroInput = document.getElementById('hero-search-input');

  if (segAi) segAi.classList.toggle('active', mode === 'ai');
  if (segManual) segManual.classList.toggle('active', mode === 'manual');

  if (mode === 'manual') {
    if (aiBar) aiBar.style.display = 'none';
    if (aiPanel) aiPanel.style.display = 'none';
    if (manualBox) manualBox.style.display = 'flex';
    if (heroInput) {
      setTimeout(() => heroInput.focus(), 100);
    }
  } else {
    if (aiBar) aiBar.style.display = 'flex';
    if (manualBox) manualBox.style.display = 'none';
    if (heroInput && heroInput.value) {
      heroInput.value = '';
      activeFilters.q = '';
      applyFiltersAndRender();
    }
    updateHeroChatCount();
  }
}"""

new_set_search_mode = """function setSearchMode(mode) {
  searchMode = mode;
  const segAi = document.getElementById('seg-btn-ai');
  const segManual = document.getElementById('seg-btn-manual');
  const aiBar = document.getElementById('ai-agentic-search-bar');
  const aiPanel = document.getElementById('ai-chat-unfold-panel');
  const manualContainer = document.getElementById('manual-search-container');
  const heroInput = document.getElementById('hero-search-input');

  if (segAi) segAi.classList.toggle('active', mode === 'ai');
  if (segManual) segManual.classList.toggle('active', mode === 'manual');

  if (mode === 'manual') {
    if (aiBar) aiBar.style.display = 'none';
    if (aiPanel) aiPanel.style.display = 'none';
    if (manualContainer) manualContainer.style.display = 'flex';
    if (heroInput) {
      setTimeout(() => heroInput.focus(), 100);
    }
  } else {
    if (aiBar) aiBar.style.display = 'flex';
    if (manualContainer) manualContainer.style.display = 'none';
    if (heroInput && heroInput.value) {
      heroInput.value = '';
      activeFilters.q = '';
      applyFiltersAndRender();
    }
    updateHeroChatCount();
  }
  syncManualCvUI();
}"""

if old_set_search_mode in app_js:
    app_js = app_js.replace(old_set_search_mode, new_set_search_mode)
    print("Patched setSearchMode in static/app.js")
else:
    print("Warning: old_set_search_mode not found in static/app.js")

# Append syncManualCvUI, onManualCvSelected, clearManualCv
manual_functions_js = """
// ==========================================================================
// MANUAL MODE CV MATCHING & PROBABILITY RANKING
// ==========================================================================
function syncManualCvUI() {
  const capsuleBtn = document.getElementById('manual-cv-capsule-btn');
  const capsuleText = document.getElementById('manual-cv-capsule-text');
  const banner = document.getElementById('manual-cv-active-banner');
  const bannerHeadline = document.getElementById('manual-cv-headline');
  const bannerSub = document.getElementById('manual-cv-sub');
  const railCard = document.getElementById('rail-cv-card');
  const railTitle = document.getElementById('rail-cv-title-text');
  const railHint = document.getElementById('rail-cv-hint-text');
  const railClear = document.getElementById('rail-clear-cv-link');

  if (currentProfileData && currentProfileData.headline) {
    const hl = currentProfileData.headline;
    const skills = (currentProfileData.skills || []).slice(0, 3).join(', ');
    const exp = currentProfileData.experienceText || (currentProfileData.experienceYears ? `${currentProfileData.experienceYears} yrs` : '');

    if (capsuleBtn) capsuleBtn.classList.add('cv-loaded');
    if (capsuleText) capsuleText.textContent = 'CV Active';

    if (banner) banner.style.display = 'flex';
    if (bannerHeadline) bannerHeadline.textContent = hl;
    if (bannerSub) bannerSub.textContent = `${exp}${exp && skills ? ' · ' : ''}${skills} · Ranked by probability %`;

    if (railCard) railCard.classList.add('cv-loaded');
    if (railTitle) railTitle.textContent = hl;
    if (railHint) railHint.textContent = `${skills || 'Core skills'} · Match % Active`;
    if (railClear) railClear.style.display = 'inline';
  } else {
    if (capsuleBtn) capsuleBtn.classList.remove('cv-loaded');
    if (capsuleText) capsuleText.textContent = 'Upload CV';

    if (banner) banner.style.display = 'none';

    if (railCard) railCard.classList.remove('cv-loaded');
    if (railTitle) railTitle.textContent = 'Upload Resume (PDF)';
    if (railHint) railHint.textContent = 'Rank jobs by probability %';
    if (railClear) railClear.style.display = 'none';
  }
}

async function onManualCvSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const capsuleText = document.getElementById('manual-cv-capsule-text');
  if (capsuleText) capsuleText.textContent = 'Extracting...';

  const railTitle = document.getElementById('rail-cv-title-text');
  if (railTitle) railTitle.textContent = 'Parsing CV...';

  let extractedText = '';
  try {
    extractedText = await extractTextFromPdfFile(file);
  } catch (e) {
    console.warn('Text extraction warning:', e);
  }

  if (capsuleText) capsuleText.textContent = 'Matching...';
  if (railTitle) railTitle.textContent = 'Scoring roles...';

  try {
    const res = await fetch(`${API_BASE}/cv/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cv_text: extractedText,
        file_name: file.name
      })
    });

    if (!res.ok) throw new Error("Failed to match CV");
    const data = await res.json();

    if (data.profile) {
      currentProfileData = data.profile;
      try {
        localStorage.setItem('camouroles_cv_profile', JSON.stringify(data.profile));
      } catch (e) {}
    }

    if (data.matches) {
      jobMatchesMap = data.matches;
      try {
        localStorage.setItem('camouroles_cv_matches', JSON.stringify(data.matches));
      } catch (e) {}
    }

    syncManualCvUI();
    syncChatGptCvUI(currentProfileData);
    syncProfileDataToUI(currentProfileData);
    updateHeroCvStatusUI(currentProfileData);

    // Default to match_desc sort to display highest probability % first
    currentSortMode = 'match_desc';
    applyFiltersAndRender();

    const count = Object.keys(jobMatchesMap).length || allJobsList.length;
    const countEl = document.getElementById('feed-count');
    if (countEl) countEl.textContent = `${count.toLocaleString()} roles · Ranked by CV Match Probability %`;

    // Smoothly scroll to the feed so the candidate sees their match percentages immediately
    const container = document.getElementById('job-rows-container');
    if (container) {
      container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  } catch (err) {
    console.error("Manual CV match error:", err);
    if (capsuleText) capsuleText.textContent = 'Upload Failed';
    if (railTitle) railTitle.textContent = 'Upload Failed (use PDF)';
    setTimeout(() => syncManualCvUI(), 3000);
  }
}

function clearManualCv() {
  currentProfileData = null;
  jobMatchesMap = {};
  try {
    localStorage.removeItem('camouroles_cv_profile');
    localStorage.removeItem('camouroles_cv_matches');
  } catch (e) {}
  syncManualCvUI();
  syncChatGptCvUI(null);
  syncProfileDataToUI(null);
  updateHeroCvStatusUI(null);
  applyFiltersAndRender();
}

window.onManualCvSelected = onManualCvSelected;
window.clearManualCv = clearManualCv;
window.syncManualCvUI = syncManualCvUI;
"""

if "function syncManualCvUI()" not in app_js:
    app_js += manual_functions_js
    print("Added manual CV functions to static/app.js")

# In loadProfileData, call syncManualCvUI as well
app_js = app_js.replace("syncProfileDataToUI(currentProfileData);", "syncProfileDataToUI(currentProfileData); syncManualCvUI();")
app_js = app_js.replace("syncProfileDataToUI(null);", "syncProfileDataToUI(null); syncManualCvUI();")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_js)

print("Manual CV mode integration complete!")
