"""
Deploy Prime Max style monetization, Razorpay Checkout, and Google Auth to static/app.js & web/app.js.
"""

import os

with open("static/app.js", "r", encoding="utf-8") as f:
    js = f.read()

# 1. State variables
state_target = """let currentUser = JSON.parse(localStorage.getItem('camouroles_user') || 'null');"""
state_replacement = """let currentUser = JSON.parse(localStorage.getItem('camouroles_user') || 'null');
let activeSelectedPlan = 'month';
let isUserPro = localStorage.getItem('camouroles_pro_unlimited') === 'true';
let userUnlimitedUntil = localStorage.getItem('camouroles_pro_until') || null;"""

if state_target in js and "let activeSelectedPlan" not in js:
    js = js.replace(state_target, state_replacement)
    print("Added state variables")
else:
    print("State variables already present or target not found")

# 2. DOMContentLoaded
dom_target = """  initTheme();
  renderAuthUI();
  updateSavedPillCount();"""
dom_replacement = """  initTheme();
  renderAuthUI();
  updateProBadgeUI();
  initGoogleAuth();
  updateSavedPillCount();"""

if dom_target in js and "updateProBadgeUI()" not in js:
    js = js.replace(dom_target, dom_replacement)
    print("Added init calls to DOMContentLoaded")
else:
    print("DOMContentLoaded already updated or target not found")

# 3. Auth and Monetization Block
old_auth_block = """function renderAuthUI() {
  const container = document.getElementById('auth-container');
  if (!container) return;

  if (currentUser) {
    container.innerHTML = `
      <button class="btn-profile-pill" onclick="toggleProfileDropdown(event)">
        <img class="profile-avatar-img" src="${currentUser.picture || 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=Camouroles'}" alt="${escapeHtml(currentUser.name)}">
        <span>${escapeHtml(currentUser.name.split(' ')[0])}</span>
        <span class="cloud-synced-chip">Synced</span>
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
}"""

new_auth_block = """function renderAuthUI() {
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
          <span>Delete CV Profile (Wipe)</span>
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

function initGoogleAuth() {
  try {
    if (window.google && window.google.accounts && window.google.accounts.id) {
      window.google.accounts.id.initialize({
        client_id: '570018263730-rvd8clojdlcjqsfqfcdohsm7r32gcqn0.apps.googleusercontent.com',
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
      });
    }
  } catch (e) {
    console.warn("Google GIS init:", e);
  }
}

async function handleGoogleCredentialResponse(response) {
  if (!response || !response.credential) return;
  try {
    const res = await fetch(`${API_BASE}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        credential: response.credential,
        savedIds: [...savedJobIds]
      })
    });
    const data = await res.json();
    if (data.user) {
      currentUser = data.user;
      localStorage.setItem('camouroles_user', JSON.stringify(currentUser));
      if (data.user.savedIds && data.user.savedIds.length) {
        data.user.savedIds.forEach(id => savedJobIds.add(id));
        localStorage.setItem('camouroles_saved_jobs', JSON.stringify([...savedJobIds]));
      }
      renderAuthUI();
      updateSavedPillCount();
      applyFiltersAndRender();
      showNotification(`Signed in as ${currentUser.name}`);
    }
  } catch (err) {
    console.error("Google credential exchange error:", err);
  }
}

async function signInWithGoogle() {
  try {
    if (window.google && window.google.accounts && window.google.accounts.id) {
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          signInWithDevGoogle();
        }
      });
    } else {
      await signInWithDevGoogle();
    }
  } catch (err) {
    await signInWithDevGoogle();
  }
}

async function signInWithDevGoogle() {
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
    showNotification(`Signed in as ${currentUser.name}`);
  } catch (err) {
    console.error("Google dev sign in error:", err);
  }
}

function signOutGoogle() {
  currentUser = null;
  localStorage.removeItem('camouroles_user');
  renderAuthUI();
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
    badgeBtn.title = 'Camouroles Pro Active · Unlimited Direct Access';
  } else {
    badgeBtn.classList.remove('active');
    if (labelEl) labelEl.textContent = 'Pro Upgrade';
    badgeBtn.title = 'View Membership Plans & Unlock Roles';
  }
}

function openPlansModal(preferredPlan) {
  if (isUserPro && !preferredPlan) {
    showNotification('Camouroles Pro is active with unlimited verified role access.');
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
    if (priceVal) priceVal.textContent = '₹49';
    if (priceWas) priceWas.textContent = '₹99';
    if (priceTag) priceTag.textContent = '7-DAY PASS';
    if (submitBtn) submitBtn.innerHTML = `<span>Unlock 7-Day Access (₹49)</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
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
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentUser?.token || 'dev'}`
      },
      body: JSON.stringify({ plan: activeSelectedPlan })
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
      name: 'Camouroles',
      description: activeSelectedPlan === 'week' ? 'Weekly Pass (7 Days Access)' : 'Monthly Pro (Unlimited Access)',
      order_id: orderData.order_id,
      theme: {
        color: '#701A2B'
      },
      prefill: {
        name: currentUser?.name || 'Candidate',
        email: currentUser?.email || 'engineer@camouroles.io'
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
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${currentUser?.token || 'dev'}`
            },
            body: JSON.stringify({
              razorpay_order_id: paymentResponse.razorpay_order_id,
              razorpay_payment_id: paymentResponse.razorpay_payment_id,
              razorpay_signature: paymentResponse.razorpay_signature,
              plan: activeSelectedPlan
            })
          });

          if (!verifyRes.ok) {
            const vErr = await verifyRes.json().catch(() => ({}));
            throw new Error(vErr.detail || 'Payment verification failed');
          }

          const verifyData = await verifyRes.json();
          isUserPro = true;
          userUnlimitedUntil = verifyData.unlimited_until;
          localStorage.setItem('camouroles_pro_unlimited', 'true');
          if (userUnlimitedUntil) localStorage.setItem('camouroles_pro_until', userUnlimitedUntil);

          updateProBadgeUI();
          closePlansModal();
          showNotification('Payment verified. Camouroles Pro is now active.');
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
}"""

if old_auth_block in js:
    js = js.replace(old_auth_block, new_auth_block)
    print("Replaced auth and added monetization block")
elif "openPlansModal" in js:
    print("Auth/monetization block already deployed")
else:
    print("WARNING: Old auth block not found")

# 4. loadProfileData update for is_unlimited
old_profile_head = """    const res = await fetch(`${API_BASE}/profile`);
    if (!res.ok) return;
    const data = await res.json();
    const profile = data.profile;
    if (!profile || !profile.headline) return;"""

new_profile_head = """    const res = await fetch(`${API_BASE}/profile`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.is_unlimited !== undefined) {
      isUserPro = Boolean(data.is_unlimited);
      if (isUserPro) {
        localStorage.setItem('camouroles_pro_unlimited', 'true');
        if (data.unlimited_until) localStorage.setItem('camouroles_pro_until', data.unlimited_until);
      }
      updateProBadgeUI();
    }
    const profile = data.profile || data;
    if (!profile || !profile.headline) return;"""

if old_profile_head in js:
    js = js.replace(old_profile_head, new_profile_head)
    print("Updated loadProfileData for is_unlimited")
else:
    print("loadProfileData already updated or head not found")

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js)
with open("web/app.js", "w", encoding="utf-8") as f:
    f.write(js)
print("Successfully saved static/app.js and web/app.js")
