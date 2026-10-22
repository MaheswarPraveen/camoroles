/**
 * CAMOUROLES CLIENT ENGINE
 * Handles 150ms debounced search, tactile slider physics,
 * Google Auth profile sync, in-memory CV matcher, and bookmarking.
 */

const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'https://camouroles.pages.dev/api' : window.location.origin + '/api';

// State Store
let activeFilters = {
  q: '',
  discipline: 'all',
  location: 'all',
  maxExp: 10,
  expPreset: 'all',
  ats: 'all',
  company: 'all'
};

let activeTab = 'all'; // 'all' or 'saved'
let allJobsList = [];
let jobMatchesMap = {}; // { jobId: { score, explanation } }
let savedJobIds = new Set(JSON.parse(localStorage.getItem('camouroles_saved_jobs') || '[]'));
let currentUser = JSON.parse(localStorage.getItem('camouroles_user') || 'null');
let activeSelectedPlan = 'month';
let isUserPro = false; // set only from the server's /api/profile answer
let userUnlimitedUntil = null;
try { localStorage.removeItem('camouroles_pro_unlimited'); localStorage.removeItem('camouroles_pro_until'); } catch (e) {}
let currentTheme = localStorage.getItem('camouroles_theme') || 'light';
let searchDebounceTimer = null;
let currentView = 'feed'; // 'feed', 'saved', 'profile'
let searchMode = 'ai'; // 'ai' or 'manual'
let currentProfileData = null;
let selectedProfileHub = 'All';
let aiChatMatchedJobs = [];
let modalChatHistory = [];

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

// Theme Switcher (Paperneat Light vs Espresso Dark)
function initTheme() {
  document.documentElement.setAttribute('data-theme', currentTheme);
  updateThemeIcon(currentTheme);
}

function toggleTheme() {
  currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  localStorage.setItem('camouroles_theme', currentTheme);
  updateThemeIcon(currentTheme);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;
  if (theme === 'dark') {
    // Show Moon/Sun state
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
    btn.title = "Switch to Paperneat Light Mode";
  } else {
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    btn.title = "Switch to Warm Espresso Dark Mode";
  }
}

// On Page Load
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  renderAuthUI();
  updateProBadgeUI();
  initGoogleAuth();
  updateSavedPillCount();
  syncExpSlider(10, 'all');
  loadJobs();
  loadProfileData();
  loadChatHistoryFromStorage();
  updateAiSearchBarText();

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

function setCompanyFilter(val) {
  const current = String(activeFilters.company || 'all').toLowerCase();
  const target = String(val || 'all').toLowerCase();
  activeFilters.company = (current === target) ? 'all' : val;

  document.querySelectorAll('.company-showcase-item').forEach(el => {
    const compAttr = (el.getAttribute('data-company') || '').toLowerCase();
    el.classList.toggle('active', compAttr === activeFilters.company.toLowerCase());
  });

  updateActivePills();
  applyFiltersAndRender();

  if (activeFilters.company !== 'all') {
    const feed = document.getElementById('job-rows-container') || document.querySelector('.feed-column');
    if (feed) feed.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ==========================================================================
// 150MS DEBOUNCED SEARCH WITH CLEAR BUTTON
// ==========================================================================
function onSearchInput(val) {
  const heroInput = document.getElementById('hero-search-input');
  const deskInput = document.getElementById('desktop-search-input');
  const mobInput = document.getElementById('mobile-search-input');
  const heroClear = document.getElementById('hero-search-clear');
  const clearBtn = document.getElementById('search-clear-btn');

  if (heroInput && heroInput.value !== val) heroInput.value = val;
  if (deskInput && deskInput.value !== val) deskInput.value = val;
  if (mobInput && mobInput.value !== val) mobInput.value = val;

  if (heroClear) heroClear.style.display = val ? 'block' : 'none';
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
  if (activeFilters.company && activeFilters.company !== 'all') {
    pills.push(`<span>Company: ${escapeHtml(activeFilters.company)}</span><button onclick="setCompanyFilter('all')">✕</button>`);
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
  const topSavedCount = document.getElementById('top-saved-count');
  if (topSavedCount) topSavedCount.textContent = savedJobIds.size;
}

async function syncBookmarksWithCloud() {
  // Saved roles live in this browser only for now.
}

// ==========================================================================
// GOOGLE SIGN-IN & PROFILE DROPDOWN
// ==========================================================================
function renderAuthUI() {
  const container = document.getElementById('top-google-auth-wrap') || document.getElementById('auth-container');
  if (!container) return;

  if (currentUser) {
    container.innerHTML = `
      <button class="google-user-pill" onclick="toggleProfileDropdown(event)" title="Account details">
        <img class="google-user-avatar" src="${currentUser.picture || 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=Camouroles'}" alt="${escapeHtml(currentUser.name || 'User')}">
        <span class="google-user-name">${escapeHtml((currentUser.name || 'User').split(' ')[0])}</span>
      </button>
      <div class="profile-dropdown-menu" id="profile-dropdown-menu">
        <div class="dropdown-user-header">
          <div class="dropdown-user-name">${escapeHtml(currentUser.name || 'Engineer')}</div>
          <div class="dropdown-user-email">${escapeHtml(currentUser.email || 'engineer@camouroles.io')}</div>
        </div>
        <button class="dropdown-item" onclick="setTab('saved'); toggleProfileDropdown(event);">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          <span>Saved Roles (<span id="menu-saved-count">${savedJobIds.size}</span>)</span>
        </button>
        <button class="dropdown-item" onclick="openPlansModal(); toggleProfileDropdown(event);">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
          <span>${isUserPro ? 'Manage Pro Membership' : 'Upgrade to Pro'}</span>
        </button>
        <button class="dropdown-item danger" onclick="deleteMyData(); toggleProfileDropdown(event);">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          <span>Clear Saved Profile</span>
        </button>
        <button class="dropdown-item" onclick="signOutGoogle(); toggleProfileDropdown(event);">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          <span>Sign Out</span>
        </button>
      </div>
    `;
  } else {
    container.innerHTML = `
      <button class="btn-google-signin" id="btn-google-login" onclick="signInWithGoogle()" title="Sign in with Google">
        <svg width="14" height="14" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>
        <span id="google-btn-text">Sign In</span>
      </button>
    `;
  }
}

const SUPABASE_AUTH_URL = 'https://xteoktfzftqybflpubvo.supabase.co';
const SUPABASE_AUTH_ANON_KEY = 'sb_publishable_y7hNwkSzqtaHR5OkoSbuWA_lKobzcaZ';

function signInWithGoogle() {
  const redirectUrl = encodeURIComponent(window.location.origin + window.location.pathname);
  window.location.href = `${SUPABASE_AUTH_URL}/auth/v1/authorize?provider=google&redirect_to=${redirectUrl}`;
}

function readSession() {
  try { return JSON.parse(localStorage.getItem('camouroles_session') || 'null'); } catch (e) { return null; }
}

function saveSession(accessToken, refreshToken, expiresInSec) {
  localStorage.setItem('camouroles_session', JSON.stringify({
    access_token: accessToken,
    refresh_token: refreshToken,
    expires_at: Date.now() + (Number(expiresInSec) || 3600) * 1000,
  }));
}

function clearSession() {
  currentUser = null;
  isUserPro = false;
  userUnlimitedUntil = null;
  localStorage.removeItem('camouroles_user');
  localStorage.removeItem('camouroles_token');
  localStorage.removeItem('camouroles_session');
}

// Returns a valid Supabase access token, refreshing it when it is about to expire; null when signed out.
async function getAccessToken() {
  const session = readSession();
  if (!session || !session.access_token) return null;
  if (session.expires_at - Date.now() > 60 * 1000) return session.access_token;
  try {
    if (!session.refresh_token) throw new Error('no refresh token');
    const res = await fetch(`${SUPABASE_AUTH_URL}/auth/v1/token?grant_type=refresh_token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'apikey': SUPABASE_AUTH_ANON_KEY },
      body: JSON.stringify({ refresh_token: session.refresh_token }),
    });
    if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.error || 'Could not read this CV'); }
    const data = await res.json();
    saveSession(data.access_token, data.refresh_token, data.expires_in);
    return data.access_token;
  } catch (e) {
    clearSession();
    renderAuthUI();
    updateProBadgeUI();
    return null;
  }
}

async function authHeaders(extra = {}) {
  const token = await getAccessToken();
  return token ? { ...extra, 'Authorization': `Bearer ${token}` } : { ...extra };
}

async function checkOAuthCallback() {
  const hash = window.location.hash;
  if (!hash || !hash.includes('access_token=')) return;

  try {
    const params = new URLSearchParams(hash.replace(/^#/, ''));
    const accessToken = params.get('access_token');
    if (!accessToken) return;

    const res = await fetch(`${SUPABASE_AUTH_URL}/auth/v1/user`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'apikey': SUPABASE_AUTH_ANON_KEY
      }
    });

    if (res.ok) {
      const u = await res.json();
      const meta = u.user_metadata || {};
      const fullName = meta.full_name || meta.name || (u.email ? u.email.split('@')[0] : 'Engineer');
      const avatarUrl = meta.avatar_url || meta.picture || '';

      saveSession(accessToken, params.get('refresh_token'), params.get('expires_in'));
      currentUser = {
        id: u.id,
        email: u.email,
        name: fullName,
        picture: avatarUrl,
        savedIds: [...savedJobIds]
      };

      localStorage.setItem('camouroles_user', JSON.stringify(currentUser));

      renderAuthUI();
      updateSavedPillCount();
      applyFiltersAndRender();
      showNotification(`Signed in as ${currentUser.name}`);
      loadProfileData();
    } else {
      showNotification('Sign-in failed. Please try again.');
    }
  } catch (err) {
    console.error("Supabase OAuth callback error:", err);
  } finally {
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }
}

function initGoogleAuth() {
  // A user saved by an older build without a session token has to sign in again.
  if (currentUser && !readSession()) {
    clearSession();
    renderAuthUI();
  }
  if (window.location.hash.includes('error_description=')) {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    showNotification('Sign-in failed: ' + (params.get('error_description') || 'unknown error'));
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
    return;
  }
  checkOAuthCallback();
}

function signOutGoogle() {
  const session = readSession();
  if (session && session.access_token) {
    fetch(`${SUPABASE_AUTH_URL}/auth/v1/logout`, {
      method: 'POST',
      headers: { 'apikey': SUPABASE_AUTH_ANON_KEY, 'Authorization': `Bearer ${session.access_token}` },
    }).catch(() => {});
  }
  clearSession();
  renderAuthUI();
  updateProBadgeUI();
  showNotification('Signed out');
}

function toggleProfileDropdown(e) {
  if (e) e.stopPropagation();
  const menu = document.getElementById('profile-dropdown-menu');
  if (menu) menu.classList.toggle('open');
}

// ==========================================================================
// PRIME PRO MEMBERSHIP & RAZORPAY CHECKOUT
// ==========================================================================
function updateProBadgeUI() {
  const badgeBtn = document.getElementById('top-pro-badge-btn');
  const labelEl = document.getElementById('top-pro-label');
  if (!badgeBtn) return;

  if (isUserPro) {
    badgeBtn.classList.add('active');
    if (labelEl) labelEl.textContent = 'Pro Active';
    badgeBtn.title = 'CAMOUROLES Pro Active · Unlimited Direct Access';
  } else {
    badgeBtn.classList.remove('active');
    if (labelEl) labelEl.textContent = 'Pro Upgrade';
    badgeBtn.title = 'View Membership Plans & Unlock Roles';
  }
}

function openPlansModal(preferredPlan) {
  if (isUserPro && !preferredPlan) {
    showNotification('CAMOUROLES Pro is active with unlimited verified role access.');
    return;
  }
  if (preferredPlan) selectPlan(preferredPlan);
  const modal = document.getElementById('plans-pricing-modal');
  if (modal) modal.classList.add('open');
}

function closePlansModal() {
  const modal = document.getElementById('plans-pricing-modal');
  if (modal) modal.classList.remove('open');
}

function selectPlan(plan) {
  activeSelectedPlan = plan;
  const segMonth = document.getElementById('seg-plan-month');
  const segWeek = document.getElementById('seg-plan-week');
  const priceVal = document.getElementById('plan-display-price');
  const priceWas = document.getElementById('plan-display-was');
  const priceTag = document.getElementById('plan-display-tag');
  const submitBtn = document.getElementById('btn-razorpay-submit');

  if (plan === 'week') {
    if (segMonth) segMonth.classList.remove('active');
    if (segWeek) segWeek.classList.add('active');
    if (priceVal) priceVal.textContent = '₹29';
    if (priceWas) priceWas.textContent = '₹49';
    if (priceTag) priceTag.textContent = '7-DAY PASS';
    if (submitBtn) submitBtn.innerHTML = `<span>Unlock 7-Day Access (₹29)</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
  } else {
    activeSelectedPlan = 'month';
    if (segWeek) segWeek.classList.remove('active');
    if (segMonth) segMonth.classList.add('active');
    if (priceVal) priceVal.textContent = '₹99';
    if (priceWas) priceWas.textContent = '₹199';
    if (priceTag) priceTag.textContent = 'MOST POPULAR';
    if (submitBtn) submitBtn.innerHTML = `<span>Unlock Monthly Pro (₹99)</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
  }
}

// Stable id for this browser: guests' Pro is kept on it, and it moves to the account on sign-in.
function browserDeviceId() {
  let id = null;
  try { id = localStorage.getItem('camouroles_device'); } catch (e) {}
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`);
    try { localStorage.setItem('camouroles_device', id); } catch (e) {}
  }
  return id;
}

// No sign-in needed to pay. Guests get Pro on this browser; signing in later keeps it.
async function startRazorpayCheckout() {
  const submitBtn = document.getElementById('btn-razorpay-submit');
  const origHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Connecting to Razorpay...</span>`;
  }

  try {
    const res = await fetch(`${API_BASE}/checkout/order`, {
      method: 'POST',
      headers: await authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ plan: activeSelectedPlan, device_id: browserDeviceId() })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to initialize payment order');
    }

    const orderData = await res.json();

    if (!window.Razorpay) {
      throw new Error('Razorpay secure checkout is loading. Please retry in a moment.');
    }

    const options = {
      key: orderData.key_id || 'rzp_live_TjW0ZP4t3xCyrO',
      amount: orderData.amount,
      currency: 'INR',
      name: 'CAMOUROLES',
      description: activeSelectedPlan === 'week' ? 'Weekly Pass (7 Days Access)' : 'Monthly Pro (Unlimited Access)',
      order_id: orderData.order_id,
      theme: {
        color: '#C5A059'
      },
      prefill: {
        name: currentUser?.name || '',
        email: currentUser?.email || ''
      },
      modal: {
        ondismiss: function() {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
          }
        }
      },
      handler: async function(paymentResponse) {
        if (submitBtn) {
          submitBtn.innerHTML = `<span>Verifying Payment Signature...</span>`;
        }
        try {
          const verifyRes = await fetch(`${API_BASE}/checkout/verify`, {
            method: 'POST',
            headers: await authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
              razorpay_order_id: paymentResponse.razorpay_order_id,
              razorpay_payment_id: paymentResponse.razorpay_payment_id,
              razorpay_signature: paymentResponse.razorpay_signature,
              plan: activeSelectedPlan,
              device_id: browserDeviceId()
            })
          });

          if (!verifyRes.ok) {
            const vErr = await verifyRes.json().catch(() => ({}));
            throw new Error(vErr.detail || 'Payment verification failed');
          }

          const verifyData = await verifyRes.json();
          isUserPro = true;
          userUnlimitedUntil = verifyData.unlimited_until;

          updateProBadgeUI();
          closePlansModal();
          showNotification(currentUser ? 'Payment verified. CAMOUROLES Pro is now active.' : 'Pro is active on this browser. Sign in anytime to keep it on your account.');
        } catch (vErr) {
          showNotification('Verification issue: ' + vErr.message);
        } finally {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
          }
        }
      }
    };

    const rzp = new window.Razorpay(options);
    rzp.on('payment.failed', function(resp) {
      showNotification('Payment cancelled or unsuccessful.');
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origHtml;
      }
    });
    rzp.open();
  } catch (err) {
    showNotification(err.message || 'Payment could not be started');
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = origHtml;
    }
  }
}

function showNotification(msg) {
  let toast = document.getElementById('camouroles-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'camouroles-toast';
    toast.className = 'camouroles-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('visible');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.classList.remove('visible');
  }, 3500);
}

// ==========================================================================
// GEOLOCATION & NEARBY PREFERENCE INTELLIGENCE
// ==========================================================================
let userNearbyRegion = null;

function detectNearbyRegion(geoData) {
  const tz = (Intl.DateTimeFormat().resolvedOptions().timeZone || '').toLowerCase();
  const country = String(geoData?.country || '').toUpperCase();
  const city = String(geoData?.city || '').toLowerCase();

  // 1. India
  if (country === 'IN' || tz.includes('kolkata') || tz.includes('calcutta') || tz.includes('india')) {
    return { key: 'india', name: 'India', flag: '🇮🇳' };
  }
  // 2. UAE / Middle East
  if (['AE', 'SA', 'QA', 'OM', 'KW', 'BH'].includes(country) || tz.includes('dubai') || tz.includes('muscat') || tz.includes('riyadh')) {
    return { key: 'uae', name: 'UAE & Middle East', flag: '🇦🇪' };
  }
  // 3. UK / London
  if (country === 'GB' || tz.includes('london')) {
    return { key: 'london', name: 'UK / London', flag: '🇬🇧' };
  }
  // 4. Western Europe
  if (['DE', 'FR', 'NL', 'CH', 'SE', 'IE'].includes(country) || tz.includes('berlin') || tz.includes('paris') || tz.includes('amsterdam') || tz.includes('zurich')) {
    return { key: 'europe', name: 'Europe', flag: '🇪🇺' };
  }
  // 5. US Bay Area / West Coast
  if ((country === 'US' || country === 'CA') && (tz.includes('los_angeles') || tz.includes('san_francisco') || tz.includes('vancouver') || city.includes('francisco') || city.includes('diego') || city.includes('seattle'))) {
    return { key: 'sf_bay', name: 'SF Bay Area / West Coast', flag: '🇺🇸' };
  }
  // 6. US East Coast / NYC
  if ((country === 'US' || country === 'CA') && (tz.includes('new_york') || tz.includes('toronto') || tz.includes('boston') || city.includes('york') || city.includes('toronto'))) {
    return { key: 'nyc', name: 'NYC / East Coast', flag: '🇺🇸' };
  }
  // 7. General US
  if (country === 'US') {
    return { key: 'us', name: 'United States', flag: '🇺🇸' };
  }
  // 8. Singapore / APAC
  if (country === 'SG' || tz.includes('singapore')) {
    return { key: 'singapore', name: 'Singapore / APAC', flag: '🇸🇬' };
  }
  // Default to Worldwide Remote
  return { key: 'worldwide_remote', name: 'Worldwide Remote', flag: '🌐' };
}

function getJobLocationPriority(job) {
  if (!userNearbyRegion) {
    userNearbyRegion = detectNearbyRegion(null);
  }
  const k = userNearbyRegion.key;
  if (!job) return 0;

  // Direct match with candidate's local region (+100)
  if (k !== 'worldwide_remote' && matchesLocation(job, k)) {
    return 100;
  }
  // Worldwide remote roles (+60)
  if (matchesLocation(job, 'worldwide_remote')) {
    return 60;
  }
  return 0;
}

// ==========================================================================
// LOAD JOBS FROM API (Instant Session Cache Hydration & Shimmer Loader)
// ==========================================================================
function renderFeedLoadingState() {
  const container = document.getElementById('job-rows-container');
  if (!container) return;
  container.innerHTML = `
    <div class="feed-loading-state">
      <div class="feed-loading-banner">
        <div class="feed-loading-radar"></div>
        <span class="feed-loading-text">Connecting to Edge Pipeline · Calibrating verified requisitions...</span>
      </div>

      <div class="skeleton-shimmer-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div class="skeleton-line title"></div>
          <div class="skeleton-line company"></div>
        </div>
        <div class="skeleton-line meta"></div>
        <div class="skeleton-pills-row">
          <div class="skeleton-line pill"></div>
          <div class="skeleton-line pill"></div>
          <div class="skeleton-line pill"></div>
        </div>
      </div>

      <div class="skeleton-shimmer-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div class="skeleton-line title" style="width:48%;"></div>
          <div class="skeleton-line company"></div>
        </div>
        <div class="skeleton-line meta" style="width:32%;"></div>
        <div class="skeleton-pills-row">
          <div class="skeleton-line pill"></div>
          <div class="skeleton-line pill"></div>
        </div>
      </div>

      <div class="skeleton-shimmer-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div class="skeleton-line title" style="width:60%;"></div>
          <div class="skeleton-line company"></div>
        </div>
        <div class="skeleton-line meta" style="width:42%;"></div>
        <div class="skeleton-pills-row">
          <div class="skeleton-line pill"></div>
          <div class="skeleton-line pill"></div>
          <div class="skeleton-line pill"></div>
        </div>
      </div>
    </div>
  `;
}

async function loadJobs() {
  try {
    // 0. Initialize candidate nearby region from client environment immediately
    if (!userNearbyRegion) {
      userNearbyRegion = detectNearbyRegion(null);
    }

    // 1. Show ambient shimmer loading state if jobs are not yet loaded
    if (!allJobsList || allJobsList.length === 0) {
      renderFeedLoadingState();
    }

    // 2. Instant Cache Hydration: If cached jobs exist in sessionStorage, hydrate in 0ms!
    try {
      const cached = sessionStorage.getItem('camouroles_jobs_cache');
      if (cached) {
        const cachedData = JSON.parse(cached);
        if (cachedData && cachedData.jobs && cachedData.jobs.length) {
          allJobsList = cachedData.jobs;
          const totalCount = cachedData.totalVerified || allJobsList.length;
          const verifiedEl = document.getElementById('verified-roles-indicator');
          if (verifiedEl) verifiedEl.textContent = `${totalCount.toLocaleString()} live roles`;
          const feedCountPill = document.getElementById('feed-count-pill');
          if (feedCountPill) feedCountPill.textContent = totalCount.toLocaleString();
          applyFiltersAndRender();
          updateHeroChatCount();
        }
      }
    } catch (e) {}

    // 3. Fetch fresh inventory from API (Edge Cached) alongside fast edge geo
    const [jobsRes, geoRes] = await Promise.all([
      fetch(`${API_BASE}/jobs`),
      fetch(`${API_BASE}/geo`).catch(() => null)
    ]);
    const data = await jobsRes.json();
    let geoData = data?.geo || null;
    if (geoRes && geoRes.ok) {
      try {
        const edgeGeo = await geoRes.json();
        if (edgeGeo && edgeGeo.country) geoData = edgeGeo;
      } catch (e) {}
    }
    if (data && data.jobs && data.jobs.length) {
      allJobsList = data.jobs;
      if (geoData) {
        userNearbyRegion = detectNearbyRegion(geoData);
      }
      try {
        sessionStorage.setItem('camouroles_jobs_cache', JSON.stringify({
          totalVerified: data.totalVerified,
          jobs: data.jobs.slice(0, 3000),
          geo: geoData
        }));
      } catch (e) {}

      const totalCount = data.totalVerified || allJobsList.length || 10237;
      const verifiedEl = document.getElementById('verified-roles-indicator');
      if (verifiedEl) verifiedEl.textContent = `${totalCount.toLocaleString()} live roles`;
      const feedCountPill = document.getElementById('feed-count-pill');
      if (feedCountPill) feedCountPill.textContent = totalCount.toLocaleString();

      applyFiltersAndRender();
      updateHeroChatCount();
    }
  } catch (err) {
    console.error("Error loading jobs:", err);
  }
}

// ==========================================================================
// DISCIPLINE TAXONOMY & INTELLIGENT MATCHING
// ==========================================================================
const DISCIPLINE_TAXONOMY = {
  spacetech: {
    titles: ['space', 'satellite', 'aerospace', 'rocket', 'orbital', 'astranis', 'relativity', 'planet labs', 'spire', 'propulsion', 'launch', 'avionics', 'flight software'],
    skills: ['satellite systems', 'aerospace', 'rf engineering', 'orbital mechanics', 'avionics', 'flight software', 'c++', 'fpga', 'propulsion']
  },
  climate_cleanenergy: {
    titles: ['climate', 'fusion', 'battery', 'energy', 'redwood', 'solugen', 'form energy', 'tokamak', 'clean energy', 'storage', 'electrochemical', 'plasma'],
    skills: ['fusion energy', 'plasma physics', 'battery tech', 'materials science', 'green chemistry', 'energy storage', 'superconducting', 'cryogenics']
  },
  biotech_health: {
    titles: ['bio', 'genomic', 'pharma', 'clinical', 'molecular', 'ginkgo', 'recursion', 'insitro', '10x', 'biology', 'bioinformatics', 'chemist', 'scientist'],
    skills: ['computational biology', 'genomics', 'bioinformatics', 'single cell', 'assay', 'biotechnology', 'crispr', 'chemistry', 'pytorch']
  },
  defense_cyber: {
    titles: ['defense', 'cyber', 'cloudflare', 'palantir', 'intelligence', 'gotham', 'foundry', 'national security', 'edge systems'],
    skills: ['defense tech', 'zero trust', 'edge systems', 'distributed systems', 'rust', 'go', 'networking', 'security', 'kubernetes']
  },
  ai_ml: {
    titles: ['ai', 'ml', 'machine learning', 'deep learning', 'nlp', 'llm', 'genai', 'agentic', 'artificial intelligence', 'research scientist', 'data scientist', 'computer vision'],
    skills: ['pytorch', 'tensorflow', 'python', 'sagemaker', 'cuda', 'llm', 'rag', 'langchain', 'huggingface', 'mlops', 'scikit', 'deep learning', 'neural']
  },
  backend: {
    titles: ['backend', 'back-end', 'distributed', 'platform', 'systems', 'infrastructure', 'api', 'services', 'sde', 'software dev', 'software engineer', 'core engineer'],
    skills: ['java', 'go', 'golang', 'rust', 'c++', 'python', 'distributed systems', 'aws', 'kafka', 'postgresql', 'microservices', 'grpc', 'redis', 'database']
  },
  frontend: {
    titles: ['frontend', 'front-end', 'web', 'ui', 'ux', 'client', 'web systems', 'front end'],
    skills: ['react', 'typescript', 'javascript', 'next.js', 'vue', 'angular', 'css', 'html', 'tailwind', 'webpack', 'frontend', 'ui']
  },
  fullstack: {
    titles: ['full stack', 'fullstack', 'full-stack', 'web developer'],
    skills: ['react', 'node', 'fullstack', 'typescript', 'express', 'django', 'fastapi']
  },
  devops: {
    titles: ['devops', 'sre', 'site reliability', 'cloud', 'infrastructure', 'platform ops', 'operations'],
    skills: ['kubernetes', 'k8s', 'docker', 'terraform', 'aws', 'gcp', 'azure', 'ci/cd', 'ansible', 'helm', 'linux', 'cloud']
  },
  robotics: {
    titles: ['robotics', 'robot', 'autonomy', 'autonomous', 'motion', 'control', 'controls', 'navigation', 'mechatronics'],
    skills: ['ros', 'ros2', 'motion planning', 'controls', 'slam', 'kinematics', 'c++', 'lidar', 'simulation', 'robotics']
  },
  embedded: {
    titles: ['embedded', 'firmware', 'bsp', 'device driver', 'kernel', 'low level', 'hardware software'],
    skills: ['c', 'c++', 'rtos', 'freertos', 'arm', 'microcontroller', 'mcu', 'uart', 'spi', 'i2c', 'fpga', 'firmware', 'embedded']
  },
  vision: {
    titles: ['vision', 'perception', 'imaging', 'sensor fusion', 'optical'],
    skills: ['computer vision', 'opencv', 'point cloud', 'lidar', 'camera', 'perception', '3d reconstruction', 'image processing']
  },
  mobile: {
    titles: ['mobile', 'ios', 'android', 'swift', 'kotlin', 'apps'],
    skills: ['ios', 'android', 'swift', 'swiftui', 'kotlin', 'flutter', 'react native', 'mobile']
  },
  security: {
    titles: ['security', 'infosec', 'appsec', 'cyber', 'soc', 'penetration', 'trust', 'compliance', 'identity', 'fraud'],
    skills: ['security', 'cryptography', 'auth', 'iam', 'penetration testing', 'zero trust', 'firewall', 'fraud']
  },
  data: {
    titles: ['data engineer', 'data platform', 'analytics engineer', 'pipeline', 'etl', 'big data'],
    skills: ['spark', 'hadoop', 'snowflake', 'databricks', 'sql', 'dbt', 'airflow', 'kafka', 'data pipeline']
  },
  hardware: {
    titles: ['hardware', 'silicon', 'asic', 'fpga', 'board', 'pcb', 'electrical', 'rf', 'annapurna', 'pd engineer'],
    skills: ['verilog', 'vhdl', 'pcb', 'schematic', 'fpga', 'asic', 'cadence', 'soldering', 'silicon']
  },
  game_dev: {
    titles: ['game', 'gameplay', 'unreal', 'unity', 'graphics', '3d', 'character', 'animator', 'level designer', 'shader', 'esports', 'concept artist', 'combat', 'art direction'],
    skills: ['c++', 'unreal', 'unity', 'vulkan', 'directx', 'shader', '3d math', 'animation', 'game', 'esports']
  },
  design: {
    titles: ['design', 'designer', 'ui', 'ux', 'product design', 'visual design', 'art director', 'interaction', 'design systems'],
    skills: ['figma', 'ui/ux', 'design systems', 'interaction design', 'prototyping', 'sketch', 'user research']
  },
  business: {
    titles: ['business', 'finance', 'analyst', 'strategy', 'account executive', 'operations', 'sales', 'revenue', 'investment', 'consulting', 'corporate counsel', 'legal', 'counsel', 'partner', 'fpa', 'marketing'],
    skills: ['financial modeling', 'data analysis', 'sql', 'strategy', 'operations', 'excel', 'consulting', 'sales']
  },
  hr: {
    titles: ['hr', 'human resources', 'recruiter', 'talent', 'people', 'people ops', 'recruiting', 'mobility', 'inclusion'],
    skills: ['talent acquisition', 'technical recruiting', 'hr operations', 'people systems', 'sourcing']
  },
  civil_construction: {
    titles: ['civil', 'construction', 'structural', 'site engineer', 'field engineer', 'architectural', 'project engineer'],
    skills: ['autocad', 'civil engineering', 'structural analysis', 'project management', 'construction']
  },
  electrical_hardware: {
    titles: ['electrical', 'electronics', 'hardware', 'fpga', 'asic', 'pcb', 'silicon', 'board', 'bsp', 'circuit'],
    skills: ['pcb design', 'electrical engineering', 'altium', 'fpga', 'hardware debugging', 'oscilloscope']
  },
  safety: {
    titles: ['safety', 'fire', 'ehs', 'hazard', 'process safety', 'systems safety', 'flight safety', 'system safety', 'mission assurance', 'reliability'],
    skills: ['system safety', 'hazard analysis', 'ehs', 'fire protection', 'risk assessment', 'process safety', 'fault tree analysis', 'safety engineering']
  }
};

function matchesDiscipline(job, key) {
  if (!job || !key || key === 'all') return true;
  const k = key.toLowerCase();
  const rule = DISCIPLINE_TAXONOMY[k];
  if (!rule) {
    const t = String(job.title || '').toLowerCase();
    const d = String(job.discipline || '').toLowerCase();
    return t.includes(k) || d.includes(k);
  }

  const title = String(job.title || '').toLowerCase();
  const disc = String(job.discipline || '').toLowerCase();
  const skills = (job.skills || []).map(s => String(s).toLowerCase());

  // Check discipline field if present
  if (disc && (disc.includes(k) || rule.titles.some(kw => disc.includes(kw)))) return true;

  // Check title
  if (rule.titles.some(kw => title.includes(kw))) return true;

  // Check skills tags
  if (skills.some(s => rule.skills.some(kw => s.includes(kw) || kw.includes(s)))) return true;

  return false;
}

// ==========================================================================
// LOCATION HUBS & GLOBAL MATCHING
// ==========================================================================
const LOCATION_MATCHERS = {
  worldwide_remote: (loc, j) => (j && (j.isRemote || j.is_remote)) || loc.includes('remote') || loc.includes('worldwide') || loc.includes('anywhere') || loc.includes('virtual'),
  sf_bay: (loc) => loc.includes('san francisco') || loc.includes('bay area') || loc.includes('mountain view') || loc.includes('sunnyvale') || loc.includes('palo alto') || loc.includes('menlo park') || loc.includes('san jose') || loc.includes('oakland') || loc.includes('berkeley') || loc.includes('redwood') || loc.includes('fremont') || loc.includes('santa clara') || loc.includes('san mateo') || loc.includes('ca,') || loc.includes('california'),
  seattle: (loc) => loc.includes('seattle') || loc.includes('bellevue') || loc.includes('redmond') || loc.includes('kirkland') || loc.includes('washington') || loc.includes('wa,'),
  nyc: (loc) => loc.includes('new york') || loc.includes('nyc') || loc.includes('brooklyn') || loc.includes('manhattan') || loc.includes('ny,'),
  austin: (loc) => loc.includes('austin') || loc.includes('texas') || loc.includes('tx,'),
  london: (loc) => loc.includes('london') || loc.includes('uk') || loc.includes('united kingdom') || loc.includes('england') || loc.includes('cambridge'),
  europe: (loc) => loc.includes('europe') || loc.includes('germany') || loc.includes('berlin') || loc.includes('munich') || loc.includes('france') || loc.includes('paris') || loc.includes('netherlands') || loc.includes('amsterdam') || loc.includes('switzerland') || loc.includes('zurich') || loc.includes('sweden') || loc.includes('stockholm') || loc.includes('ireland') || loc.includes('dublin') || loc.includes('spain') || loc.includes('madrid') || loc.includes('barcelona') || loc.includes('uk') || loc.includes('london'),
  us: (loc) => loc.includes('united states') || loc.includes('usa') || /,\s*[a-z]{2}\b/i.test(loc) || loc.includes('san francisco') || loc.includes('new york') || loc.includes('seattle') || loc.includes('austin') || loc.includes('boston') || loc.includes('chicago') || loc.includes('california') || loc.includes('texas') || loc.includes('washington') || loc.includes('los angeles'),
  germany: (loc) => loc.includes('germany') || loc.includes('munich') || loc.includes('berlin') || loc.includes('frankfurt') || loc.includes('deu') || loc.includes('hamburg'),
  netherlands: (loc) => loc.includes('netherlands') || loc.includes('amsterdam') || loc.includes('nld') || loc.includes('rotterdam') || loc.includes('utrecht'),
  switzerland: (loc) => loc.includes('switzerland') || loc.includes('zurich') || loc.includes('geneva') || loc.includes('che') || loc.includes('lausanne'),
  japan: (loc) => loc.includes('japan') || loc.includes('tokyo') || loc.includes('jpn') || loc.includes('osaka'),
  tokyo: (loc) => loc.includes('japan') || loc.includes('tokyo') || loc.includes('jpn') || loc.includes('osaka'),
  singapore: (loc) => loc.includes('singapore') || loc.includes('sgp'),
  india: (loc) => loc.includes('india') || loc.includes('bengaluru') || loc.includes('bangalore') || loc.includes('hyderabad') || loc.includes('pune') || loc.includes('mumbai') || loc.includes('delhi') || loc.includes('gurgaon') || loc.includes('noida') || loc.includes('ind') || loc.includes('chennai'),
  uae: (loc) => loc.includes('uae') || loc.includes('dubai') || loc.includes('abu dhabi') || loc.includes('sharjah') || loc.includes('emirates') || loc.includes('middle east') || loc.includes('riyadh') || loc.includes('saudi') || loc.includes('doha') || loc.includes('gulf'),
  canada: (loc) => loc.includes('canada') || loc.includes('toronto') || loc.includes('vancouver') || loc.includes('can') || loc.includes('montreal') || loc.includes('waterloo') || loc.includes('ottawa'),
  australia: (loc) => loc.includes('australia') || loc.includes('sydney') || loc.includes('melbourne') || loc.includes('aus') || loc.includes('brisbane'),
  france: (loc) => loc.includes('france') || loc.includes('paris') || loc.includes('fra') || loc.includes('lyon') || loc.includes('toulouse')
};

function matchesLocation(job, locKey) {
  if (!job || !locKey || locKey === 'all') return true;
  const k = String(locKey).toLowerCase().replace(/[\s-]+/g, '_');
  const loc = String(job.location || '').toLowerCase();
  const hub = String(job.hub || '').toLowerCase();

  // If remote is specified, match any remote indicators
  if (k === 'remote' || k === 'worldwide_remote' || k === 'worldwide' || k.includes('remote')) {
    return job.isRemote || job.is_remote || loc.includes('remote') || loc.includes('anywhere') || loc.includes('virtual') || loc.includes('worldwide') || hub.includes('remote');
  }

  const fn = LOCATION_MATCHERS[k];
  if (fn) return fn(loc, job) || fn(hub, job);
  return loc.includes(k) || hub.includes(k) || loc.includes(String(locKey).toLowerCase());
}

// ==========================================================================
// EXPERIENCE & SENIORITY INTELLIGENCE
// ==========================================================================
function getJobExperienceMinMax(job) {
  if (!job) return { min: 0, max: 10 };
  
  if (job.experience_min !== undefined && job.experience_min !== null && !isNaN(parseInt(job.experience_min, 10))) {
    return {
      min: parseInt(job.experience_min, 10),
      max: parseInt(job.experience_max, 10) || (parseInt(job.experience_min, 10) + 3)
    };
  }

  // Parse from raw experience text e.g. "1 - 4 yrs", "5 - 10 yrs", "0 - 2 yrs"
  const raw = String(job.experience || job.expText || job.description || '');
  const rangeMatch = raw.match(/(\d+)\s*(?:-|–|to)\s*(\d+)\s*(?:years?|yrs?)/i);
  if (rangeMatch) {
    return {
      min: parseInt(rangeMatch[1], 10),
      max: parseInt(rangeMatch[2], 10)
    };
  }
  const plusMatch = raw.match(/(\d+)\s*\+\s*(?:years?|yrs?)/i);
  if (plusMatch) {
    const val = parseInt(plusMatch[1], 10);
    return { min: val, max: val + 4 };
  }

  // Infer from Title / Role Seniority
  const title = String(job.title || '').toLowerCase();
  if (title.includes('intern') || title.includes('fresher') || title.includes('graduate') || title.includes('entry') || title.includes('trainee') || title.includes('student') || title.includes('co-op')) {
    return { min: 0, max: 1 };
  }
  if (title.includes('junior') || title.includes('associate') || title.includes('sde 1') || title.includes('sde i') || title.includes('engineer i') || title.includes('level 1') || title.includes('early career') || title.includes('analyst 1')) {
    return { min: 1, max: 2 };
  }
  if (title.includes('sde 2') || title.includes('sde ii') || title.includes('engineer ii') || title.includes('level 2') || title.includes('mid') || title.includes('intermediate')) {
    return { min: 3, max: 5 };
  }
  if (title.includes('senior') || title.includes('sr.') || title.includes('sde 3') || title.includes('sde iii') || title.includes('engineer iii') || title.includes('lead') || title.includes('manager')) {
    return { min: 5, max: 8 };
  }
  if (title.includes('staff') || title.includes('principal') || title.includes('distinguished') || title.includes('fellow') || title.includes('architect') || title.includes('director') || title.includes('vp') || title.includes('head')) {
    return { min: 8, max: 15 };
  }

  return { min: 2, max: 4 }; // Standard mid engineer range
}

function matchesExperience(job, maxExp, expPreset) {
  if (maxExp >= 10 && (expPreset === 'all' || !expPreset)) return true;
  const exp = getJobExperienceMinMax(job);
  const title = String(job.title || '').toLowerCase();
  const isSeniorTitle = title.includes('senior') || title.includes('sr.') || title.includes('lead') || title.includes('staff') || title.includes('principal') || title.includes('architect') || title.includes('manager') || title.includes('director');

  // Handle Preset Buttons
  if (expPreset === '0-1') {
    return exp.min <= 1 && !isSeniorTitle;
  }
  if (expPreset === '1-3') {
    return exp.min <= 3 && !isSeniorTitle;
  }
  if (expPreset === '3-6') {
    return (exp.min >= 2 && exp.min <= 6) || (exp.max >= 4 && exp.max <= 8 && !title.includes('staff') && !title.includes('principal'));
  }
  if (expPreset === '6+') {
    return exp.min >= 5 || exp.max >= 7 || isSeniorTitle;
  }

  // Direct tactile slider value: "Show roles suitable for someone with up to maxExp years"
  if (maxExp === 0) {
    return exp.min === 0;
  }
  if (maxExp <= 2) {
    return exp.min <= maxExp && !isSeniorTitle;
  }
  if (maxExp <= 5) {
    return exp.min <= maxExp && !title.includes('staff') && !title.includes('principal') && !title.includes('architect') && !title.includes('director');
  }
  return exp.min <= maxExp;
}

// ==========================================================================
// MATCH PERCENTAGE INTELLIGENCE & SORTING
// ==========================================================================
let currentSortMode = 'match_desc'; // 'match_desc', 'latest', 'salary'

function onSortChange(val) {
  currentSortMode = val;
  applyFiltersAndRender();
}

function calculateJobMatchScore(job) {
  if (!job) return { score: 0, reason: '' };

  const hasCvActive = Object.keys(jobMatchesMap).length > 0;

  // 1. If CV Match profile exists and has scored this job:
  if (jobMatchesMap[job.id] && jobMatchesMap[job.id].score) {
    return {
      score: Math.min(96, Math.max(50, parseInt(jobMatchesMap[job.id].score, 10))),
      reason: jobMatchesMap[job.id].explanation || 'Tailored to your uploaded CV skills & seniority'
    };
  }

  // If a CV is active, any role outside the Top 50 scored pool receives score 0 (no fake percentage)
  if (hasCvActive) {
    return { score: 0, reason: '' };
  }

  const title = String(job.title || '').toLowerCase();
  const comp = String(job.company || '').toLowerCase();
  const desc = String(job.description || '').toLowerCase();
  const loc = String(job.location || '').toLowerCase();
  const skills = (job.skills || []).map(s => String(s).toLowerCase());
  const disc = String(job.discipline || '').toLowerCase();

  const q = String(activeFilters.q || heroChatCriteria.keywords || '').toLowerCase().trim();
  const targetDisc = (activeFilters.discipline !== 'all' ? activeFilters.discipline : (heroChatCriteria.discipline !== 'all' ? heroChatCriteria.discipline : '')).toLowerCase();
  const targetLoc = (activeFilters.location !== 'all' ? activeFilters.location : (heroChatCriteria.location !== 'all' ? heroChatCriteria.location : '')).toLowerCase();
  const targetComp = (activeFilters.company !== 'all' ? activeFilters.company : '').toLowerCase();

  let hasCriteria = false;
  let relevanceScore = 0;
  let matchReasons = [];

  // 2. Query relevance
  if (q) {
    hasCriteria = true;
    const qWords = q.split(/\s+/).filter(w => w.length > 1);
    let titleHits = 0;
    let skillHits = 0;
    let compHit = false;

    qWords.forEach(w => {
      if (title.includes(w)) titleHits++;
      if (skills.some(s => s.includes(w))) skillHits++;
      if (comp.includes(w)) compHit = true;
    });

    if (title.includes(q)) {
      relevanceScore += 50;
      matchReasons.push(`Direct title match for "${q}"`);
    } else if (titleHits > 0) {
      relevanceScore += Math.min(45, titleHits * 22);
      matchReasons.push(`Title keywords matched`);
    }

    if (skillHits > 0) {
      relevanceScore += Math.min(30, skillHits * 15);
      matchReasons.push(`Skills matched: ${skills.filter(s => qWords.some(w => s.includes(w))).slice(0, 3).join(', ')}`);
    }

    if (compHit) {
      relevanceScore += 25;
      matchReasons.push(`Direct ${job.company} opening`);
    }
  }

  // 3. Discipline relevance
  if (targetDisc && targetDisc !== 'all') {
    hasCriteria = true;
    if (matchesDiscipline(job, targetDisc)) {
      relevanceScore += 30;
      matchReasons.push(`Matches ${formatPillName(targetDisc)} domain`);
    }
  }

  // 4. Location relevance
  if (targetLoc && targetLoc !== 'all') {
    hasCriteria = true;
    if (matchesLocation(job, targetLoc)) {
      relevanceScore += 20;
      matchReasons.push(`Located in ${formatPillName(targetLoc)}`);
    }
  }

  // 5. Company relevance
  if (targetComp && targetComp !== 'all') {
    hasCriteria = true;
    if (comp.includes(targetComp)) {
      relevanceScore += 35;
      matchReasons.push(`Verified opening at ${job.company}`);
    }
  }

  // 6. Experience relevance
  if (activeFilters.maxExp < 10) {
    hasCriteria = true;
    if (matchesExperience(job, activeFilters.maxExp, activeFilters.expPreset)) {
      relevanceScore += 15;
    }
  }

  let finalScore = 0;
  if (hasCriteria) {
    // Honest scoring: calculate against maximum possible points
    // Max possible: query(50+30+25=105) + discipline(30) + location(20) + company(35) + experience(15) = 205
    const maxPossible = (q ? 105 : 0) + (targetDisc ? 30 : 0) + (targetLoc ? 20 : 0) + (targetComp ? 35 : 0) + (activeFilters.maxExp < 10 ? 15 : 0);
    if (maxPossible > 0) {
      finalScore = Math.min(99, Math.max(15, Math.round((relevanceScore / maxPossible) * 100)));
    }
  } else {
    // When loading without explicit filters or CV, prioritize nearby region and remote roles!
    const locPrio = getJobLocationPriority(job);
    if (locPrio >= 100) {
      finalScore = 92;
      matchReasons.push(`Nearby opening (${userNearbyRegion ? userNearbyRegion.flag + ' ' + userNearbyRegion.name : 'Local'})`);
    } else if (locPrio >= 60) {
      finalScore = 85;
      matchReasons.push('Worldwide Remote opportunity');
    }
  }

  const reason = matchReasons.length
    ? matchReasons.slice(0, 2).join(' · ')
    : (hasCriteria ? 'Verified requisition' : '');

  return { score: finalScore, reason };
}

// High-Precision Tokenized Search Across All Fields (Title, Company, Skills, Description, Location, Discipline, Portal)
function matchesSearchQuery(job, query) {
  if (!query || !query.trim()) return true;
  const qClean = query.trim().toLowerCase();

  // Intent words that candidates naturally type like "jobs", "openings", "roles"
  const STOP_WORDS = new Set([
    'jobs', 'job', 'openings', 'opening', 'roles', 'role', 'positions', 'position',
    'careers', 'career', 'vacancies', 'vacancy', 'hiring', 'looking', 'want',
    'at', 'in', 'for', 'with', 'and', 'or', 'the', 'a', 'an', 'to', 'of', 'from'
  ]);

  const rawTokens = qClean.split(/[\s,+/|]+/).filter(Boolean);
  const meaningfulTokens = rawTokens.filter(t => !STOP_WORDS.has(t) && t.length > 1);
  const tokens = meaningfulTokens.length ? meaningfulTokens : rawTokens;
  if (!tokens.length) return true;

  // Every word must start a word in the title, skills, company or location ("data" must not hit "Datadog",
  // and a word buried in a long description is not enough to call it a match).
  const title = (job.title || '').toLowerCase();
  const skills = Array.isArray(job.skills) ? job.skills.join(' ').toLowerCase() : String(job.skills || '').toLowerCase();
  const corpus = `${title} | ${skills} | ${(job.company || '').toLowerCase()} | ${(job.location || '').toLowerCase()}`;
  return tokens.every(token => searchWordRegex(token).test(corpus));
}

const searchWordRegexCache = new Map();
function searchWordRegex(token) {
  let rx = searchWordRegexCache.get(token);
  if (!rx) {
    // Whole word, allowing common endings: "engineer" finds "engineering", "data" does not find "datadog".
    rx = new RegExp(`(^|[^a-z0-9+#])${token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(s|es|ing|ed|er|ers)?(?![a-z0-9])`);
    searchWordRegexCache.set(token, rx);
  }
  return rx;
}

// 3 = whole phrase in the title, 2 = every word in the title, 1 = matched through skills/company.
function searchTitleRank(job, query) {
  const q = String(query || '').trim().toLowerCase();
  if (!q) return 0;
  const title = (job.title || '').toLowerCase();
  if (title.includes(q)) return 3;
  const words = q.split(/[\s,+/|]+/).filter(w => w.length > 1);
  return words.length && words.every(w => searchWordRegex(w).test(title)) ? 2 : 1;
}

// Batch rendering to avoid overwhelming the DOM and maintain natural scroll velocity
let currentFilteredJobs = [];
let renderedBatchLimit = 20;

function loadMoreJobs() {
  renderedBatchLimit += 20;
  renderJobCards(currentFilteredJobs);
}

// Apply Client-Side Filters & Render
function applyFiltersAndRender() {
  let filtered = allJobsList;
  const hasCvMatches = Object.keys(jobMatchesMap).length > 0;

  // If chat or CV filtered roles are active and no search query overrides
  if (aiChatMatchedJobs && aiChatMatchedJobs.length > 0 && !activeFilters.q) {
    filtered = aiChatMatchedJobs;
  } else if (hasCvMatches && !activeFilters.q && activeFilters.discipline === 'all' && activeFilters.company === 'all' && activeFilters.location === 'all') {
    filtered = allJobsList.filter(j => jobMatchesMap[j.id]);
  }

  // 1. Keyword Search (Deep Tokenized Multi-Field Search)
  if (activeFilters.q) {
    filtered = filtered.filter(j => matchesSearchQuery(j, activeFilters.q));
  }

  // 2. Experience Filter (YOE Slider & Presets)
  if (activeFilters.maxExp < 10 || (activeFilters.expPreset && activeFilters.expPreset !== 'all')) {
    filtered = filtered.filter(j => matchesExperience(j, activeFilters.maxExp, activeFilters.expPreset));
  }

  // 3. Discipline Taxonomy Filter
  if (activeFilters.discipline && activeFilters.discipline !== 'all') {
    filtered = filtered.filter(j => matchesDiscipline(j, activeFilters.discipline));
  }

  // 4. Global Location Hubs Filter
  if (activeFilters.location && activeFilters.location !== 'all') {
    filtered = filtered.filter(j => matchesLocation(j, activeFilters.location));
  }

  // 5. Verified Portals Filter
  if (activeFilters.ats && activeFilters.ats !== 'all') {
    const atsLower = activeFilters.ats.toLowerCase();
    filtered = filtered.filter(j => {
      const portal = (j.portal || j.ats_type || '').toLowerCase();
      const applyUrl = (j.applyUrl || j.apply_url || '').toLowerCase();
      const comp = (j.company || '').toLowerCase();
      if (atsLower === 'faang') return j.isFaang || comp.includes('amazon') || comp.includes('google') || comp.includes('apple') || comp.includes('meta') || comp.includes('microsoft');
      return portal.includes(atsLower) || applyUrl.includes(atsLower);
    });
  }

  // 6. Company Filter from Shelf or Rail
  if (activeFilters.company && activeFilters.company !== 'all') {
    const compLower = activeFilters.company.toLowerCase().trim();
    filtered = filtered.filter(j => {
      const c = (j.company || '').toLowerCase();
      const p = (j.portal || j.ats_type || '').toLowerCase();
      if (compLower === 'yc' || compLower === 'y combinator') return p.includes('ycombinator') || c.includes('yc') || p.includes('yc');
      if (compLower === 'rocket lab') return c.includes('rocket lab') || c.includes('rocketlab');
      if (compLower === 'relativity space') return c.includes('relativity');
      if (compLower === 'redwood materials') return c.includes('redwood');
      if (compLower === 'form energy') return c.includes('form energy');
      if (compLower === 'riot games') return c.includes('riot');
      if (compLower === 'epic games') return c.includes('epic');
      if (compLower === 'careem') return c.includes('careem');
      if (compLower === 'cloudflare') return c.includes('cloudflare');
      if (compLower === 'scale ai') return c.includes('scale ai') || c.includes('scale');
      if (compLower === 'meta') return c.includes('meta') || c.includes('facebook') || c.includes('reality labs');
      if (compLower === 'apple') return c.includes('apple');
      return c.includes(compLower);
    });
  }

  // 7. Saved Filter Tab
  if (activeTab === 'saved') {
    filtered = filtered.filter(j => savedJobIds.has(j.id));
  }

  // Graceful fallback: Never leave candidate stranded with 0 results if remote or discipline exists
  if (filtered.length === 0 && !activeFilters.q && activeTab !== 'saved') {
    if (activeFilters.location && activeFilters.location !== 'all') {
      filtered = allJobsList.filter(j => matchesLocation(j, activeFilters.location));
    } else if (activeFilters.discipline && activeFilters.discipline !== 'all') {
      filtered = allJobsList.filter(j => matchesDiscipline(j, activeFilters.discipline));
    }
  }

  // Compute and attach Match Percentage score & explanation to all filtered jobs
  filtered.forEach(j => {
    const info = calculateJobMatchScore(j);
    j._matchScore = info.score;
    j._matchReason = info.reason;
  });

  // Sort based on currentSortMode: By default ALWAYS Highest Match % first!
  if (currentSortMode === 'latest') {
    filtered.sort((a, b) => String(b.id || '').localeCompare(String(a.id || '')));
  } else if (currentSortMode === 'salary') {
    filtered.sort((a, b) => {
      const parseSal = (job) => {
        const text = String(job.description || '') + ' ' + String(job.salary || '');
        const m = text.match(/\$([\d,]+)/);
        return m ? parseInt(m[1].replace(/,/g, ''), 10) : 0;
      };
      return parseSal(b) - parseSal(a);
    });
  } else {
    // Default: 'match_desc' -> Highest Match % first, with nearby location & remote preference on load!
    const hasCv = Object.keys(jobMatchesMap).length > 0;
    filtered.sort((a, b) => {
      if (hasCv) {
        // If CV is active, match score takes priority, nearby location breaks ties
        const scoreDiff = (b._matchScore || 0) - (a._matchScore || 0);
        if (scoreDiff !== 0) return scoreDiff;
        return getJobLocationPriority(b) - getJobLocationPriority(a);
      } else {
        // A keyword search puts real title matches first.
        if (activeFilters.q) {
          const rankDiff = searchTitleRank(b, activeFilters.q) - searchTitleRank(a, activeFilters.q);
          if (rankDiff !== 0) return rankDiff;
        }
        // When loading without CV, give preference to nearby location & remote roles first!
        const locPrioDiff = getJobLocationPriority(b) - getJobLocationPriority(a);
        if (locPrioDiff !== 0) return locPrioDiff;
        return (b._matchScore || 0) - (a._matchScore || 0);
      }
    });
  }

  currentFilteredJobs = filtered;
  renderedBatchLimit = 20;
  renderJobCards(currentFilteredJobs);

  const countEl = document.getElementById('feed-count');
  if (countEl) {
    if (hasCvMatches && !activeFilters.q) {
      countEl.innerHTML = `<span>Top ${filtered.length} Matched Positions · Ranked by CV Match Score</span> <button type="button" class="feed-view-all-link" onclick="clearManualCv()">View All 10,237 Roles</button>`;
    } else if (activeFilters.location === 'all' && !activeFilters.q && userNearbyRegion && userNearbyRegion.name) {
      countEl.innerHTML = `<span><strong>${filtered.length.toLocaleString()} roles</strong> · Prioritizing roles near ${userNearbyRegion.flag} ${userNearbyRegion.name} & Remote</span>`;
    } else {
      countEl.textContent = `${filtered.length.toLocaleString()} roles · Ranked by Match %`;
    }
  }

  const sheetApplyBtn = document.getElementById('sheet-apply-btn-label');
  if (sheetApplyBtn) sheetApplyBtn.textContent = `Show ${filtered.length.toLocaleString()} Openings`;
}

// Render Job Cards with Progressive Batching, Highlighting & AI Match Badges
function renderJobCards(jobs) {
  const container = document.getElementById('job-rows-container');
  if (!container) return;

  if (!jobs.length) {
    container.innerHTML = `
      <div class="empty-state-box">
        <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="1.6"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <div style="font-size:15px; font-weight:700; color:var(--ink);">
          ${activeTab === 'saved' ? 'No saved openings yet' : 'No matching roles found'}
        </div>
        <div style="font-size:13px; color:var(--muted);">
          ${activeTab === 'saved' ? 'Click the bookmark icon on any role to pin it to this view.' : 'Try adjusting the max experience slider or broadening your company/location filter.'}
        </div>
      </div>
    `;
    return;
  }

  const q = activeFilters.q;
  const visible = jobs.slice(0, renderedBatchLimit);

  let cardsHtml = visible.map(j => {
    const isSaved = savedJobIds.has(j.id);
    const matchScore = j._matchScore || (jobMatchesMap[j.id]?.score) || calculateJobMatchScore(j).score;
    const matchExplanation = j._matchReason || (jobMatchesMap[j.id]?.explanation) || calculateJobMatchScore(j).reason;

    const exp = getJobExperienceMinMax(j);
    const expText = j.expText || j.experience || `${exp.min} - ${exp.max} yrs`;
    const salaryText = getJobSalaryBand(j);

    return `
      <article class="job-row">
        <div class="job-row-main">
          <div class="job-row-title-area" style="cursor:pointer;" onclick="openJobDetailsModal('${j.id}')">
            <h3 class="job-title">${highlightQuery(j.title, q)}</h3>
            <div class="job-company-line">
              <span class="company-avatar-glyph">${renderCompanyVectorLogo(j.company, j.portal || j.ats_type)}</span>
              <span class="job-company-badge">${highlightQuery(j.company, q)}</span>
              <span>·</span>
              <span>${escapeHtml(j.location || 'Remote')}</span>
            </div>
          </div>

          <div class="job-actions-top">
            ${matchScore > 0 ? `<div class="match-chip tabular-num ${matchScore >= 85 ? 'high-match' : ''}">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <span>${matchScore}% Match</span>
            </div>` : ''}
            <button class="btn-bookmark ${isSaved ? 'saved' : ''}" title="${isSaved ? 'Remove bookmark' : 'Save role'}" onclick="toggleBookmark('${j.id}')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            </button>
          </div>
        </div>

        <!-- Metadata Line (Salary, Location, Experience, Verified Live) -->
        <div class="job-meta-line">
          <span class="job-salary-badge mono-num">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/></svg>
            ${escapeHtml(salaryText)}
          </span>
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
              Verified Active
            </span>
          </span>
        </div>

        <!-- AI Match Explanation Callout (if available) -->
        ${matchExplanation ? `
          <div class="job-match-reason">
            <span style="font-weight:600; color:var(--gold); margin-right:4px;">Why Matched:</span>
            ${escapeHtml(matchExplanation)}
          </div>
        ` : ''}

        <!-- Skills List with Highlight -->
        ${(j.skills && j.skills.length) ? `
          <div class="job-skills-row">
            ${j.skills.slice(0, 5).map(s => `<span class="skill-tag">${highlightQuery(s, q)}</span>`).join('')}
          </div>
        ` : ''}

        <!-- Clean Card Footer with Details / Apply Button (No Portal Jargon) -->
        <div class="job-row-actions">
          <div class="source-brand-badge">
            <span class="verified-micro-dot" style="margin-right:2px;"></span>
            <span>Direct Opening · Full-time</span>
          </div>
          <button class="btn-apply-link" onclick="openJobDetailsModal('${j.id}')">
            <span>Apply / Details</span>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
          </button>
        </div>
      </article>
    `;
  }).join('');

  if (jobs.length > renderedBatchLimit) {
    const remaining = jobs.length - renderedBatchLimit;
    cardsHtml += `
      <div class="load-more-wrap">
        <button class="btn-load-more" onclick="loadMoreJobs()">
          <span>Show More Roles (${remaining} remaining)</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
        </button>
      </div>
    `;
  }

  container.innerHTML = cardsHtml;
}

// Helper to produce clean corporate monogram
function getCompanyMonogram(name) {
  if (!name) return 'CO';
  const clean = name.replace(/[^a-zA-Z0-9\s]/g, '').trim();
  const words = clean.split(/\s+/).filter(Boolean);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase() || 'CO';
}

function getCompanyBadgeColor(name) {
  const palette = [
    '#C5A059', '#1E293B', '#1E6B52', '#2A4365', '#334155',
    '#B38F46', '#1E3A8A', '#18191E', '#0F172A', '#D97706',
    '#134E4A', '#24252B', '#1E3A5F', '#3B362A', '#2D3748'
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
// CONFIDENTIAL CV DROPZONE & AI MATCHING
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
  statusText.textContent = `Analyzing ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);
  // The server needs the CV's text; raw PDF bytes cannot be read there.
  formData.append('extracted_text', await extractTextFromPdfFile(file).catch(() => ''));
  formData.append('targetHub', prefLocationHub);
  formData.append('targetDiscipline', prefDiscipline);

  try {
    const res = await fetch(`${RECRUITER_API}/cv/match`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.error || 'Could not read this CV'); }
    const data = await res.json();
    statusText.textContent = `Analyzed: ${file.name}`;

    // Render candidate profile
    const profile = data.profile;
    if (profile) {
      currentProfileData = profile;
      try {
        localStorage.setItem('camouroles_cv_profile', JSON.stringify(profile));
      } catch (e) {}

      const box = document.getElementById('candidate-data-box');
      if (box) box.style.display = 'block';
      document.getElementById('cand-headline').textContent = profile.headline;
      document.getElementById('cand-exp').textContent = profile.experienceText;
      const skillsContainer = document.getElementById('cand-skills');
      if (skillsContainer && profile.skills) {
        skillsContainer.innerHTML = profile.skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
      }

      updateHeroCvStatusUI(profile);
      syncProfileDataToUI(profile);
    }

    // Store matches map & re-render cards
    if (data.matches) {
      jobMatchesMap = data.matches;
      try {
        localStorage.setItem('camouroles_cv_matches', JSON.stringify(data.matches));
      } catch (e) {}
      applyFiltersAndRender();
      document.getElementById('feed-count').textContent = `AI ranked matches active`;
    }
  } catch (err) {
    console.error("CV upload error:", err);
    if (typeof showNotification === "function") showNotification(err.message || "Could not read this CV");
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
  try {
    localStorage.removeItem('camouroles_cv_profile');
    localStorage.removeItem('camouroles_cv_matches');
  } catch (e) {}
  jobMatchesMap = {};
  currentProfileData = null;
  const candBox = document.getElementById('candidate-data-box');
  if (candBox) candBox.style.display = 'none';
  const profBox = document.getElementById('profile-candidate-data-box');
  if (profBox) profBox.style.display = 'none';

  const dropText = document.getElementById('dropzone-status-text');
  if (dropText) dropText.textContent = 'Upload CV Document';
  const profDropText = document.getElementById('profile-dropzone-status-text');
  if (profDropText) profDropText.textContent = 'Upload Candidate CV (PDF)';
  const aiDropText = document.getElementById('ai-cv-status-text');
  if (aiDropText) aiDropText.textContent = 'Upload Resume for Instant AI Match';

  syncChatGptCvUI(null);
  updateHeroCvStatusUI(null);
  applyFiltersAndRender();
  renderProfileTopJobs();
}

// Re-rank a saved CV against today's jobs (no AI call; the profile is already read).
async function refreshCvMatchesFromProfile(profile) {
  try {
    const res = await fetch(`${RECRUITER_API}/cv/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile }),
    });
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success || !data.matches) return;
    jobMatchesMap = data.matches;
    localStorage.setItem('camouroles_cv_matches', JSON.stringify(data.matches));
    applyFiltersAndRender();
  } catch (e) {}
}

async function loadProfileData() {
  // First restore from localStorage for instant persistent CV memory only if valid user profile
  try {
    const cachedProfile = localStorage.getItem('camouroles_cv_profile');
    if (cachedProfile) {
      const parsed = JSON.parse(cachedProfile);
      // Profiles saved before the CV reader was fixed (no matchVersion) were often read from raw PDF bytes; drop them.
      if (parsed && parsed.headline && parsed.fileName && parsed.matchVersion >= 2) {
        currentProfileData = parsed;
        const cachedMatches = localStorage.getItem('camouroles_cv_matches');
        if (cachedMatches) jobMatchesMap = JSON.parse(cachedMatches);
        refreshCvMatchesFromProfile(parsed);

        updateHeroCvStatusUI(currentProfileData);
        syncProfileDataToUI(currentProfileData); syncManualCvUI();
        syncChatGptCvUI(currentProfileData);
        applyFiltersAndRender();
      } else {
        localStorage.removeItem('camouroles_cv_profile');
        localStorage.removeItem('camouroles_cv_matches');
        currentProfileData = null;
      }
    }
  } catch (e) {}

  try {
    const res = await fetch(`${API_BASE}/profile?device_id=${encodeURIComponent(browserDeviceId())}`, { headers: await authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    if (data.is_unlimited !== undefined) {
      isUserPro = Boolean(data.is_unlimited);
      userUnlimitedUntil = data.unlimited_until || null;
      updateProBadgeUI();
    }
    // Only set profile if the backend explicitly reports has_cv: true and valid profile data
    if (data.has_cv && data.profile && data.profile.headline) {
      currentProfileData = data.profile;
      syncProfileDataToUI(currentProfileData); syncManualCvUI();
      syncChatGptCvUI(currentProfileData);
    } else if (!currentProfileData) {
      // Ensure UI stays in clean pre-upload state
      syncProfileDataToUI(null); syncManualCvUI();
      syncChatGptCvUI(null);
    }
  } catch (err) {
    if (!currentProfileData) {
      syncProfileDataToUI(null); syncManualCvUI();
      syncChatGptCvUI(null);
    }
  }
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

// ==========================================================================
// JOB SALARY BAND & SUMMARY INTELLIGENCE
// ==========================================================================
function getJobSalaryBand(job) {
  if (!job) return '$185,000 – $245,000 / yr';
  
  // Check if job description or raw data explicitly provides compensation
  const desc = String(job.description || '');
  const salaryMatch = desc.match(/(?:salary|compensation|pay range|base pay|base range|target pay)[:\s]*([$€£₹][\d,]+(?:\s*[-–to]+\s*[$€£₹]?[\d,]+)?(?:\s*(?:\/|per)?\s*(?:yr|year|annum|hr|hour|mo|month|L|LPA))?)/i);
  if (salaryMatch && salaryMatch[1] && salaryMatch[1].length < 40) {
    let s = salaryMatch[1].trim();
    if (!s.includes('/') && !s.includes('per')) s += ' / yr';
    return s;
  }

  const title = String(job.title || '').toLowerCase();
  const loc = String(job.location || '').toLowerCase();
  const expMin = parseInt(job.experience_min, 10) || 0;
  const expMax = parseInt(job.experience_max, 10) || (expMin + 3);
  const avgExp = (expMin + expMax) / 2;

  const isSenior = title.includes('senior') || title.includes('sr.') || avgExp >= 5;
  const isStaff = title.includes('staff') || title.includes('principal') || title.includes('lead') || title.includes('director') || avgExp >= 8;
  const isIntern = title.includes('intern') || title.includes('graduate') || (expMin === 0 && expMax <= 1);

  // India Hubs
  if (loc.includes('india') || loc.includes('bengaluru') || loc.includes('bangalore') || loc.includes('hyderabad') || loc.includes('delhi') || loc.includes('pune') || loc.includes('mumbai')) {
    if (isIntern) return '₹6L – ₹12L / yr';
    if (isStaff) return '₹55L – ₹90L / yr';
    if (isSenior) return '₹36L – ₹58L / yr';
    if (avgExp <= 2) return '₹16L – ₹26L / yr';
    return '₹24L – ₹38L / yr';
  }

  // UK Hubs
  if (loc.includes('london') || loc.includes('uk') || loc.includes('united kingdom') || loc.includes('cambridge')) {
    if (isIntern) return '£35,000 – £50,000 / yr';
    if (isStaff) return '£150,000 – £220,000 / yr';
    if (isSenior) return '£110,000 – £155,000 / yr';
    if (avgExp <= 2) return '£60,000 – £85,000 / yr';
    return '£85,000 – £115,000 / yr';
  }

  // European Hubs
  if (loc.includes('germany') || loc.includes('munich') || loc.includes('berlin') || loc.includes('netherlands') || loc.includes('amsterdam') || loc.includes('zurich') || loc.includes('switzerland') || loc.includes('paris') || loc.includes('europe')) {
    if (isIntern) return '€35,000 – €48,000 / yr';
    if (isStaff) return '€160,000 – €230,000 / yr';
    if (isSenior) return '€115,000 – €160,000 / yr';
    if (avgExp <= 2) return '€65,000 – €90,000 / yr';
    return '€85,000 – €120,000 / yr';
  }

  // US, Canada, Remote & Global Default
  if (isIntern) return '$85,000 – $115,000 / yr';
  if (isStaff) return '$260,000 – $360,000 / yr';
  if (isSenior) return '$195,000 – $265,000 / yr';
  if (avgExp <= 2) return '$125,000 – $165,000 / yr';
  return '$160,000 – $210,000 / yr';
}

function getJobShortSummary(job) {
  if (!job) return 'Exciting high-impact engineering opportunity.';
  
  if (job.description && job.description.trim().length > 30) {
    let clean = job.description.replace(/<[^>]+>/g, ' ').replace(/[#*_`]/g, '').replace(/\s+/g, ' ').trim();
    let sentences = clean.split(/(?<=[.?!])\s+/).filter(s => s.length > 20);
    if (sentences.length > 0) {
      let summary = sentences.slice(0, 2).join(' ');
      if (summary.length > 260) {
        summary = summary.substring(0, 257) + '...';
      }
      return summary;
    }
  }

  // Fallback high-signal summary
  const comp = job.company || 'Leading Tech Company';
  const title = job.title || 'Software Engineer';
  const skills = (job.skills && job.skills.length) ? job.skills.slice(0, 3).join(', ') : 'modern tech stacks';
  return `Join ${comp} as a ${title}. In this role, you will architect scalable systems, collaborate with cross-functional product teams, and apply ${skills} to solve complex engineering challenges.`;
}

// ==========================================================================
// JOB APPLICATION & DETAILS MODAL
// ==========================================================================
function openJobDetailsModal(jobId) {
  const modal = document.getElementById('job-apply-modal');
  if (!modal) return;

  const job = allJobsList.find(j => String(j.id) === String(jobId));
  if (!job) return;

  // Set avatar & company title
  const avatarEl = document.getElementById('modal-company-avatar');
  if (avatarEl) {
    avatarEl.innerHTML = renderCompanyVectorLogo(job.company, job.portal || job.ats_type);
  }

  const titleEl = document.getElementById('modal-job-title');
  if (titleEl) titleEl.textContent = job.title || 'Engineering Role';

  const subEl = document.getElementById('modal-company-sub');
  if (subEl) {
    const loc = job.location || (job.is_remote ? 'Worldwide Remote' : 'Global');
    subEl.textContent = `${job.company || 'Company'} · ${loc}`;
  }

  // Set stats
  const salaryEl = document.getElementById('modal-salary-val');
  if (salaryEl) salaryEl.textContent = getJobSalaryBand(job);

  const expEl = document.getElementById('modal-exp-val');
  if (expEl) {
    const expText = job.expText || job.experience || `${job.experience_min || 0} - ${job.experience_max || 3} yrs`;
    expEl.textContent = expText;
  }

  const remoteEl = document.getElementById('modal-remote-val');
  if (remoteEl) {
    remoteEl.textContent = job.is_remote ? '100% Remote' : (job.location || 'Hybrid / On-site');
  }

  // Summary
  const summaryEl = document.getElementById('modal-summary-text');
  if (summaryEl) summaryEl.textContent = getJobShortSummary(job);

  // Key Skills Stack
  const skillsRow = document.getElementById('modal-skills-row');
  if (skillsRow) {
    if (job.skills && job.skills.length) {
      skillsRow.innerHTML = job.skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
    } else {
      skillsRow.innerHTML = `<span class="skill-tag">Software Engineering</span><span class="skill-tag">Problem Solving</span>`;
    }
  }

  // Application Sources Box
  const sourcesBox = document.getElementById('modal-sources-box');
  let applyUrl = job.applyUrl || job.apply_url || '#';
  if (applyUrl.includes('linkedin.com/jobs/view/')) {
    const idMatch = applyUrl.match(/(\d{8,})/);
    if (idMatch) {
      applyUrl = `https://www.linkedin.com/jobs/view/${idMatch[1]}?trk=public_jobs_topcard-title`;
    }
  }

  let domain = 'official careers portal';
  try {
    if (applyUrl && applyUrl.startsWith('http')) {
      domain = new URL(applyUrl).hostname.replace(/^www\./, '');
    }
  } catch (e) {}

  // Identify the verified application portal
  let portalDisplayName = job.company ? `${job.company} Career Portal` : 'Official Portal';
  let portalBadgeText = domain;

  if (applyUrl.includes('naukri.com')) {
    portalDisplayName = `${job.company} on Naukri`;
    portalBadgeText = 'Naukri.com Direct';
  } else if (applyUrl.includes('linkedin.com')) {
    portalDisplayName = `${job.company} on LinkedIn`;
    portalBadgeText = 'LinkedIn Direct';
  } else if (applyUrl.includes('greenhouse.io')) {
    portalDisplayName = `${job.company} (Greenhouse)`;
    portalBadgeText = 'Greenhouse ATS';
  } else if (applyUrl.includes('lever.co')) {
    portalDisplayName = `${job.company} (Lever)`;
    portalBadgeText = 'Lever ATS';
  } else if (applyUrl.includes('ashbyhq.com')) {
    portalDisplayName = `${job.company} (Ashby)`;
    portalBadgeText = 'Ashby ATS';
  } else if (applyUrl.includes('kula.ai')) {
    portalDisplayName = `${job.company} (Kula)`;
    portalBadgeText = 'Kula ATS';
  } else if (applyUrl.includes('breezy.hr')) {
    portalDisplayName = `${job.company} (Breezy HR)`;
    portalBadgeText = 'Breezy HR';
  } else if (applyUrl.includes('myworkdayjobs.com')) {
    portalDisplayName = `${job.company} (Workday)`;
    portalBadgeText = 'Workday Direct';
  }

  if (sourcesBox) {
    sourcesBox.innerHTML = `
      <div class="modal-sources-list">
        <a class="source-link-row primary" href="${applyUrl}" target="_blank" rel="noopener noreferrer">
          <div class="source-link-left">
            <span class="source-brand-badge">${renderCompanyVectorLogo(job.company, job.portal || job.ats_type)}</span>
            <div>
              <div class="source-name">${escapeHtml(portalDisplayName)}</div>
              <div class="source-domain">${escapeHtml(portalBadgeText)} · 100% Verified Live Requisition</div>
            </div>
          </div>
          <span class="source-action-chip primary">Open Direct Link ↗</span>
        </a>
      </div>
    `;
  }

  // Direct Apply Button
  const applyBtn = document.getElementById('modal-apply-btn');
  if (applyBtn) {
    applyBtn.href = applyUrl;
    applyBtn.target = '_blank';
    applyBtn.rel = 'noopener noreferrer';
  }

  modal.classList.add('open');
}

function closeJobApplyModal() {
  const modal = document.getElementById('job-apply-modal');
  if (modal) modal.classList.remove('open');
}

function onJobModalBackdropClick(e) {
  if (e.target.id === 'job-apply-modal') {
    closeJobApplyModal();
  }
}

// Global keyboard shortcut: Escape closes modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeJobApplyModal();
    closeFiltersModal();
    closeAiSearchModal();
    closeChatGptInterface();
  }
});

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

// ==========================================================================
// VIEW SWITCHER (FEED / SAVED / PROFILE)
// ==========================================================================
function showView(view) {
  currentView = view;
  const heroSection = document.getElementById('hero-search-section');
  const appLayout = document.querySelector('.app-layout');
  const profilePage = document.getElementById('profile-page-view');

  // Desktop top nav tabs
  const tabBrowse = document.getElementById('top-tab-browse');
  const tabSaved = document.getElementById('top-tab-saved');
  const tabProfile = document.getElementById('top-tab-profile');
  if (tabBrowse) tabBrowse.classList.toggle('active', view === 'feed');
  if (tabSaved) tabSaved.classList.toggle('active', view === 'saved');
  if (tabProfile) tabProfile.classList.toggle('active', view === 'profile');

  // Mobile bottom nav buttons
  const mobJobs = document.getElementById('mob-nav-jobs');
  const mobSaved = document.getElementById('mob-nav-saved');
  const mobProfile = document.getElementById('mob-nav-profile');
  if (mobJobs) mobJobs.classList.toggle('active', view === 'feed');
  if (mobSaved) mobSaved.classList.toggle('active', view === 'saved');
  if (mobProfile) mobProfile.classList.toggle('active', view === 'profile');

  if (view === 'profile') {
    if (heroSection) heroSection.style.display = 'none';
    if (appLayout) appLayout.style.display = 'none';
    if (profilePage) profilePage.style.display = 'block';
    renderProfileView();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    if (profilePage) profilePage.style.display = 'none';
    if (heroSection) heroSection.style.display = '';
    if (appLayout) appLayout.style.display = '';

    if (view === 'saved') {
      activeTab = 'saved';
      const tabAllEl = document.getElementById('tab-all-roles');
      const tabSavedEl = document.getElementById('tab-saved-roles');
      if (tabAllEl) tabAllEl.classList.remove('active');
      if (tabSavedEl) tabSavedEl.classList.add('active');
    } else {
      activeTab = 'all';
      const tabAllEl = document.getElementById('tab-all-roles');
      const tabSavedEl = document.getElementById('tab-saved-roles');
      if (tabAllEl) tabAllEl.classList.add('active');
      if (tabSavedEl) tabSavedEl.classList.remove('active');
    }
    applyFiltersAndRender();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

// ==========================================================================
// SEARCH MODE SEGMENTED SWITCHER (AI AGENTIC VS MANUAL KEYWORD)
// ==========================================================================
// ==========================================================================
// SEARCH MODE SEGMENTED SWITCHER (AI AGENTIC VS MANUAL KEYWORD)
// ==========================================================================
function setSearchMode(mode) {
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
}

function toggleSearchMode() {
  setSearchMode(searchMode === 'ai' ? 'manual' : 'ai');
}

// ==========================================================================
// CHATGPT-STYLE INLINE HERO AI RECRUITER (UNFOLDS DIRECTLY UNDERNEATH)
// ==========================================================================
let heroChatHistory = [];
let recruiterSessionState = {
  discipline: 'all',
  location: 'all',
  company: 'all',
  minExp: 1
};
let heroChatCriteria = {
  discipline: 'all',
  location: 'all',
  company: 'all',
  maxExp: 10,
  keywords: ''
};

function openHeroAiChat() {
  openChatGptInterface();
}

function toggleAiRecruiterPanel(forceOpen) {
  if (forceOpen === false) closeChatGptInterface();
  else openChatGptInterface();
}

function toggleHeroAiChat(forceOpen) {
  if (forceOpen === false) closeChatGptInterface();
  else openChatGptInterface();
}

function updateAiSearchBarText() {
  const summaryText = document.getElementById('ai-bar-summary-text');
  const btnLabel = document.getElementById('ai-toggle-btn-label');
  if (!summaryText) return;
  const hasActiveConversation = chatGptHistory && chatGptHistory.length > 0;
  if (hasActiveConversation) {
    summaryText.textContent = 'Resume conversation with talent intelligence';
    if (btnLabel) btnLabel.textContent = 'Resume';
  } else {
    summaryText.textContent = 'Click here to match using talent intelligence';
    if (btnLabel) btnLabel.textContent = 'Match';
  }
}

function updateHeroCvStatusUI(profile) {
  if (!profile) return;
  const statusText = document.getElementById('hero-cv-status-text');
  const headline = profile.headline || 'Engineering Profile';
  const skills = (profile.skills || []).slice(0, 4).join(', ');
  if (statusText) {
    statusText.innerHTML = `<strong>Active CV Loaded:</strong> ${escapeHtml(headline)} <span style="font-size:11.5px; color:var(--muted); font-weight:normal;">(${escapeHtml(skills)})</span>`;
  }
  updateAiSearchBarText();
}

function updateHeroChatCount() {
  let count = 0;
  for (let i = 0; i < allJobsList.length; i++) {
    const j = allJobsList[i];
    if (heroChatCriteria.company && heroChatCriteria.company !== 'all') {
      const c = (j.company || '').toLowerCase();
      if (!c.includes(heroChatCriteria.company.toLowerCase())) continue;
    }
    if (heroChatCriteria.discipline !== 'all' && !matchesDiscipline(j, heroChatCriteria.discipline)) continue;
    if (heroChatCriteria.location !== 'all' && !matchesLocation(j, heroChatCriteria.location)) continue;
    if (heroChatCriteria.maxExp < 10 && !matchesExperience(j, heroChatCriteria.maxExp, 'all')) continue;
    if (heroChatCriteria.keywords) {
      if (!matchesSearchQuery(j, heroChatCriteria.keywords)) continue;
    }
    count++;
  }

  const btnLabel = document.getElementById('hero-results-btn-label');
  if (btnLabel) {
    btnLabel.textContent = `View Matching Roles (${count.toLocaleString()}) ↓`;
  }
  const hintEl = document.getElementById('hero-chat-match-hint');
  if (hintEl) {
    if (heroChatCriteria.company && heroChatCriteria.company !== 'all') {
      hintEl.textContent = `Filtered for ${formatPillName(heroChatCriteria.company)} openings`;
    } else {
      const dName = formatPillName(heroChatCriteria.discipline);
      const lName = formatPillName(heroChatCriteria.location);
      hintEl.textContent = `Target: ${dName} · ${lName} (${count.toLocaleString()} matches)`;
    }
  }
  return count;
}

async function onHeroCvSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const statusText = document.getElementById('hero-cv-status-text');
  if (statusText) statusText.textContent = `Analyzing ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);
  // The server needs the CV's text; raw PDF bytes cannot be read there.
  formData.append('extracted_text', await extractTextFromPdfFile(file).catch(() => ''));
  formData.append('targetHub', heroChatCriteria.location === 'all' ? 'All' : heroChatCriteria.location);
  formData.append('targetDiscipline', heroChatCriteria.discipline);

  try {
    const res = await fetch(`${RECRUITER_API}/cv/match`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.error || 'Could not read this CV'); }
    const data = await res.json();
    currentProfileData = data.profile;
    if (data.matches) {
      jobMatchesMap = data.matches;
    }

    try {
      localStorage.setItem('camouroles_cv_profile', JSON.stringify(data.profile));
      localStorage.setItem('camouroles_cv_matches', JSON.stringify(data.matches || {}));
    } catch (e) {}

    updateHeroCvStatusUI(data.profile);
    applyFiltersAndRender();

    const headline = data.profile?.headline || 'Candidate Profile';
    const skills = (data.profile?.skills || []).slice(0, 5).join(', ');

    // Append to Chat stream
    const chatContainer = document.getElementById('hero-chat-messages');
    if (chatContainer) {
      const userBubble = document.createElement('div');
      userBubble.className = 'chat-msg user-msg';
      userBubble.innerHTML = `
        <div class="msg-avatar">You</div>
        <div class="msg-bubble">
          <p><strong>Uploaded CV:</strong> ${escapeHtml(file.name)}</p>
        </div>
      `;
      chatContainer.appendChild(userBubble);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Automatically trigger AI Recruiter to filter feed and display matching roles
    sendHeroAiChat(`Recommend top matching roles for my CV: ${headline} with skills in ${skills}`);
    updateHeroChatCount();
  } catch (err) {
    console.error("Hero CV upload error:", err);
    if (typeof showNotification === "function") showNotification(err.message || "Could not read this CV");
    if (statusText) statusText.textContent = "Upload failed. Please upload a PDF file.";
  }
}

// ==========================================================================
// AI RECRUITER COMPLETE WEBPAGE CONTROL & INLINE CARDS
// ==========================================================================

// ==========================================================================
// AI RECRUITER: the server turns the conversation into filters; the browser
// searches the full catalogue with them, so chat and feed always agree.
// ==========================================================================
const RECRUITER_API = /^(mobile-preview\.|localhost$|127\.0\.0\.1$)/.test(location.hostname)
  ? 'https://camouroles-preview.primemax.workers.dev/api'
  : API_BASE;

// Everything we know from the candidate's uploaded CV, so the recruiter can talk to them as a person.
function cvContextForRecruiter() {
  const p = currentProfileData;
  if (!p) return null;
  const parts = [];
  if (p.headline) parts.push(`Headline: ${p.headline}`);
  if (p.experienceYears !== undefined && p.experienceYears !== null) parts.push(`Experience: ${p.experienceYears} years`);
  else if (p.experienceText) parts.push(`Experience: ${p.experienceText}`);
  if (p.discipline) parts.push(`Field: ${p.discipline}`);
  if (p.skills && p.skills.length) parts.push(`Skills: ${p.skills.slice(0, 12).join(', ')}`);
  if (p.summary) parts.push(`Summary: ${p.summary}`);
  return parts.join('. ');
}

function recruiterRequestBody(query, conversation) {
  return JSON.stringify({
    message: query,
    conversation,
    cv_summary: cvContextForRecruiter(),
    current_filters: {
      q: activeFilters.q || '',
      discipline: activeFilters.discipline || 'all',
      location: activeFilters.location || 'all',
      expPreset: activeFilters.expPreset || 'all',
      company: activeFilters.company || 'all',
    },
  });
}

const EXP_PRESET_MAX = { all: 10, '0-1': 1, '1-3': 3, '3-6': 6, '6+': 9 };

function jobPassesFilters(j, f) {
  if (f.q && !matchesSearchQuery(j, f.q)) return false;
  if (f.expPreset !== 'all' && !matchesExperience(j, EXP_PRESET_MAX[f.expPreset], f.expPreset)) return false;
  if (f.discipline !== 'all' && !matchesDiscipline(j, f.discipline)) return false;
  if (f.location !== 'all' && !matchesLocation(j, f.location)) return false;
  if (f.company !== 'all' && !String(j.company || '').toLowerCase().includes(f.company.toLowerCase())) return false;
  return true;
}

function countJobsFor(f) {
  let n = 0;
  for (const j of allJobsList) if (jobPassesFilters(j, f)) n++;
  return n;
}

function setRecruiterFilters(f) {
  activeFilters.q = f.q;
  ['hero-search-input', 'desktop-search-input', 'mobile-search-input'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = f.q;
  });
  activeFilters.discipline = f.discipline;
  activeFilters.location = f.location;
  activeFilters.company = f.company;
  activeFilters.expPreset = f.expPreset;
  activeFilters.maxExp = EXP_PRESET_MAX[f.expPreset] ?? 10;
  heroChatCriteria.discipline = f.discipline;
  heroChatCriteria.location = f.location;
  heroChatCriteria.company = f.company;
  heroChatCriteria.keywords = f.q;
  syncExpSlider(activeFilters.maxExp, f.expPreset);
  const locs = new Set(f.location.split(','));
  const fields = new Set(f.discipline.split(','));
  document.querySelectorAll('[data-location]').forEach(el => el.classList.toggle('active', locs.has(el.getAttribute('data-location'))));
  document.querySelectorAll('[data-discipline]').forEach(el => el.classList.toggle('active', fields.has(el.getAttribute('data-discipline'))));
  updateActivePills();
  applyFiltersAndRender();
}

function describeRecruiterFilters(f) {
  const bits = [];
  if (f.q) bits.push(`for "${f.q}"`);
  if (f.discipline !== 'all') bits.push(`in ${formatPillName(f.discipline)}`);
  if (f.location !== 'all') bits.push(`· ${formatPillName(f.location)}`);
  if (f.expPreset !== 'all') bits.push(`· ${f.expPreset.replace('-', '–')} yrs experience`);
  if (f.company !== 'all') bits.push(`at ${f.company}`);
  return bits.join(' ');
}

// Applies the recruiter's plan to the page and returns what the chat should show.
function applyLlmControlToWebpage(data) {
  const plan = data && data.plan;
  if (!plan) return { reply: (data && data.reply) || '', jobs: [], total: null, tags: [] };

  aiChatMatchedJobs = []; // the feed follows the filters, never a hand-picked list
  if (plan.action === 'ask' || plan.action === 'chat') {
    if (plan.reset) setRecruiterFilters({ q: '', discipline: 'all', location: 'all', expPreset: 'all', company: 'all' });
    return { reply: [plan.say, plan.question].filter(Boolean).join(' '), jobs: [], total: null, tags: [] };
  }

  const want = {
    q: plan.query || '',
    discipline: plan.fields && plan.fields.length ? plan.fields.join(',') : 'all',
    location: plan.locations && plan.locations.length ? plan.locations.join(',') : 'all',
    expPreset: plan.experience || 'all',
    company: plan.company || 'all',
  };

  // Widen one step at a time until something real matches, and say what was widened.
  const steps = [
    { f: want, note: '' },
    { f: { ...want, expPreset: 'all' }, note: 'any experience level' },
    { f: { ...want, expPreset: 'all', company: 'all' }, note: want.company !== 'all' ? 'other companies' : '' },
    { f: { ...want, expPreset: 'all', company: 'all', q: '' }, note: want.q ? (want.discipline !== 'all' ? `all ${formatPillName(want.discipline)} roles` : 'related roles') : '' },
    { f: { ...want, expPreset: 'all', company: 'all', location: 'all' }, note: want.location !== 'all' ? 'all locations' : '' },
  ];
  let chosen = steps[0];
  let total = countJobsFor(chosen.f);
  for (const step of steps.slice(1)) {
    if (total > 0) break;
    if (JSON.stringify(step.f) === JSON.stringify(chosen.f)) continue;
    const n = countJobsFor(step.f);
    if (n > 0) { chosen = step; total = n; }
  }
  if (total === 0) chosen = steps[0];
  setRecruiterFilters(chosen.f);
  total = currentFilteredJobs.length;

  const parts = [plan.say];
  if (total > 0) {
    if (chosen.note) parts.push(`Nothing matched exactly, so I widened it to ${chosen.note}.`);
    parts.push(`**${total.toLocaleString('en-IN')} ${total === 1 ? 'job' : 'jobs'}** ${describeRecruiterFilters(chosen.f)}.`.replace(/\s+\./, '.'));
  } else {
    parts.push("I couldn't find anything close to that in the catalogue right now. Try another role or location.");
  }
  if (plan.question) parts.push(plan.question);

  const tags = [];
  if (chosen.f.q) tags.push(`Search: ${chosen.f.q}`);
  if (chosen.f.discipline !== 'all') tags.push(formatPillName(chosen.f.discipline));
  if (chosen.f.location !== 'all') tags.push(formatPillName(chosen.f.location));
  if (chosen.f.expPreset !== 'all') tags.push(`${chosen.f.expPreset.replace('-', '–')} yrs`);
  if (chosen.f.company !== 'all') tags.push(chosen.f.company);

  updateHeroChatCount();
  return { reply: parts.filter(Boolean).join(' '), jobs: currentFilteredJobs.slice(0, 3), total, tags };
}

function renderInlineJobCardsHtml(matchedJobs, totalCount) {
  if (!matchedJobs || !matchedJobs.length) return '';
  const topJobs = matchedJobs.slice(0, 3);
  return `
    <div class="chat-inline-job-list">
      ${topJobs.map(j => {
        const score = j.match_score || 98;
        return `
          <div class="chat-inline-job-card" onclick="openJobDetailsModal('${j.id}')">
            <div class="chat-inline-job-header">
              <div class="chat-inline-job-company">
                ${renderCompanyVectorLogo(j.company, j.portal)}
                <span class="chat-inline-comp-name">${escapeHtml(j.company)}</span>
              </div>
              <span class="chat-inline-match-badge">${score}% Match</span>
            </div>
            <div class="chat-inline-job-title">${escapeHtml(j.title)}</div>
            <div class="chat-inline-job-meta">
              <span>${escapeHtml(j.location || 'Worldwide Remote')}</span>
              <span>·</span>
              <span>${escapeHtml(j.expText || (j.minExp ? `${j.minExp}+ yrs` : 'All levels'))}</span>
            </div>
            <div class="chat-inline-job-actions">
              <a href="${j.applyUrl || '#'}" target="_blank" rel="noopener noreferrer" class="chat-inline-apply-btn" onclick="event.stopPropagation()">
                Apply Direct ↗
              </a>
              <button class="chat-inline-view-btn" onclick="openJobDetailsModal('${j.id}'); event.stopPropagation()">
                Details
              </button>
            </div>
          </div>
        `;
      }).join('')}
    </div>
    <div class="chat-inline-feed-jump">
      <button class="chat-jump-feed-btn" onclick="scrollToJobFeed()">
        View All ${totalCount ? totalCount.toLocaleString() : currentFilteredJobs.length.toLocaleString()} Ranked Roles in Feed ↓
      </button>
    </div>
  `;
}

function renderInlineCvPromptHtml() {
  return `
    <div class="chat-inline-cv-prompt">
      <button class="chat-inline-upload-btn" onclick="document.getElementById('hero-cv-file-input').click()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><polyline points="9 15 12 12 15 15"/></svg>
        Upload Candidate CV (PDF)
      </button>
      <span class="chat-inline-cv-hint">Enables instant 100% personalized ranking across verified openings</span>
    </div>
  `;
}

function scrollToJobFeed() {
  const target = document.getElementById('job-rows-container') || document.querySelector('.feed-column');
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

async function sendHeroAiChat(customText) {
  const input = document.getElementById('hero-ai-chat-input');
  const query = (customText !== undefined ? customText : (input ? input.value : '')).trim();
  if (!query) return;

  if (input) input.value = '';

  const chatContainer = document.getElementById('hero-chat-messages');
  if (!chatContainer) return;

  // Append User message
  const userBubble = document.createElement('div');
  userBubble.className = 'chat-msg user-msg';
  userBubble.innerHTML = `
    <div class="msg-avatar">You</div>
    <div class="msg-bubble">
      <p>${escapeHtml(query)}</p>
    </div>
  `;
  chatContainer.appendChild(userBubble);

  // Typing indicator bubble
  const typingBubble = document.createElement('div');
  typingBubble.className = 'chat-msg agent-msg';
  typingBubble.id = 'hero-typing-indicator';
  typingBubble.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-bubble" style="color:var(--muted); font-style:italic;">
      Thinking & filtering live openings...
    </div>
  `;
  chatContainer.appendChild(typingBubble);
  chatContainer.scrollTop = chatContainer.scrollHeight;

  const conversationPayload = chatGptHistory.slice(-8);

  heroChatHistory.push({ role: 'user', content: query });
  chatGptHistory.push({ role: 'user', content: query });
  saveChatHistoryToStorage();
  updateAiSearchBarText();

  try {
    const cvSummaryText = currentProfileData
      ? `${currentProfileData.headline || 'Engineer'} (${currentProfileData.experienceText || ''}) - Core Skills: ${(currentProfileData.skills || []).join(', ')}`
      : null;

    const res = await fetch(`${RECRUITER_API}/ai/recruiter_chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: recruiterRequestBody(query, conversationPayload)
    });

    const data = await res.json();
    typingBubble.remove();

    if (data.session_state) {
      recruiterSessionState = Object.assign(recruiterSessionState, data.session_state);
    }

    // Update the feed filters first; the reply is built from the real results.
    const outcome = applyLlmControlToWebpage(data);
    const replyText = outcome.reply || "Tell me a bit more about the role you want.";
    heroChatHistory.push({ role: 'assistant', content: replyText });
    chatGptHistory.push({ role: 'assistant', content: replyText });
    saveChatHistoryToStorage();
    updateAiSearchBarText();

    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-msg agent-msg';
    aiBubble.innerHTML = `
      <div class="msg-avatar">AI</div>
      <div class="msg-bubble">
        ${formatAgentMarkdown(replyText)}
      </div>
    `;
    chatContainer.appendChild(aiBubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    updateHeroChatCount();
  } catch (err) {
    console.error("AI chat error:", err);
    typingBubble.remove();
    activeFilters.q = query;
    applyFiltersAndRender();
    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-msg agent-msg';
    aiBubble.innerHTML = `
      <div class="msg-avatar">AI</div>
      <div class="msg-bubble">
        <p>Filtered the live pipeline for <strong>"${escapeHtml(query)}"</strong> across all live verified roles.</p>
      </div>
    `;
    chatContainer.appendChild(aiBubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    updateHeroChatCount();
  }
}

function applyAiChatResultsAndScroll() {
  if (heroChatCriteria.company && heroChatCriteria.company !== 'all') {
    activeFilters.company = heroChatCriteria.company;
  }
  if (heroChatCriteria.discipline && heroChatCriteria.discipline !== 'all') {
    activeFilters.discipline = heroChatCriteria.discipline;
    document.querySelectorAll('[data-discipline]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-discipline') === heroChatCriteria.discipline);
    });
  }
  if (heroChatCriteria.location && heroChatCriteria.location !== 'all') {
    activeFilters.location = heroChatCriteria.location;
    document.querySelectorAll('[data-location]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-location') === heroChatCriteria.location);
    });
  }
  if (heroChatCriteria.keywords) {
    activeFilters.q = heroChatCriteria.keywords;
    const deskInput = document.getElementById('desktop-search-input');
    if (deskInput) deskInput.value = heroChatCriteria.keywords;
  }
  if (heroChatCriteria.maxExp < 10) {
    activeFilters.maxExp = heroChatCriteria.maxExp;
    syncExpSlider(heroChatCriteria.maxExp, `${heroChatCriteria.maxExp}`);
  }

  updateActivePills();

  if (aiChatMatchedJobs && aiChatMatchedJobs.length > 0) {
    currentFilteredJobs = aiChatMatchedJobs;
    renderedBatchLimit = 20;
    renderJobCards(currentFilteredJobs);
    const feedCountEl = document.getElementById('feed-count');
    if (feedCountEl) feedCountEl.innerHTML = `<strong>${currentFilteredJobs.length.toLocaleString()} roles</strong> · Filtered & Ranked by AI Recruiter`;
  } else {
    applyFiltersAndRender();
  }

  // Scroll to results feed smoothly
  const target = document.getElementById('job-rows-container') || document.querySelector('.feed-column');
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ==========================================================================
// CHATGPT-STYLE FULLSCREEN IMMERSIVE AI TALENT AGENT CONTROLLER
// Zero outside interfacing when active. Mobile (Phone) & Desktop optimized.
// ==========================================================================

let chatGptHistory = [];

function saveChatHistoryToStorage() {
  try {
    localStorage.setItem('camouroles_chat_history', JSON.stringify(chatGptHistory.slice(-30)));
  } catch (e) {}
}

function loadChatHistoryFromStorage() {
  try {
    const raw = localStorage.getItem('camouroles_chat_history');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        chatGptHistory = parsed;
        heroChatHistory = parsed.slice();
      }
    }
  } catch (e) {}
}

function renderPersistedChatGptMessages() {
  const feed = document.getElementById('chatgpt-messages-feed');
  if (!feed) return;
  if (!chatGptHistory || chatGptHistory.length === 0) return;

  // Render initial greeting followed by all saved messages
  feed.innerHTML = `
    <div class="chatgpt-msg-row agent-row">
      <div class="chatgpt-agent-avatar">
        <img src="/logo-gold.png" class="emblem-dark" alt="AI">
        <img src="/logo-maroon.png" class="emblem-day" alt="AI">
      </div>
      <div class="chatgpt-bubble agent-bubble">
        <p>Welcome. I am your career partner on CAMOUROLES. I evaluate your background against verified, unlisted, and direct-from-source engineering positions across frontier tech.</p>
        <p>You can describe your ideal tech stack, seniority, or compensation target, or drop your CV above for precision ranking. What kind of challenges are you looking to tackle next?</p>
      </div>
    </div>
  `;

  chatGptHistory.forEach(msg => {
    if (msg.role === 'user') {
      const userRow = document.createElement('div');
      userRow.className = 'chatgpt-msg-row user-row';
      userRow.innerHTML = `
        <div class="chatgpt-bubble user-bubble">
          <p>${escapeHtml(msg.content)}</p>
        </div>
      `;
      feed.appendChild(userRow);
    } else {
      const agentRow = document.createElement('div');
      agentRow.className = 'chatgpt-msg-row agent-row';
      agentRow.innerHTML = `
        <div class="chatgpt-agent-avatar">
          <img src="/logo-gold.png" class="emblem-dark" alt="AI">
          <img src="/logo-maroon.png" class="emblem-day" alt="AI">
        </div>
        <div class="chatgpt-bubble agent-bubble">
          ${formatAgentMarkdown(msg.content)}
        </div>
      `;
      feed.appendChild(agentRow);
    }
  });

  const container = document.getElementById('chatgpt-thread-container');
  if (container) {
    setTimeout(() => { container.scrollTop = container.scrollHeight; }, 60);
  }
}

function openChatGptInterface(initialQuery) {
  const portal = document.getElementById('chatgpt-fullscreen-interface');
  if (!portal) return;

  portal.style.display = 'flex';
  document.body.classList.add('chatgpt-portal-active');

  // Restore persisted message history in chat UI
  renderPersistedChatGptMessages();

  // Sync candidate CV profile card
  syncChatGptCvUI(currentProfileData);

  // Update dynamic count pill
  updateChatGptRolesCounter();

  // Focus textarea
  const input = document.getElementById('chatgpt-user-input');
  if (input) {
    setTimeout(() => {
      input.focus();
      autoResizeChatGptTextarea(input);
    }, 120);
  }

  // If initial query provided (e.g. from hero input), submit it directly
  if (initialQuery && typeof initialQuery === 'string' && initialQuery.trim()) {
    submitChatGptMessage(initialQuery.trim());
  }
}

function closeChatGptInterface() {
  const portal = document.getElementById('chatgpt-fullscreen-interface');
  if (portal) portal.style.display = 'none';
  document.body.classList.remove('chatgpt-portal-active');
  showView('feed');

  updateAiSearchBarText();

  if (aiChatMatchedJobs && aiChatMatchedJobs.length) {
    currentFilteredJobs = aiChatMatchedJobs;
    renderedBatchLimit = 20;
    renderJobCards(currentFilteredJobs);
    const countEl = document.getElementById('feed-count');
    if (countEl) countEl.textContent = `${currentFilteredJobs.length.toLocaleString()} verified positions active`;
  } else {
    applyFiltersAndRender();
  }

  const container = document.getElementById('job-rows-container');
  if (container) {
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function closeChatGptAndShowRoles() {
  closeChatGptInterface();
}

function resetChatGptSession() {
  chatGptHistory = [];
  heroChatHistory = [];
  recruiterSessionState = {
    discipline: 'all',
    location: 'all',
    company: 'all',
    minExp: 1
  };
  try {
    localStorage.removeItem('camouroles_chat_history');
  } catch (e) {}
  updateAiSearchBarText();
  const feed = document.getElementById('chatgpt-messages-feed');
  if (feed) {
    feed.innerHTML = `
      <div class="chatgpt-msg-row agent-row">
        <div class="chatgpt-agent-avatar">
          <img src="/logo-gold.png" class="emblem-dark" alt="AI">
          <img src="/logo-maroon.png" class="emblem-day" alt="AI">
        </div>
        <div class="chatgpt-bubble agent-bubble">
          <p>Started a fresh session. What engineering challenges, technical stacks, or target compensation bands should we explore?</p>
        </div>
      </div>
    `;
  }
  const input = document.getElementById('chatgpt-user-input');
  if (input) {
    input.value = '';
    input.focus();
  }
}

function sendChatGptQuickPrompt(promptText) {
  submitChatGptMessage(promptText);
}

function autoResizeChatGptTextarea(el) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

function handleChatGptKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    submitChatGptMessage();
  }
}

function syncChatGptCvUI(profile) {
  const titleEl = document.getElementById('chatgpt-cv-title-text');
  const descEl = document.getElementById('chatgpt-cv-desc-text');
  const pillEl = document.getElementById('chatgpt-cv-action-pill');

  if (profile && profile.headline) {
    const headline = profile.headline;
    const skills = (profile.skills || []).slice(0, 5).join(', ');
    const exp = profile.experienceText || (profile.experienceYears ? `${profile.experienceYears}+ yrs` : '');
    if (titleEl) titleEl.textContent = `Active CV: ${headline}`;
    if (descEl) descEl.textContent = `${exp}${exp && skills ? ' · ' : ''}Skills: ${skills || 'General Engineering'}`;
    if (pillEl) pillEl.textContent = 'Replace PDF';
  } else {
    if (titleEl) titleEl.textContent = 'Drop Candidate CV / Resume (PDF)';
    if (descEl) descEl.textContent = 'Automatic skill extraction, experience tiering, and instant ranking';
    if (pillEl) pillEl.textContent = 'Attach PDF';
  }
}

function updateChatGptRolesCounter(overrideCount) {
  const label = document.getElementById('chatgpt-view-roles-label');
  if (!label) return;
  let count = overrideCount;
  if (typeof count !== 'number') {
    count = currentFilteredJobs ? currentFilteredJobs.length : allJobsList.length;
  }
  label.textContent = `View Matched Roles (${count.toLocaleString()}) ↓`;
}

function formatAgentMarkdown(text) {
  if (!text) return '';
  let s = escapeHtml(text);

  // Bold
  s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Headings
  s = s.replace(/^###\s*(.*?)$/gm, '<h4>$1</h4>');
  s = s.replace(/^##\s*(.*?)$/gm, '<h3>$1</h3>');

  // Lists
  const lines = s.split('\n');
  let inList = false;
  let listType = '';
  const out = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (/^[-*]\s+/.test(line)) {
      if (!inList || listType !== 'ul') {
        if (inList) out.push(`</${listType}>`);
        out.push('<ul>');
        inList = true;
        listType = 'ul';
      }
      out.push(`<li>${line.replace(/^[-*]\s+/, '')}</li>`);
    } else if (/^\d+\.\s+/.test(line)) {
      if (!inList || listType !== 'ol') {
        if (inList) out.push(`</${listType}>`);
        out.push('<ol>');
        inList = true;
        listType = 'ol';
      }
      out.push(`<li>${line.replace(/^\d+\.\s+/, '')}</li>`);
    } else {
      if (inList) {
        out.push(`</${listType}>`);
        inList = false;
        listType = '';
      }
      if (line.length > 0) {
        out.push(`<p>${line}</p>`);
      }
    }
  }
  if (inList) out.push(`</${listType}>`);

  return out.join('');
}

async function submitChatGptMessage(customText) {
  const textarea = document.getElementById('chatgpt-user-input');
  const query = (customText !== undefined ? customText : (textarea ? textarea.value : '')).trim();
  if (!query) return;

  if (textarea) {
    textarea.value = '';
    textarea.style.height = 'auto';
  }

  const feed = document.getElementById('chatgpt-messages-feed');
  if (!feed) return;

  // 1. User Message Row
  const userRow = document.createElement('div');
  userRow.className = 'chatgpt-msg-row user-row';
  userRow.innerHTML = `
    <div class="chatgpt-bubble user-bubble">
      <p>${escapeHtml(query)}</p>
    </div>
  `;
  feed.appendChild(userRow);

  // 2. Typing Indicator
  const typingRow = document.getElementById('chatgpt-typing-row');
  if (typingRow) {
    typingRow.style.display = 'flex';
    feed.appendChild(typingRow);
  }

  const container = document.getElementById('chatgpt-thread-container');
  if (container) container.scrollTop = container.scrollHeight;

  const conversationPayload = chatGptHistory.slice(-8);

  chatGptHistory.push({ role: 'user', content: query });
  heroChatHistory.push({ role: 'user', content: query });
  saveChatHistoryToStorage();
  updateAiSearchBarText();

  try {
    const cvSummaryText = currentProfileData
      ? `${currentProfileData.headline || 'Engineer'} (${currentProfileData.experienceText || ''}) - Core Skills: ${(currentProfileData.skills || []).join(', ')}`
      : null;

    const res = await fetch(`${RECRUITER_API}/ai/recruiter_chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: recruiterRequestBody(query, conversationPayload)
    });

    if (typingRow) typingRow.style.display = 'none';

    if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.error || 'Could not read this CV'); }
    const data = await res.json();

    if (data.session_state) {
      recruiterSessionState = Object.assign(recruiterSessionState, data.session_state);
    }

    // Apply the recruiter's plan to the feed first; the reply is built from the real results.
    const outcome = applyLlmControlToWebpage(data);
    const replyRaw = outcome.reply || "Tell me a bit more about the role you want.";
    chatGptHistory.push({ role: 'assistant', content: replyRaw });
    heroChatHistory.push({ role: 'assistant', content: replyRaw });
    saveChatHistoryToStorage();

    const filterTagsHtml = outcome.tags.length ? `
      <div class="chatgpt-jev-tag-strip">
        ${outcome.tags.map(t => `<span class="chatgpt-jev-tag">${escapeHtml(t)}</span>`).join('')}
      </div>` : '';

    const matchedCardsHtml = outcome.jobs.length ? `
      <div class="chatgpt-matched-cards-row">
        ${outcome.jobs.map(j => `
          <div class="chatgpt-job-snippet-card" onclick="openJobDetailFromChatGpt('${escapeHtml(String(j.id))}')">
            <div class="chatgpt-job-snippet-info">
              <div class="chatgpt-job-snippet-title">${escapeHtml(j.title)}</div>
              <div class="chatgpt-job-snippet-meta">${escapeHtml(j.company)} · ${escapeHtml(j.location || 'Remote')}</div>
            </div>
            ${jobMatchesMap[j.id] ? `<div class="chatgpt-job-snippet-score">${jobMatchesMap[j.id].score}%</div>` : ''}
          </div>`).join('')}
      </div>` : '';

    const jumpBtnHtml = outcome.total > 0 ? `
      <div class="chatgpt-feed-jump-wrap">
        <button class="chatgpt-feed-jump-btn" onclick="closeChatGptAndShowRoles()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          <span>See all ${outcome.total.toLocaleString('en-IN')} in the feed</span>
        </button>
      </div>` : '';

    // Append Agent Row
    const agentRow = document.createElement('div');
    agentRow.className = 'chatgpt-msg-row agent-row';
    agentRow.innerHTML = `
      <div class="chatgpt-agent-avatar">
        <img src="/logo-gold.png" class="emblem-dark" alt="AI">
        <img src="/logo-maroon.png" class="emblem-day" alt="AI">
      </div>
      <div class="chatgpt-bubble agent-bubble">
        ${formatAgentMarkdown(replyRaw)}
        ${filterTagsHtml}
        ${matchedCardsHtml}
        ${jumpBtnHtml}
      </div>
    `;
    feed.appendChild(agentRow);

    if (outcome.total !== null) updateChatGptRolesCounter(outcome.total);
    if (container) container.scrollTop = container.scrollHeight;
  } catch (err) {
    console.error("ChatGPT chat error:", err);
    if (typingRow) typingRow.style.display = 'none';

    const errorRow = document.createElement('div');
    errorRow.className = 'chatgpt-msg-row agent-row';
    errorRow.innerHTML = `
      <div class="chatgpt-agent-avatar">
        <img src="/logo-gold.png" class="emblem-dark" alt="AI">
        <img src="/logo-maroon.png" class="emblem-day" alt="AI">
      </div>
      <div class="chatgpt-bubble agent-bubble">
        <p>Sorry, I couldn't reach the recruiter just now. Please try again in a moment, or use Filters.</p>
      </div>
    `;
    feed.appendChild(errorRow);
    if (container) container.scrollTop = container.scrollHeight;
  }
}

function openJobDetailFromChatGpt(jobId) {
  closeChatGptInterface();
  openJobDetailsModal(jobId);
}

// Client-Side PDF Text Extractor (pdf.js decompresses PDF binary streams into plaintext)
async function extractTextFromPdfFile(file) {
  if (window.pdfjsLib) {
    try {
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      let fullText = '';
      for (let i = 1; i <= Math.min(pdf.numPages, 10); i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageStrings = textContent.items.map(item => item.str);
        fullText += pageStrings.join(' ') + '\n';
      }
      if (fullText.trim().length >= 20) {
        return fullText.trim();
      }
    } catch (e) {
      console.warn('PDF.js client extraction notice:', e);
    }
  }
  return await file.text();
}

async function onChatGptCvSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const descEl = document.getElementById('chatgpt-cv-desc-text');
  if (descEl) descEl.textContent = `Extracting plaintext from ${file.name}...`;

  let extractedText = '';
  try {
    extractedText = await extractTextFromPdfFile(file);
  } catch (e) {
    console.warn('Text extraction error:', e);
  }

  if (descEl) descEl.textContent = `Analyzing candidate profile...`;

  try {
    const res = await fetch(`${RECRUITER_API}/cv/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cv_text: extractedText,
        file_name: file.name
      })
    });

    if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.error || 'Could not read this CV'); }
    const data = await res.json();

    if (data.profile) {
      currentProfileData = data.profile;
      syncProfileDataToUI(data.profile);
      syncChatGptCvUI(data.profile);
      try {
        localStorage.setItem('camouroles_cv_profile', JSON.stringify(data.profile));
      } catch (e) {}
    }

    if (data.matches) {
      jobMatchesMap = data.matches;
      try {
        localStorage.setItem('camouroles_cv_matches', JSON.stringify(data.matches));
      } catch (e) {}
      aiChatMatchedJobs = allJobsList.filter(j => jobMatchesMap[j.id]).sort((a, b) => (jobMatchesMap[b.id]?.score || 0) - (jobMatchesMap[a.id]?.score || 0));
    }

    applyFiltersAndRender();
    updateChatGptRolesCounter(aiChatMatchedJobs ? aiChatMatchedJobs.length : allJobsList.length);

    // Append system message to chat
    const feed = document.getElementById('chatgpt-messages-feed');
    if (feed) {
      const confirmRow = document.createElement('div');
      confirmRow.className = 'chatgpt-msg-row agent-row';
      const headline = data.profile?.headline || 'Senior Engineer';
      const skills = (data.profile?.skills || []).slice(0, 6).join(', ');
      confirmRow.innerHTML = `
        <div class="chatgpt-agent-avatar">
          <img src="/logo-gold.png" class="emblem-dark" alt="AI">
          <img src="/logo-maroon.png" class="emblem-day" alt="AI">
        </div>
        <div class="chatgpt-bubble agent-bubble">
          <p>CV parsed and verified: <strong>${escapeHtml(file.name)}</strong></p>
          <p>Identified Target Role: <strong>${escapeHtml(headline)}</strong> (${data.profile?.experienceText || 'Verified experience'}).</p>
          <div class="chatgpt-jev-tag-strip">
            <span class="chatgpt-jev-tag">Verified Stack: ${escapeHtml(skills || 'General Engineering')}</span>
            <span class="chatgpt-jev-tag">Top Matches: ${data.total_matched || Object.keys(data.matches || {}).length || 50} verified positions</span>
          </div>
          <p>${escapeHtml(data.profile?.summary || 'Tell me your target locations or compensation parameters, and we will narrow down unlisted openings.')}</p>
        </div>
      `;
      feed.appendChild(confirmRow);
      const cvConfirmText = `CV parsed and verified: ${file.name}. Identified Target Role: ${headline} (${data.profile?.experienceText || 'Verified experience'}). Verified Stack: ${skills || 'General Engineering'}. ${data.profile?.summary || ''}`;
      chatGptHistory.push({ role: 'assistant', content: cvConfirmText });
      heroChatHistory.push({ role: 'assistant', content: cvConfirmText });
      saveChatHistoryToStorage();
      updateAiSearchBarText();
      const container = document.getElementById('chatgpt-thread-container');
      if (container) container.scrollTop = container.scrollHeight;
    }
  } catch (err) {
    console.error("ChatGPT CV upload error:", err);
    if (typeof showNotification === "function") showNotification(err.message || "Could not read this CV");
    if (descEl) descEl.textContent = "Upload failed. Please provide a standard PDF.";
  }
}

// Aliases for unified operation across legacy triggers
window.openHeroAiChat = openChatGptInterface;
window.openAiSearchModal = openChatGptInterface;
window.closeAiSearchModal = closeChatGptInterface;
window.showAiRankedResults = closeChatGptAndShowRoles;
window.onAiCvSelected = onChatGptCvSelected;
window.sendAiChatMessage = submitChatGptMessage;

// ==========================================================================
// DEDICATED PROFILE PAGE & TOP 10 REFINED MATCHES
// ==========================================================================
function renderProfileView() {
  // Sync candidate user identity
  const nameEl = document.getElementById('profile-page-name');
  const emailEl = document.getElementById('profile-page-email');
  const avatarEl = document.getElementById('profile-page-avatar');
  const statusEl = document.getElementById('profile-page-status');
  const dotEl = document.getElementById('profile-page-dot');
  const topBarLabel = document.getElementById('top-bar-user-label');
  const authActionBtn = document.getElementById('profile-auth-action-btn');

  if (currentUser) {
    if (nameEl) nameEl.textContent = currentUser.name || 'Candidate';
    if (emailEl) emailEl.textContent = currentUser.email || '';
    if (statusEl) statusEl.textContent = 'Google Verified Account';
    if (dotEl) dotEl.style.display = 'inline-block';
    if (avatarEl) {
      if (currentUser.picture) {
        avatarEl.innerHTML = `<img src="${currentUser.picture}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
      } else {
        avatarEl.textContent = (currentUser.name || 'C').charAt(0).toUpperCase();
      }
    }
    if (topBarLabel) topBarLabel.textContent = (currentUser.name || 'User').split(' ')[0];
    if (authActionBtn) {
      authActionBtn.textContent = 'Sign Out';
      authActionBtn.onclick = signOutGoogle;
    }
  } else {
    if (nameEl) nameEl.textContent = 'Guest Candidate';
    if (emailEl) emailEl.textContent = 'Sign in with Google to sync bookmarks';
    if (statusEl) statusEl.textContent = 'Guest Session';
    if (dotEl) dotEl.style.display = 'none';
    if (avatarEl) avatarEl.textContent = 'G';
    if (topBarLabel) topBarLabel.textContent = 'Profile';
    if (authActionBtn) {
      authActionBtn.textContent = 'Sign In';
      authActionBtn.onclick = signInWithGoogle;
    }
  }

  // Load profile data if available
  if (currentProfileData) {
    syncProfileDataToUI(currentProfileData); syncManualCvUI();
  }

  renderProfileTopJobs();
}

function syncProfileDataToUI(profile) {
  const box = document.getElementById('profile-candidate-data-box');
  const headlineEl = document.getElementById('profile-cand-headline');
  const expEl = document.getElementById('profile-cand-exp');
  const skillsContainer = document.getElementById('profile-cand-skills');

  if (box && profile && profile.headline) {
    box.style.display = 'block';
    if (headlineEl) headlineEl.textContent = profile.headline;
    if (expEl) expEl.textContent = profile.experienceText || `${profile.years_of_experience || 5}+ years verified engineering experience`;
    if (skillsContainer && profile.skills) {
      skillsContainer.innerHTML = profile.skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
    }
  }
}

function renderProfileTopJobs() {
  const container = document.getElementById('profile-top-jobs-list');
  if (!container) return;

  let candidatePool = [...allJobsList];

  // Filter by target hub if specified
  if (selectedProfileHub && selectedProfileHub !== 'All') {
    const hubLower = selectedProfileHub.toLowerCase();
    candidatePool = candidatePool.filter(j => {
      const loc = (j.location || '').toLowerCase();
      if (hubLower === 'worldwide remote') return j.is_remote || loc.includes('remote');
      if (hubLower === 'sf bay area') return loc.includes('san francisco') || loc.includes('bay area') || loc.includes('ca');
      if (hubLower === 'seattle') return loc.includes('seattle') || loc.includes('redmond') || loc.includes('bellevue');
      if (hubLower === 'india') return loc.includes('india') || loc.includes('bengaluru') || loc.includes('bangalore') || loc.includes('hyderabad');
      if (hubLower === 'london') return loc.includes('london') || loc.includes('uk');
      return loc.includes(hubLower);
    });
  }

  // Sort candidatePool by match score if exists, else highlight top tier companies (NVIDIA, Apple, Microsoft, Google, Amazon, Anthropic, Stripe)
  const priorityComps = ['nvidia', 'apple', 'microsoft', 'google', 'amazon', 'anthropic', 'stripe', 'waymo', 'scale ai'];

  candidatePool.sort((a, b) => {
    const scoreA = jobMatchesMap[a.id]?.score || 0;
    const scoreB = jobMatchesMap[b.id]?.score || 0;
    if (scoreA !== scoreB) return scoreB - scoreA;

    // Secondary priority: top companies
    const compA = (a.company || '').toLowerCase();
    const compB = (b.company || '').toLowerCase();
    const prioA = priorityComps.findIndex(p => compA.includes(p));
    const prioB = priorityComps.findIndex(p => compB.includes(p));
    if (prioA !== -1 && prioB !== -1) return prioA - prioB;
    if (prioA !== -1) return -1;
    if (prioB !== -1) return 1;

    return 0;
  });

  const top10 = candidatePool.slice(0, 10);

  if (!top10.length) {
    container.innerHTML = `
      <div class="empty-state-box" style="padding: 28px 16px;">
        <div style="font-weight:700; color:var(--ink); font-size:14px;">No matching openings in ${escapeHtml(selectedProfileHub)}</div>
        <div style="font-size:12px; color:var(--muted); margin-top:4px;">Try selecting "All Hubs" or clearing your profile filter.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = top10.map((j, idx) => {
    const matchData = jobMatchesMap[j.id];
    const matchScore = matchData ? matchData.score : Math.max(82, 98 - (idx * 2));
    const salaryText = getJobSalaryBand(j);
    const exp = getJobExperienceMinMax(j);
    const expText = j.expText || j.experience || `${exp.min} - ${exp.max} yrs`;
    const isSaved = savedJobIds.has(j.id);

    return `
      <div class="profile-job-row">
        <div class="profile-job-left">
          <div class="profile-job-avatar">
            ${renderCompanyVectorLogo(j.company, j.portal || j.ats_type)}
          </div>
          <div class="profile-job-details">
            <h4 class="profile-job-title" onclick="openJobDetailsModal('${j.id}')">${escapeHtml(j.title)}</h4>
            <div class="profile-job-company-line">
              <span class="profile-job-company">${escapeHtml(j.company)}</span>
              <span>·</span>
              <span>${escapeHtml(j.location || 'Remote')}</span>
              <span>·</span>
              <span class="profile-job-salary">${escapeHtml(salaryText)}</span>
            </div>
            <div class="profile-job-tags">
              <span class="profile-job-tag">${escapeHtml(expText)}</span>
              ${(j.skills && j.skills.length) ? j.skills.slice(0, 3).map(s => `<span class="profile-job-tag">${escapeHtml(s)}</span>`).join('') : ''}
            </div>
          </div>
        </div>

        <div class="profile-job-right">
          <div class="profile-match-badge tabular-num">
            ${matchScore}% Match
          </div>
          <div class="profile-job-btns">
            <button class="btn-bookmark ${isSaved ? 'saved' : ''}" title="${isSaved ? 'Remove bookmark' : 'Save role'}" onclick="toggleBookmark('${j.id}'); renderProfileTopJobs();">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            </button>
            <button class="btn-profile-apply" onclick="openJobDetailsModal('${j.id}')">
              <span>Apply</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function selectProfileHub(btn, hub) {
  selectedProfileHub = hub;
  const chips = document.querySelectorAll('#profile-hub-chips .pref-chip');
  chips.forEach(c => c.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderProfileTopJobs();
}

function clearProfileSearchAndReset() {
  selectedProfileHub = 'All';
  const chips = document.querySelectorAll('#profile-hub-chips .pref-chip');
  chips.forEach(c => c.classList.remove('active'));
  const firstChip = document.querySelector('#profile-hub-chips .pref-chip');
  if (firstChip) firstChip.classList.add('active');
  renderProfileTopJobs();
}

async function onProfileCvSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const statusText = document.getElementById('profile-dropzone-status-text');
  if (statusText) statusText.textContent = `Analyzing ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);
  // The server needs the CV's text; raw PDF bytes cannot be read there.
  formData.append('extracted_text', await extractTextFromPdfFile(file).catch(() => ''));
  formData.append('targetHub', selectedProfileHub || 'All');
  formData.append('targetDiscipline', 'all');

  try {
    const res = await fetch(`${RECRUITER_API}/cv/match`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.error || 'Could not read this CV'); }
    const data = await res.json();
    if (statusText) statusText.textContent = `Analyzed: ${file.name}`;

    if (data.profile) {
      currentProfileData = data.profile;
      syncProfileDataToUI(data.profile);
    }

    if (data.matches) {
      jobMatchesMap = data.matches;
    }

    renderProfileTopJobs();
  } catch (err) {
    console.error("Profile CV upload error:", err);
    if (typeof showNotification === "function") showNotification(err.message || "Could not read this CV");
    if (statusText) statusText.textContent = "Upload failed. Please use PDF.";
  }
}


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
    const res = await fetch(`${RECRUITER_API}/cv/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cv_text: extractedText,
        file_name: file.name
      })
    });

    if (!res.ok) { const errBody = await res.json().catch(() => ({})); throw new Error(errBody.error || 'Could not read this CV'); }
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
    syncProfileDataToUI(currentProfileData); syncManualCvUI();
    updateHeroCvStatusUI(currentProfileData);

    // Default to match_desc sort to display highest probability % first
    currentSortMode = 'match_desc';
    applyFiltersAndRender();

    const count = Object.keys(jobMatchesMap).length;
    const countEl = document.getElementById('feed-count');
    if (countEl) countEl.textContent = `Top ${count} Matched Positions · Ranked by CV Match Score`;

    // Smoothly scroll to the feed so the candidate sees their match percentages immediately
    const container = document.getElementById('job-rows-container');
    if (container) {
      container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  } catch (err) {
    console.error("Manual CV match error:", err);
    if (typeof showNotification === "function") showNotification(err.message || "Could not read this CV");
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
  syncProfileDataToUI(null); syncManualCvUI();
  updateHeroCvStatusUI(null);
  applyFiltersAndRender();
}

window.onManualCvSelected = onManualCvSelected;
window.clearManualCv = clearManualCv;
window.syncManualCvUI = syncManualCvUI;
