/* ==========================================================================
   CAMOUROLES — FREE APPLY LIMITS
   When the server sends jobs without apply links (gated: true), every Apply goes
   through /api/apply: 2 free applies signed out, 5 in total signed in, unlimited on Pro.
   Loaded after app.js and mobile.js.
   ========================================================================== */

let applyStatus = null; // { gated, signed_in, pro, used, limit, left }

function applyDeviceId() {
  let id = null;
  try { id = localStorage.getItem('camouroles_device'); } catch (e) {}
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`);
    try { localStorage.setItem('camouroles_device', id); } catch (e) {}
  }
  return id;
}

async function refreshApplyStatus() {
  try {
    const res = await fetch(`${API_BASE}/apply/status?device_id=${encodeURIComponent(applyDeviceId())}`, { headers: await authHeaders() });
    if (res.ok) applyStatus = await res.json();
  } catch (e) {}
  renderApplyMeter();
}

function applyMeterText() {
  const s = applyStatus;
  if (!s || !s.gated) return '';
  if (s.pro) return 'Pro · unlimited applies';
  if (!s.signed_in) {
    return s.left > 0
      ? `${s.left} of ${s.limit} free applies left · sign in for 5`
      : 'Sign in to keep applying (5 free applies)';
  }
  return s.left > 0
    ? `${s.left} of ${s.limit} free applies left`
    : 'Free applies used · Pro gives unlimited';
}

function renderApplyMeter() {
  const bar = document.querySelector('#job-apply-modal .job-modal-actions-bar');
  if (!bar) return;
  let meter = document.getElementById('m-apply-meter');
  if (!meter) {
    meter = document.createElement('div');
    meter.id = 'm-apply-meter';
    meter.className = 'm-apply-meter';
    bar.parentNode.insertBefore(meter, bar);
  }
  const text = applyMeterText();
  meter.textContent = text;
  meter.hidden = !text;
}

function findJob(jobId) {
  return allJobsList.find((j) => String(j.id) === String(jobId));
}

// Gated jobs have no link in the browser; show the site's name in the details and fetch the link on Apply.
const ungatedOpenJobDetails = openJobDetailsModal;
let openedJobId = null;
openJobDetailsModal = function (jobId) {
  const job = findJob(jobId);
  if (job && job.gated && !job.applyUrl && job.applyHost) job.applyUrl = `https://${job.applyHost}/`;
  openedJobId = jobId;
  ungatedOpenJobDetails(jobId);
  renderApplyMeter();
};

async function gatedApply(jobId) {
  // Open the tab now, while we still have the tap; fill it in once the server says yes.
  const tab = window.open('', '_blank');
  try {
    const res = await fetch(`${API_BASE}/apply`, {
      method: 'POST',
      headers: await authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ job_id: jobId, device_id: applyDeviceId() }),
    });
    const data = await res.json().catch(() => ({}));
    applyStatus = { ...(applyStatus || {}), gated: true, ...data };
    renderApplyMeter();

    if (data.allowed && data.url) {
      if (tab) { tab.opener = null; tab.location.href = data.url; } else { window.location.href = data.url; }
      if (!data.pro && typeof data.left === 'number') {
        showNotification(data.left > 0
          ? `Opened. ${data.left} free ${data.left === 1 ? 'apply' : 'applies'} left.`
          : (data.signed_in ? 'Opened. That was your last free apply.' : 'Opened. Sign in to get 3 more free applies.'));
      }
      return;
    }
    if (tab) tab.close();
    if (data.need === 'login' || data.need === 'pay') openApplyGate(data.need);
    else showNotification(data.detail || 'Could not open this job right now. Please try again.');
  } catch (e) {
    if (tab) tab.close();
    showNotification('Could not open this job right now. Please try again.');
  }
}

// Catch every Apply link on a gated job: the details sheet, its source row, and chat cards.
document.addEventListener('click', (e) => {
  const link = e.target.closest('#modal-apply-btn, #modal-sources-box a, .chat-inline-apply-btn');
  if (!link) return;
  const jobId = link.dataset.jobId || (link.closest('#job-apply-modal') ? openedJobId : null);
  const job = jobId && findJob(jobId);
  if (!job || !job.gated) return;
  e.preventDefault();
  e.stopPropagation();
  gatedApply(job.id);
}, true);

// --------------------------------------------------------------------------
// Sign-in / upgrade prompt
// --------------------------------------------------------------------------
const GATE_COPY = {
  login: {
    icon: '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>',
    title: 'Sign in to keep applying',
    body: () => `You've used your ${ANON_LIMIT_TEXT()} free applies. Sign in with Google — it's free, and you get 5 applies in total.`,
    primary: 'Continue with Google',
    action: () => signInWithGoogle(),
  },
  pay: {
    icon: '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
    title: "You've used your 5 free applies",
    body: () => 'Go Pro for unlimited applies: ₹29 for a week or ₹99 for a month. Jobs you already applied to stay free to reopen.',
    primary: 'See plans',
    action: () => { closeApplyGate(); setTimeout(() => openPlansModal('week'), 350); },
  },
};
const ANON_LIMIT_TEXT = () => (applyStatus && !applyStatus.signed_in && applyStatus.limit) || 2;

function buildApplyGate() {
  const el = document.createElement('div');
  el.className = 'm-sheet-backdrop m-gate-backdrop';
  el.id = 'm-gate';
  el.innerHTML = `
    <div class="m-sheet m-gate" role="dialog" aria-modal="true" aria-labelledby="m-gate-title">
      <div class="m-gate-icon"></div>
      <h2 id="m-gate-title"></h2>
      <p class="m-gate-body"></p>
      <button type="button" class="m-primary" data-gate="go"></button>
      <button type="button" class="m-text-btn m-gate-later" data-gate="later">Not now</button>
    </div>`;
  document.body.appendChild(el);
  el.addEventListener('click', (e) => {
    if (e.target === el || e.target.closest('[data-gate="later"]')) return closeApplyGate();
    if (e.target.closest('[data-gate="go"]')) GATE_COPY[el.dataset.kind]?.action();
  });
  if (typeof setupSheet === 'function') setupSheet({ backdrop: 'm-gate', panel: '.m-sheet', close: () => closeApplyGate() });
  if (typeof watchOverlay === 'function') watchOverlay(el);
  return el;
}

function openApplyGate(kind) {
  const el = document.getElementById('m-gate') || buildApplyGate();
  const copy = GATE_COPY[kind];
  el.dataset.kind = kind;
  el.querySelector('.m-gate-icon').innerHTML = copy.icon;
  el.querySelector('#m-gate-title').textContent = copy.title;
  el.querySelector('.m-gate-body').textContent = copy.body();
  el.querySelector('[data-gate="go"]').textContent = copy.primary;
  void el.offsetHeight;
  el.classList.add('open');
}

function closeApplyGate() {
  document.getElementById('m-gate')?.classList.remove('open');
}

// Back button closes the prompt like any other sheet.
if (typeof OVERLAYS === 'object') {
  OVERLAYS.gate = { isOpen: () => document.getElementById('m-gate')?.classList.contains('open'), close: () => closeApplyGate() };
}

// Signing in or out changes the allowance; refresh it whenever the profile reloads.
const ungatedSignOut = signOutGoogle;
signOutGoogle = function () {
  ungatedSignOut();
  refreshApplyStatus();
};

const ungatedLoadProfile = loadProfileData;
loadProfileData = async function () {
  await ungatedLoadProfile();
  refreshApplyStatus();
};

document.addEventListener('DOMContentLoaded', () => {
  refreshApplyStatus();
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshApplyStatus(); });
});
