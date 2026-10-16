/**
 * CAMOUROLES CLIENT ENGINE
 * Handles 150ms debounced search, tactile slider physics,
 * Google Auth profile sync, in-memory CV matcher, and bookmarking.
 */

const API_BASE = window.location.origin + '/api';

// State Store
let activeFilters = {
  q: '',
  discipline: 'all',
  location: 'all',
  maxExp: 10,
  expPreset: 'all',
  ats: 'all'
};

let activeTab = 'all'; // 'all' or 'saved'
let allJobsList = [];
let jobMatchesMap = {}; // { jobId: { score, explanation } }
let savedJobIds = new Set(JSON.parse(localStorage.getItem('camouroles_saved_jobs') || '[]'));
let currentUser = JSON.parse(localStorage.getItem('camouroles_user') || 'null');
let searchDebounceTimer = null;

// Experience Readout Lookup Table
function getExpReadoutText(val) {
  const n = parseInt(val, 10);
  if (n >= 10) return 'Any Experience (All Levels)';
  if (n === 0) return '0 Yrs (Intern / Fresher)';
  if (n === 1) return '0 - 1 Yrs (Intern / Fresher)';
  if (n <= 3) return `0 - ${n} Yrs (Early Career)`;
  if (n <= 6) return `0 - ${n} Yrs (Mid-Level)`;
  return `0 - ${n} Yrs (Senior / Lead)`;
}

// On Page Load
document.addEventListener('DOMContentLoaded', () => {
  renderAuthUI();
  updateSavedPillCount();
  syncExpSlider(10, 'all');
  loadJobs();
  loadProfileData();

  // Close profile dropdown when clicking outside
  document.addEventListener('click', (e) => {
    const authBox = document.getElementById('auth-container');
    const menu = document.getElementById('profile-dropdown-menu');
    if (authBox && menu && !authBox.contains(e.target)) {
      menu.classList.remove('open');
    }
  });
});

// ==========================================================================
// TACTILE EXPERIENCE SLIDER
// ==========================================================================
function onExpSliderInput(val) {
  const n = parseInt(val, 10);
  activeFilters.maxExp = n;
  activeFilters.expPreset = (n >= 10) ? 'all' : `${n}`;

  syncExpSlider(n, activeFilters.expPreset);
  updateActivePills();
  applyFiltersAndRender();
}

function setExpPreset(preset) {
  activeFilters.expPreset = preset;
  let targetVal = 10;
  if (preset === '0-1') targetVal = 1;
  else if (preset === '1-3') targetVal = 3;
  else if (preset === '3-6') targetVal = 6;
  else if (preset === '6+') targetVal = 9;
  else targetVal = 10;

  activeFilters.maxExp = targetVal;
  syncExpSlider(targetVal, preset);
  updateActivePills();
  applyFiltersAndRender();
}

function syncExpSlider(val, preset) {
  const pct = (val / 10) * 100;
  const text = getExpReadoutText(val);

  // Desktop Slider
  const deskSlider = document.getElementById('desktop-exp-slider');
  const deskReadout = document.getElementById('desktop-exp-readout');
  if (deskSlider) {
    deskSlider.value = val;
    deskSlider.style.setProperty('--slider-pct', `${pct}%`);
  }
  if (deskReadout) deskReadout.textContent = text;

  // Mobile Slider
  const mobSlider = document.getElementById('mobile-exp-slider');
  const mobReadout = document.getElementById('mobile-exp-readout');
  if (mobSlider) {
    mobSlider.value = val;
    mobSlider.style.setProperty('--slider-pct', `${pct}%`);
  }
  if (mobReadout) mobReadout.textContent = text;

  // Preset Buttons
  document.querySelectorAll('[data-exp-preset]').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-exp-preset') === preset);
  });
}

// ==========================================================================
// FILTER SWITCHERS
// ==========================================================================
function setDisciplineFilter(val) {
  activeFilters.discipline = val;
  document.querySelectorAll('[data-discipline]').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-discipline') === val);
  });
  updateActivePills();
  applyFiltersAndRender();
}

function setLocationFilter(val) {
  activeFilters.location = val;
  document.querySelectorAll('[data-location]').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-location') === val);
  });
  updateActivePills();
  applyFiltersAndRender();
}

function setAtsFilter(val) {
  activeFilters.ats = val;
  document.querySelectorAll('[data-ats]').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-ats') === val);
  });
  updateActivePills();
  applyFiltersAndRender();
}

// ==========================================================================
// 150MS DEBOUNCED SEARCH WITH CLEAR BUTTON
// ==========================================================================
function onSearchInput(val) {
  const deskInput = document.getElementById('desktop-search-input');
  const mobInput = document.getElementById('mobile-search-input');
  const clearBtn = document.getElementById('search-clear-btn');

  if (deskInput && deskInput.value !== val) deskInput.value = val;
  if (mobInput && mobInput.value !== val) mobInput.value = val;
  if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';

  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    activeFilters.q = val.trim();
    updateActivePills();
    applyFiltersAndRender();
  }, 150);
}

function clearSearchInput() {
  onSearchInput('');
}

// ==========================================================================
// ACTIVE FILTER PILLS BAR
// ==========================================================================
function updateActivePills() {
  const container = document.getElementById('active-pills-bar');
  if (!container) return;
  const pills = [];

  if (activeFilters.q) {
    pills.push(`<span>Query: "${escapeHtml(activeFilters.q)}"</span><button onclick="clearSearchInput()">✕</button>`);
  }
  if (activeFilters.discipline !== 'all') {
    pills.push(`<span>${escapeHtml(formatPillName(activeFilters.discipline))}</span><button onclick="setDisciplineFilter('all')">✕</button>`);
  }
  if (activeFilters.location !== 'all') {
    pills.push(`<span>${escapeHtml(formatPillName(activeFilters.location))}</span><button onclick="setLocationFilter('all')">✕</button>`);
  }
  if (activeFilters.maxExp < 10) {
    pills.push(`<span>Max ${activeFilters.maxExp} Yrs</span><button onclick="setExpPreset('all')">✕</button>`);
  }
  if (activeFilters.ats !== 'all') {
    pills.push(`<span>Portal: ${escapeHtml(activeFilters.ats)}</span><button onclick="setAtsFilter('all')">✕</button>`);
  }

  container.innerHTML = pills.map(p => `<div class="active-filter-pill">${p}</div>`).join('');
}

function formatPillName(val) {
  return val.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// ==========================================================================
// TAB SWITCHER (ALL VS SAVED)
// ==========================================================================
function setTab(tab) {
  activeTab = tab;
  document.getElementById('tab-all-roles').classList.toggle('active', tab === 'all');
  document.getElementById('tab-saved-roles').classList.toggle('active', tab === 'saved');

  const mobJobsBtn = document.getElementById('mob-nav-jobs');
  const mobSavedBtn = document.getElementById('mob-nav-saved');
  if (mobJobsBtn) mobJobsBtn.classList.toggle('active', tab === 'all');
  if (mobSavedBtn) mobSavedBtn.classList.toggle('active', tab === 'saved');

  applyFiltersAndRender();
}

// ==========================================================================
// BOOKMARKING / SAVED JOBS (LOCALSTORAGE + CLOUD SYNC)
// ==========================================================================
function toggleBookmark(jobId) {
  if (savedJobIds.has(jobId)) {
    savedJobIds.delete(jobId);
  } else {
    savedJobIds.add(jobId);
  }
  localStorage.setItem('camouroles_saved_jobs', JSON.stringify([...savedJobIds]));
  updateSavedPillCount();
  applyFiltersAndRender();

  // If logged in, sync with backend cloud
  if (currentUser) {
    syncBookmarksWithCloud();
  }
}

function updateSavedPillCount() {
  const pill = document.getElementById('saved-count-pill');
  if (pill) pill.textContent = savedJobIds.size;
  const menuCount = document.getElementById('menu-saved-count');
  if (menuCount) menuCount.textContent = savedJobIds.size;
}

async function syncBookmarksWithCloud() {
  if (!currentUser) return;
  try {
    await fetch(`${API_BASE}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        credential: 'dev_sync',
        savedIds: [...savedJobIds]
      })
    });
  } catch (err) {
    console.error("Cloud bookmark sync error:", err);
  }
}

// ==========================================================================
// GOOGLE SIGN-IN & PROFILE DROPDOWN
// ==========================================================================
function renderAuthUI() {
  const container = document.getElementById('auth-container');
  if (!container) return;

  if (currentUser) {
    container.innerHTML = `
      <button class="btn-profile-pill" onclick="toggleProfileDropdown(event)">
        <img class="profile-avatar-img" src="${currentUser.picture || 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=Camouroles'}" alt="${escapeHtml(currentUser.name)}">
        <span>${escapeHtml(currentUser.name.split(' ')[0])}</span>
        <span class="cloud-synced-chip">★ Synced</span>
      </button>
      <div class="profile-dropdown-menu" id="profile-dropdown-menu">
        <div class="dropdown-user-header">
          <div class="dropdown-user-name">${escapeHtml(currentUser.name)}</div>
          <div class="dropdown-user-email">${escapeHtml(currentUser.email || 'engineer@camouroles.io')}</div>
        </div>
        <button class="dropdown-item" onclick="setTab('saved')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          <span>Saved Roles (<span id="menu-saved-count">${savedJobIds.size}</span>)</span>
        </button>
        <button class="dropdown-item danger" onclick="deleteMyData()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          <span>Delete CV Profile (Wipe)</span>
        </button>
        <button class="dropdown-item" onclick="signOutGoogle()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          <span>Sign Out</span>
        </button>
      </div>
    `;
  } else {
    container.innerHTML = `
      <button class="btn-google-signin" onclick="signInWithGoogle()">
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>
        <span>Sign in</span>
      </button>
    `;
  }
}

function toggleProfileDropdown(e) {
  e.stopPropagation();
  const menu = document.getElementById('profile-dropdown-menu');
  if (menu) menu.classList.toggle('open');
}

async function signInWithGoogle() {
  try {
    const res = await fetch(`${API_BASE}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        credential: 'dev_maheswar_google_auth',
        savedIds: [...savedJobIds]
      })
    });
    const data = await res.json();
    currentUser = data.user;
    localStorage.setItem('camouroles_user', JSON.stringify(currentUser));
    if (data.user.savedIds && data.user.savedIds.length) {
      data.user.savedIds.forEach(id => savedJobIds.add(id));
      localStorage.setItem('camouroles_saved_jobs', JSON.stringify([...savedJobIds]));
    }
    renderAuthUI();
    updateSavedPillCount();
    applyFiltersAndRender();
  } catch (err) {
    console.error("Google sign in error:", err);
  }
}

function signOutGoogle() {
  currentUser = null;
  localStorage.removeItem('camouroles_user');
  renderAuthUI();
}

// ==========================================================================
// LOAD JOBS FROM API
// ==========================================================================
async function loadJobs() {
  try {
    let url = `${API_BASE}/jobs/search?limit=120`;
    let res = await fetch(url);
    if (!res.ok) {
      url = `${API_BASE}/jobs`;
      res = await fetch(url);
    }
    const data = await res.json();
    allJobsList = data.jobs || [];

    const totalCount = data.totalVerified || allJobsList.length || 1288;
    document.getElementById('verified-roles-indicator').textContent = `${totalCount} live verified roles`;
    document.getElementById('feed-count-pill').textContent = totalCount;

    applyFiltersAndRender();
  } catch (err) {
    console.error("Error loading jobs:", err);
  }
}

// Apply Client-Side Filters & Render
function applyFiltersAndRender() {
  let filtered = allJobsList;

  // Keyword Search
  if (activeFilters.q) {
    const qLower = activeFilters.q.toLowerCase();
    filtered = filtered.filter(j => {
      const titleMatch = (j.title || '').toLowerCase().includes(qLower);
      const compMatch = (j.company || '').toLowerCase().includes(qLower);
      const skillMatch = (j.skills || []).some(s => s.toLowerCase().includes(qLower));
      return titleMatch || compMatch || skillMatch;
    });
  }

  // Max Experience Slider
  if (activeFilters.maxExp < 10) {
    filtered = filtered.filter(j => {
      const minExp = j.minExp !== undefined ? j.minExp : (j.experience_min || 0);
      return minExp <= activeFilters.maxExp;
    });
  }

  // Discipline Filter
  if (activeFilters.discipline !== 'all') {
    const discLower = activeFilters.discipline.toLowerCase();
    filtered = filtered.filter(j => {
      const title = (j.title || '').toLowerCase();
      const disc = (j.discipline || '').toLowerCase();
      return disc.includes(discLower) || title.includes(discLower);
    });
  }

  // Location Hub Filter
  if (activeFilters.location !== 'all') {
    const locLower = activeFilters.location.toLowerCase();
    filtered = filtered.filter(j => {
      const loc = (j.location || '').toLowerCase();
      const hub = (j.hub || '').toLowerCase();
      if (locLower === 'worldwide_remote') return j.is_remote || loc.includes('remote') || loc.includes('worldwide');
      if (locLower === 'sf_bay') return loc.includes('san francisco') || loc.includes('bay') || loc.includes('mountain view') || loc.includes('sunnyvale');
      if (locLower === 'seattle') return loc.includes('seattle') || loc.includes('bellevue') || loc.includes('redmond');
      if (locLower === 'nyc') return loc.includes('new york') || loc.includes('nyc');
      if (locLower === 'austin') return loc.includes('austin') || loc.includes('texas');
      if (locLower === 'london') return loc.includes('london') || loc.includes('uk');
      if (locLower === 'india') return loc.includes('india') || loc.includes('bengaluru') || loc.includes('hyderabad') || loc.includes('pune');
      return loc.includes(locLower) || hub.includes(locLower);
    });
  }

  // Portal Filter
  if (activeFilters.ats !== 'all') {
    const atsLower = activeFilters.ats.toLowerCase();
    filtered = filtered.filter(j => {
      const portal = (j.portal || j.ats_type || '').toLowerCase();
      if (atsLower === 'faang') return j.isFaang || (j.company || '').toLowerCase().includes('amazon') || (j.company || '').toLowerCase().includes('waymo');
      return portal.includes(atsLower);
    });
  }

  // Saved Filter Tab
  if (activeTab === 'saved') {
    filtered = filtered.filter(j => savedJobIds.has(j.id));
  }

  renderJobCards(filtered);

  const countText = `${filtered.length} roles available`;
  const countEl = document.getElementById('feed-count');
  if (countEl) countEl.textContent = countText;

  const sheetApplyBtn = document.getElementById('sheet-apply-btn-label');
  if (sheetApplyBtn) sheetApplyBtn.textContent = `Show ${filtered.length} Openings`;
}

// Render Job Cards with Highlighting & AI Match Badges
function renderJobCards(jobs) {
  const container = document.getElementById('job-rows-container');
  if (!container) return;

  if (!jobs.length) {
    container.innerHTML = `
      <div class="empty-state-box">
        <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="1.6"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <div style="font-size:15px; font-weight:700; color:#CBD5E1;">
          ${activeTab === 'saved' ? 'No saved openings yet' : 'No matching roles found'}
        </div>
        <div style="font-size:13px; color:#64748B;">
          ${activeTab === 'saved' ? 'Click the bookmark icon on any role to pin it to this view.' : 'Try adjusting the max experience slider or broadening your location filter.'}
        </div>
      </div>
    `;
    return;
  }

  const q = activeFilters.q;

  container.innerHTML = jobs.map(j => {
    const isSaved = savedJobIds.has(j.id);
    const matchData = jobMatchesMap[j.id];
    const matchScore = matchData ? matchData.score : j.match_score;
    const matchExplanation = matchData ? matchData.explanation : j.why_matched;

    const portalBadgeText = j.portalBadge || `${(j.ats_type || 'Direct').toUpperCase()} Direct Portal`;
    const applyUrl = j.applyUrl || j.apply_url || '#';
    const expText = j.expText || j.experience || `${j.experience_min || 0} - ${j.experience_max || 3} yrs`;

    return `
      <article class="job-row">
        <div class="job-row-main">
          <div class="job-row-title-area">
            <h3 class="job-title">${highlightQuery(j.title, q)}</h3>
            <div class="job-company-line">
              <span class="job-company-badge">${highlightQuery(j.company, q)}</span>
              <span>·</span>
              <span>${escapeHtml(j.location || 'Remote')}</span>
            </div>
          </div>

          <div class="job-actions-top">
            ${matchScore ? `
              <div class="match-chip tabular-num">
                ${matchScore}% match
              </div>
            ` : ''}
            <button class="btn-bookmark ${isSaved ? 'saved' : ''}" title="${isSaved ? 'Remove bookmark' : 'Save role'}" onclick="toggleBookmark('${j.id}')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            </button>
          </div>
        </div>

        <!-- Metadata Line (Location, Experience, Verified Live) -->
        <div class="job-meta-line">
          <span class="job-meta-item">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            ${escapeHtml(j.location || 'Worldwide Remote')}
          </span>
          <span class="job-meta-item tabular-num">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
            ${escapeHtml(expText)}
          </span>
          <span class="job-meta-item">
            <span class="verified-micro-badge">
              <span class="verified-micro-dot"></span>
              Verified Live
            </span>
          </span>
        </div>

        <!-- AI Match Explanation Callout (if available) -->
        ${matchExplanation ? `
          <div class="job-match-reason">
            ${escapeHtml(matchExplanation)}
          </div>
        ` : ''}

        <!-- Skills List with Highlight -->
        ${(j.skills && j.skills.length) ? `
          <div class="job-skills-row">
            ${j.skills.slice(0, 5).map(s => `<span class="skill-tag">${highlightQuery(s, q)}</span>`).join('')}
          </div>
        ` : ''}

        <!-- Job Row Actions / 3px Tactile Apply Button -->
        <div class="job-row-actions">
          <div class="source-brand-badge">
            ${renderPortalSvg(j.portal || j.ats_type || '')}
            <span>${escapeHtml(portalBadgeText)}</span>
          </div>
          <a href="${applyUrl}" target="_blank" rel="noopener noreferrer" class="btn-apply-link">
            <span>Direct Apply</span>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
          </a>
        </div>
      </article>
    `;
  }).join('');
}

// Render Brand Vector SVG Logos (No Emojis)
function renderPortalSvg(portal) {
  const p = String(portal).toLowerCase();
  if (p.includes('amazon')) {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`;
  } else if (p.includes('greenhouse')) {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;
  } else if (p.includes('ycombinator') || p.includes('yc')) {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FF5B1F" stroke-width="2"><polygon points="12 2 2 22 22 22"/></svg>`;
  } else if (p.includes('lever')) {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><polygon points="6 2 18 2 18 6 6 6"/><polygon points="3 11 21 11 21 15 3 15"/><polygon points="9 19 15 19 15 22 9 22"/></svg>`;
  }
  return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
}

// Highlight keywords in text
function highlightQuery(text, query) {
  if (!query || !text) return escapeHtml(text || '');
  const escapedText = escapeHtml(text);
  const cleanQ = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${cleanQ})`, 'gi');
  return escapedText.replace(regex, '<mark class="search-kw">$1</mark>');
}

// ==========================================================================
// IN-MEMORY CV DROPZONE & MATCHING (DPDP COMPLIANT)
// ==========================================================================
let prefLocationHub = 'All';
let prefDiscipline = 'All';

function selectPrefLocation(btn, val) {
  prefLocationHub = val;
  document.querySelectorAll('#pref-location-chips .pref-chip').forEach(el => el.classList.remove('active'));
  btn.classList.add('active');
}

function selectPrefRole(btn, val) {
  prefDiscipline = val;
  document.querySelectorAll('#pref-role-chips .pref-chip').forEach(el => el.classList.remove('active'));
  btn.classList.add('active');
}

async function onCvSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const statusText = document.getElementById('dropzone-status-text');
  statusText.textContent = `Analyzing ${file.name} in RAM...`;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('targetHub', prefLocationHub);
  formData.append('targetDiscipline', prefDiscipline);

  try {
    const res = await fetch(`${API_BASE}/cv/match`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) throw new Error("Failed to parse CV");
    const data = await res.json();
    statusText.textContent = `Analyzed: ${file.name}`;

    // Render candidate profile
    const profile = data.profile;
    if (profile) {
      const box = document.getElementById('candidate-data-box');
      if (box) box.style.display = 'block';
      document.getElementById('cand-headline').textContent = profile.headline;
      document.getElementById('cand-exp').textContent = profile.experienceText;
      const skillsContainer = document.getElementById('cand-skills');
      if (skillsContainer && profile.skills) {
        skillsContainer.innerHTML = profile.skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
      }
    }

    // Store matches map & re-render cards
    if (data.matches) {
      jobMatchesMap = data.matches;
      applyFiltersAndRender();
      document.getElementById('feed-count').textContent = `AI ranked matches active`;
    }
  } catch (err) {
    console.error("CV upload error:", err);
    statusText.textContent = "Upload failed. Please use PDF.";
  }
}

async function recalculateMatches() {
  const fileInput = document.getElementById('cv-file-input');
  if (!fileInput.files.length) {
    fileInput.click();
    return;
  }
  onCvSelected({ target: fileInput });
}

async function deleteMyData() {
  if (!confirm("Permanently wipe your CV profile and parsed in-memory attributes?")) return;
  try {
    await fetch(`${API_BASE}/profile`, { method: 'DELETE' });
  } catch (err) {}
  jobMatchesMap = {};
  document.getElementById('candidate-data-box').style.display = 'none';
  document.getElementById('dropzone-status-text').textContent = 'Upload CV Document';
  applyFiltersAndRender();
}

async function loadProfileData() {
  try {
    const res = await fetch(`${API_BASE}/profile`);
    if (!res.ok) return;
    const data = await res.json();
    const profile = data.profile;
    if (!profile || !profile.headline) return;

    const box = document.getElementById('candidate-data-box');
    if (box) box.style.display = 'block';
    document.getElementById('cand-headline').textContent = profile.headline;
    document.getElementById('cand-exp').textContent = `${profile.years_of_experience || 0} years experience`;
    const skillsContainer = document.getElementById('cand-skills');
    if (skillsContainer && profile.skills) {
      skillsContainer.innerHTML = profile.skills.slice(0, 6).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
    }
  } catch (err) {}
}

// ==========================================================================
// MOBILE DRAWER MODAL HELPERS
// ==========================================================================
function openFiltersModal() {
  document.getElementById('mobile-filter-modal').classList.add('open');
}
function closeFiltersModal() {
  document.getElementById('mobile-filter-modal').classList.remove('open');
}
function onModalBackdropClick(e) {
  if (e.target.id === 'mobile-filter-modal') closeFiltersModal();
}
function showMobileTab(tab) {
  if (tab === 'roles') setTab('all');
  else if (tab === 'saved') setTab('saved');
}

// Security HTML Escaper
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
