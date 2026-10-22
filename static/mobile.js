/* ==========================================================================
   CAMOUROLES — MOBILE LAYER (phones, < 768px)
   Loaded after app.js. Replaces the job card markup on phones, turns the
   details and filter modals into swipeable bottom sheets, hides the header
   while scrolling down, and slides a highlight under the active nav tab.
   Desktop keeps the original app.js behaviour.
   ========================================================================== */

const phoneQuery = window.matchMedia('(max-width: 767px)');
const isPhone = () => phoneQuery.matches;

const ICON = {
  pin: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
  bag: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
  star: '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
};

// --------------------------------------------------------------------------
// Real salary only: what the posting itself states, never an estimate
// --------------------------------------------------------------------------
const desktopSalaryBand = getJobSalaryBand;
function statedSalary(job) {
  const desc = String((job && job.description) || '');
  const m = desc.match(/(?:salary|compensation|pay range|base pay|base range|target pay)[:\s]*([$€£₹][\d,]+(?:\s*[-–to]+\s*[$€£₹]?[\d,]+)?(?:\s*(?:\/|per)?\s*(?:yr|year|annum|hr|hour|mo|month|L|LPA))?)/i);
  return m && m[1] && m[1].length < 40 ? m[1].trim() : '';
}
getJobSalaryBand = function (job) {
  return isPhone() ? statedSalary(job) : desktopSalaryBand(job);
};

// --------------------------------------------------------------------------
// Location + field filters: several picks at once (stored comma-joined, e.g. "india,uae")
// --------------------------------------------------------------------------
// Country names need whole-word matching: the old checks treated "Indiana" as India and "American" as Canada.
Object.assign(LOCATION_MATCHERS, {
  india: (loc) => /\b(india|bengaluru|bangalore|hyderabad|pune|mumbai|delhi|gurgaon|gurugram|noida|chennai|kolkata|ahmedabad|kochi|coimbatore)\b/.test(loc) || /,\s*ind\b/.test(loc),
  canada: (loc) => /\b(canada|toronto|vancouver|montreal|waterloo|ottawa|calgary)\b/.test(loc) || /,\s*can\b/.test(loc),
  australia: (loc) => /\b(australia|sydney|melbourne|brisbane|perth)\b/.test(loc) || /,\s*aus\b/.test(loc),
  france: (loc) => /\b(france|paris|lyon|toulouse)\b/.test(loc) || /,\s*fra\b/.test(loc),
  usa: (loc) => /\b(united states|usa|u\.s\.?|california|new york|texas|washington|massachusetts|colorado|illinois|georgia|virginia|florida|san francisco|san jose|palo alto|mountain view|sunnyvale|menlo park|san mateo|los angeles|seattle|bellevue|redmond|boston|austin|denver|chicago|atlanta|costa mesa|long beach|hawthorne|el segundo|arlington|pittsburgh|philadelphia)\b/.test(loc)
    || /,\s*(ca|ny|tx|wa|ma|co|il|ga|va|fl|nj|pa|or|az|ut|nc|md|mi|oh|mn)\b/.test(loc),
});

const singleMatchesLocation = matchesLocation;
matchesLocation = function (job, locKey) {
  const keys = String(locKey || 'all').split(',').filter(Boolean);
  return keys.length > 1 ? keys.some((k) => singleMatchesLocation(job, k)) : singleMatchesLocation(job, locKey);
};

const singleMatchesDiscipline = matchesDiscipline;
matchesDiscipline = function (job, key) {
  const keys = String(key || 'all').split(',').filter(Boolean);
  return keys.length > 1 ? keys.some((k) => singleMatchesDiscipline(job, k)) : singleMatchesDiscipline(job, key);
};

const singlePillName = formatPillName;
formatPillName = function (val) {
  return String(val).split(',').map((v) => LABELS[v] || singlePillName(v)).join(' + ');
};

const COUNTRIES = [
  ['worldwide_remote', 'Remote'], ['india', 'India'], ['usa', 'United States'], ['uae', 'UAE & Gulf'],
  ['london', 'United Kingdom'], ['germany', 'Germany'], ['canada', 'Canada'], ['singapore', 'Singapore'],
  ['netherlands', 'Netherlands'], ['switzerland', 'Switzerland'], ['france', 'France'], ['japan', 'Japan'],
  ['australia', 'Australia'],
];
const FIELDS = [
  ['ai_ml', 'AI & ML'], ['backend', 'Backend'], ['frontend', 'Frontend'], ['devops', 'DevOps'],
  ['robotics', 'Robotics'], ['spacetech', 'Space'], ['electrical_hardware', 'Hardware'], ['defense_cyber', 'Defense & Cyber'],
  ['climate_cleanenergy', 'Climate'], ['biotech_health', 'Biotech'], ['game_dev', 'Games'], ['design', 'Design'],
  ['business', 'Business & Ops'], ['hr', 'HR & People'], ['civil_construction', 'Civil'], ['safety', 'Safety'],
];
const EXPERIENCE = [['all', 'Any'], ['0-1', '0–1 yr'], ['1-3', '1–3 yrs'], ['3-6', '3–6 yrs'], ['6+', '6+ yrs']];
const LABELS = Object.fromEntries([...COUNTRIES, ...FIELDS]);

// Every filter setter refreshes the pills; keep the sheet and the nav badge in step with it.
const desktopUpdateActivePills = updateActivePills;
updateActivePills = function () {
  desktopUpdateActivePills();
  syncFilterSheet();
};

// --------------------------------------------------------------------------
// Compact job cards
// --------------------------------------------------------------------------
const desktopRenderJobCards = renderJobCards;
const animatedJobIds = new Set(); // cards animate in once, not on every re-render

renderJobCards = function (jobs) {
  if (!isPhone() || !jobs.length) return desktopRenderJobCards(jobs);
  const container = document.getElementById('job-rows-container');
  if (!container) return;

  const hasCvScores = Object.keys(jobMatchesMap || {}).length > 0;
  const visible = jobs.slice(0, renderedBatchLimit);
  let fresh = 0;

  let html = visible.map((j) => {
    const firstTime = !animatedJobIds.has(j.id);
    if (firstTime) animatedJobIds.add(j.id);
    const delay = firstTime ? Math.min(fresh++, 8) : -1;

    const saved = savedJobIds.has(j.id);
    const exp = getJobExperienceMinMax(j);
    const location = j.location || (j.isRemote || j.is_remote ? 'Remote' : '');
    const remote = (j.isRemote || j.is_remote) && !/remote/i.test(location);
    const salary = statedSalary(j);
    const score = hasCvScores ? Number(jobMatchesMap[j.id]?.score || 0) : 0;
    const skills = (j.skills || []).slice(0, 3);

    return `
      <article class="m-card${score ? ' has-match' : ''}${delay < 0 ? ' m-seen' : ''}" style="--i:${Math.max(delay, 0)}"
               data-job-id="${escapeHtml(String(j.id))}" onclick="openJobDetailsModal('${j.id}')">
        <div class="m-card-top">
          <span class="m-logo">${renderCompanyVectorLogo(j.company, j.portal || j.ats_type)}</span>
          <div class="m-head">
            <h3 class="m-title">${escapeHtml(j.title || '')}</h3>
            <div class="m-company">${escapeHtml(j.company || '')}</div>
          </div>
          <button class="m-save${saved ? ' saved' : ''}" aria-label="${saved ? 'Remove from saved' : 'Save role'}"
                  onclick="event.stopPropagation(); mobileToggleSave('${j.id}')">${ICON.star}</button>
        </div>
        <div class="m-meta">
          ${location ? `<span class="m-meta-item m-loc">${ICON.pin}<span class="m-ellipsis">${escapeHtml(location)}</span></span>` : ''}
          <span class="m-meta-item m-exp">${ICON.bag}${exp.min}–${exp.max} yrs</span>
          ${remote ? '<span class="m-meta-item m-remote">Remote</span>' : ''}
          ${salary ? `<span class="m-meta-item m-salary">${escapeHtml(salary)}</span>` : ''}
        </div>
        ${skills.length ? `<div class="m-skills">${skills.map((s) => `<span class="m-skill">${escapeHtml(s)}</span>`).join('')}</div>` : ''}
        ${score ? matchRing(score) : ''}
      </article>`;
  }).join('');

  if (jobs.length > renderedBatchLimit) {
    html += `
      <div class="load-more-wrap">
        <button class="btn-load-more" onclick="loadMoreJobs()">
          <span>Show more (${(jobs.length - renderedBatchLimit).toLocaleString('en-IN')} left)</span>
        </button>
      </div>`;
  }
  container.innerHTML = html;
};

function matchRing(score) {
  const pct = Math.max(0, Math.min(100, Math.round(score)));
  const offset = (113.1 * (1 - pct / 100)).toFixed(1);
  return `
    <div class="m-match" style="--m-ring-offset:${offset}" aria-label="${pct}% match with your CV">
      <svg width="40" height="40" viewBox="0 0 40 40"><circle class="m-ring-bg" cx="20" cy="20" r="18" fill="none" stroke-width="3"/>
        <circle class="m-ring" cx="20" cy="20" r="18" fill="none" stroke-width="3"/></svg>
      <span class="m-match-val">${pct}</span>
    </div>`;
}

function mobileToggleSave(jobId) {
  toggleBookmark(jobId); // re-renders the feed
  const btn = document.querySelector(`.m-card[data-job-id="${CSS.escape(String(jobId))}"] .m-save`);
  if (btn) {
    btn.classList.add('m-pop');
    if (navigator.vibrate) navigator.vibrate(8);
  }
}

// Chat top bar: short "38 jobs →" label on phones
const desktopRolesCounter = updateChatGptRolesCounter;
updateChatGptRolesCounter = function (count) {
  desktopRolesCounter(count);
  const label = document.getElementById('chatgpt-view-roles-label');
  if (!isPhone() || !label) return;
  const n = typeof count === 'number' ? count : (currentFilteredJobs || []).length;
  label.textContent = `${n.toLocaleString('en-IN')} jobs →`;
};

// --------------------------------------------------------------------------
// Details sheet: hide stats we do not actually know
// --------------------------------------------------------------------------
const desktopOpenJobDetails = openJobDetailsModal;
openJobDetailsModal = function (jobId) {
  desktopOpenJobDetails(jobId);
  if (!isPhone()) return;
  const salaryEl = document.getElementById('modal-salary-val');
  const salaryItem = salaryEl && salaryEl.closest('.modal-stat-item');
  if (salaryItem) salaryItem.classList.toggle('m-empty', !salaryEl.textContent.trim());
  const dialog = document.querySelector('#job-apply-modal .job-modal-dialog');
  if (dialog) dialog.scrollTop = 0;
};

// --------------------------------------------------------------------------
// Filter sheet (phones): multi-select countries and fields, live result count
// --------------------------------------------------------------------------
const CHECK = '<svg class="m-chip-check" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>';

function buildFilterSheet() {
  const chips = (group, items) => items.map(([key, label]) =>
    `<button type="button" class="m-chip" data-group="${group}" data-key="${key}">${CHECK}<span>${label}</span></button>`).join('');

  const el = document.createElement('div');
  el.className = 'm-sheet-backdrop';
  el.id = 'm-filters';
  el.innerHTML = `
    <div class="m-sheet" role="dialog" aria-modal="true" aria-label="Filters">
      <div class="m-sheet-head">
        <h2>Filters</h2>
        <button type="button" class="m-text-btn" data-action="reset">Reset</button>
      </div>
      <div class="m-sheet-body">
        <label class="m-search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="search" id="m-filter-q" placeholder="Title, company or skill" autocomplete="off">
        </label>
        <section>
          <h3>Experience</h3>
          <div class="m-segment">${EXPERIENCE.map(([key, label]) => `<button type="button" data-group="exp" data-key="${key}">${label}</button>`).join('')}</div>
        </section>
        <section>
          <h3>Where <span class="m-hint">pick any</span></h3>
          <div class="m-chips">${chips('loc', COUNTRIES)}</div>
        </section>
        <section>
          <h3>Field <span class="m-hint">pick any</span></h3>
          <div class="m-chips">${chips('field', FIELDS)}</div>
        </section>
      </div>
      <div class="m-sheet-foot">
        <button type="button" class="m-primary" data-action="done"><span id="m-filter-count">Show jobs</span></button>
      </div>
    </div>`;
  document.body.appendChild(el);
  setupSheet(SHEETS.find((s) => s.backdrop === 'm-filters'));
  watchOverlay(el);

  el.addEventListener('click', (e) => {
    if (e.target === el) return closeMobileFilters();
    const btn = e.target.closest('button');
    if (!btn) return;
    const { group, key, action } = btn.dataset;
    if (action === 'done') return closeMobileFilters();
    if (action === 'reset') {
      document.getElementById('m-filter-q').value = '';
      onSearchInput('');
      setExpPreset('all');
      setLocationFilter('all');
      setDisciplineFilter('all');
    } else if (group === 'exp') {
      setExpPreset(key);
    } else if (group === 'loc' || group === 'field') {
      const current = group === 'loc' ? activeFilters.location : activeFilters.discipline;
      const picked = new Set(String(current || 'all').split(',').filter((k) => k && k !== 'all'));
      picked.has(key) ? picked.delete(key) : picked.add(key);
      const next = picked.size ? [...picked].join(',') : 'all';
      group === 'loc' ? setLocationFilter(next) : setDisciplineFilter(next);
    }
    syncFilterSheet();
  });
  document.getElementById('m-filter-q').addEventListener('input', (e) => {
    onSearchInput(e.target.value);
    setTimeout(syncFilterSheet, 200); // search is debounced by 150 ms
  });
  return el;
}

function syncFilterSheet() {
  const sheet = document.getElementById('m-filters');
  if (!sheet) return;
  const locs = new Set(String(activeFilters.location || 'all').split(','));
  const fields = new Set(String(activeFilters.discipline || 'all').split(','));
  sheet.querySelectorAll('[data-group="loc"]').forEach((b) => b.classList.toggle('on', locs.has(b.dataset.key)));
  sheet.querySelectorAll('[data-group="field"]').forEach((b) => b.classList.toggle('on', fields.has(b.dataset.key)));
  sheet.querySelectorAll('[data-group="exp"]').forEach((b) => b.classList.toggle('on', (activeFilters.expPreset || 'all') === b.dataset.key));
  const q = document.getElementById('m-filter-q');
  if (q && document.activeElement !== q) q.value = activeFilters.q || '';
  const n = (currentFilteredJobs || []).length;
  document.getElementById('m-filter-count').textContent = `Show ${n.toLocaleString('en-IN')} job${n === 1 ? '' : 's'}`;
  const active = (locs.has('all') ? 0 : locs.size) + (fields.has('all') ? 0 : fields.size) + ((activeFilters.expPreset || 'all') !== 'all' ? 1 : 0) + (activeFilters.q ? 1 : 0);
  const navLabel = document.querySelector('#mob-nav-filter span');
  if (navLabel) navLabel.textContent = active ? `Filters · ${active}` : 'Filters';
}

function openMobileFilters() {
  const sheet = document.getElementById('m-filters') || buildFilterSheet();
  syncFilterSheet();
  sheet.querySelector('.m-sheet').scrollTop = 0;
  void sheet.offsetHeight; // commit the closed position first so the slide-up animates
  sheet.classList.add('open');
}
function closeMobileFilters() {
  document.getElementById('m-filters')?.classList.remove('open');
}

const desktopOpenFilters = openFiltersModal;
openFiltersModal = function () {
  return isPhone() ? openMobileFilters() : desktopOpenFilters();
};
const desktopCloseFilters = closeFiltersModal;
closeFiltersModal = function () {
  closeMobileFilters();
  desktopCloseFilters();
};

// --------------------------------------------------------------------------
// Back button / swipe-back: each open sheet or screen is one history step
// --------------------------------------------------------------------------
const OVERLAYS = {
  job: { isOpen: () => document.getElementById('job-apply-modal')?.classList.contains('open'), close: () => closeJobApplyModal() },
  filters: { isOpen: () => document.getElementById('m-filters')?.classList.contains('open'), close: () => closeMobileFilters() },
  plans: { isOpen: () => document.getElementById('plans-pricing-modal')?.classList.contains('open'), close: () => closePlansModal() },
  chat: { isOpen: () => document.body.classList.contains('chatgpt-portal-active'), close: () => closeChatGptInterface() },
  view: { isOpen: () => currentMobileView !== 'feed', close: () => showView('feed') },
};
const overlayStack = [];
let closingFromHistory = false;
let currentMobileView = 'feed';

function syncOverlayHistory() {
  if (!isPhone() || closingFromHistory) return;
  for (const [name, o] of Object.entries(OVERLAYS)) {
    const inStack = overlayStack.includes(name);
    if (o.isOpen() && !inStack) {
      overlayStack.push(name);
      history.pushState({ mOverlay: name }, '');
    } else if (!o.isOpen() && inStack) {
      // Closed from the page (X, swipe, backdrop): drop its history step too.
      overlayStack.splice(overlayStack.indexOf(name), 1);
      closingFromHistory = true;
      history.back();
    }
  }
}

window.addEventListener('popstate', () => {
  if (closingFromHistory) { closingFromHistory = false; return; }
  const top = overlayStack.pop();
  if (!top) return;
  closingFromHistory = true;
  OVERLAYS[top].close();
  // close() triggers observers synchronously or on the next tick; release after both.
  setTimeout(() => { closingFromHistory = false; }, 0);
});

const desktopShowView = showView;
showView = function (view) {
  desktopShowView(view);
  currentMobileView = view || 'feed';
  syncOverlayHistory();
};

// --------------------------------------------------------------------------
// Bottom sheets: swipe down to close, lock page scroll while open
// --------------------------------------------------------------------------
const SHEETS = [
  { backdrop: 'job-apply-modal', panel: '.job-modal-dialog', close: () => closeJobApplyModal() },
  { backdrop: 'm-filters', panel: '.m-sheet', close: () => closeMobileFilters() },
];

function setupSheet({ backdrop, panel, close }) {
  const bd = document.getElementById(backdrop);
  const sheet = bd && bd.querySelector(panel);
  if (!sheet) return;

  const grabber = document.createElement('div');
  grabber.className = 'm-grabber';
  sheet.prepend(grabber);

  let startY = 0, lastY = 0, lastT = 0, velocity = 0, dragging = false;

  sheet.addEventListener('touchstart', (e) => {
    if (!isPhone()) return;
    const onGrabber = e.target === grabber;
    // Only a pull from the very top closes the sheet; anywhere content can still scroll up, let it scroll.
    if (!onGrabber && scrolledDownInside(e.target, sheet)) return;
    dragging = true;
    startY = lastY = e.touches[0].clientY;
    lastT = performance.now();
    velocity = 0;
  }, { passive: true });

  sheet.addEventListener('touchmove', (e) => {
    if (!dragging) return;
    const y = e.touches[0].clientY;
    if (y < startY) { dragging = false; return; } // moving up is a scroll, not a close
    const dy = y - startY;
    if (dy < 6) return; // ignore tiny wobbles on a tap
    const now = performance.now();
    velocity = (y - lastY) / Math.max(1, now - lastT);
    lastY = y; lastT = now;
    sheet.classList.add('m-dragging');
    sheet.style.setProperty('--m-drag', `${dy}px`);
    if (e.cancelable) e.preventDefault();
  }, { passive: false });

  const end = () => {
    if (!dragging) return;
    dragging = false;
    sheet.classList.remove('m-dragging');
    const dy = parseFloat(sheet.style.getPropertyValue('--m-drag')) || 0;
    if (dy > 120 || velocity > 0.6) {
      close();
      setTimeout(() => sheet.style.removeProperty('--m-drag'), 420);
    } else {
      sheet.style.removeProperty('--m-drag');
    }
  };
  sheet.addEventListener('touchend', end);
  sheet.addEventListener('touchcancel', end);
}

// True when the touch starts inside something (the sheet or a list in it) that is scrolled away from its top.
function scrolledDownInside(target, sheet) {
  for (let el = target; el && el !== sheet.parentElement; el = el.parentElement) {
    if (el.scrollTop > 0 && el.scrollHeight > el.clientHeight) return true;
    if (el === sheet) break;
  }
  return false;
}

// Freeze the page behind an open sheet without losing the reader's place in the feed.
let lockedScrollY = null;
function syncScrollLock() {
  const anyOpen = isPhone() && ['job', 'filters', 'plans'].some((name) => OVERLAYS[name].isOpen());
  const body = document.body;
  if (anyOpen && lockedScrollY === null) {
    lockedScrollY = window.scrollY;
    Object.assign(body.style, { position: 'fixed', top: `-${lockedScrollY}px`, left: '0', right: '0', width: '100%' });
  } else if (!anyOpen && lockedScrollY !== null) {
    const y = lockedScrollY;
    lockedScrollY = null;
    Object.assign(body.style, { position: '', top: '', left: '', right: '', width: '' });
    window.scrollTo(0, y);
  }
}

// One observer per overlay element: keeps scroll lock and back-button history in step.
function watchOverlay(el) {
  if (!el) return;
  new MutationObserver(() => { syncScrollLock(); syncOverlayHistory(); })
    .observe(el, { attributes: true, attributeFilter: ['class'] });
}

// --------------------------------------------------------------------------
// Header hides while scrolling down, comes back on any upward scroll
// --------------------------------------------------------------------------
function setupHeaderAutoHide() {
  const bar = document.querySelector('.top-bar');
  if (!bar) return;
  let lastY = window.scrollY;
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (Math.abs(y - lastY) < 6) return; // ignore jitter
    const hide = isPhone() && y > 160 && y > lastY;
    bar.classList.toggle('m-hidden', hide);
    document.body.classList.toggle('m-header-hidden', hide);
    lastY = y;
  }, { passive: true });
}

// --------------------------------------------------------------------------
// Bottom nav: a highlight that slides to the active tab
// --------------------------------------------------------------------------
function setupNavPill() {
  const nav = document.querySelector('.mobile-nav-bar');
  if (!nav) return;
  const pill = document.createElement('div');
  pill.className = 'm-nav-pill';
  nav.prepend(pill);

  const place = () => {
    const active = nav.querySelector('.mobile-nav-btn.active') || nav.querySelector('.mobile-nav-btn');
    if (!active) return;
    const navBox = nav.getBoundingClientRect();
    const box = active.getBoundingClientRect();
    const width = Math.min(box.width - 8, 72);
    pill.style.width = `${width}px`;
    pill.style.transform = `translateX(${box.left - navBox.left + (box.width - width) / 2}px)`;
  };
  new MutationObserver(place).observe(nav, { subtree: true, attributes: true, attributeFilter: ['class'] });
  new ResizeObserver(place).observe(nav); // also catches the first real layout after fonts load
  place();
}

// --------------------------------------------------------------------------
// Boot
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  setupSheet(SHEETS[0]);
  ['job-apply-modal', 'plans-pricing-modal'].forEach((id) => watchOverlay(document.getElementById(id)));
  watchOverlay(document.body); // the AI chat screen toggles a class on <body>
  setupHeaderAutoHide();
  setupNavPill();

  const closeBtn = document.querySelector('.job-modal-close-btn');
  if (closeBtn && !closeBtn.children.length) {
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  }

  const aiText = document.getElementById('ai-bar-summary-text');
  if (aiText && isPhone()) aiText.textContent = 'Ask the AI recruiter…';
  const heroInput = document.getElementById('hero-search-input');
  if (heroInput && isPhone()) heroInput.placeholder = 'Role, skill or company';

  // Switching between phone and desktop width re-renders with the right card style
  phoneQuery.addEventListener('change', () => { if (typeof applyFiltersAndRender === 'function') applyFiltersAndRender(); });
});
