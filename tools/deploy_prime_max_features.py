"""
Deploy Prime Max style monetization, Razorpay Checkout, and Google Auth to Camouroles.
"""

import os
import re

# 1. Update static/styles.css
with open("static/styles.css", "r", encoding="utf-8") as f:
    css = f.read()

monetization_css = """
/* ==========================================================================
   PRIME PRO PLANS, RAZORPAY & GOOGLE AUTH (Apple Burgundy + Vintage White)
   ========================================================================== */
.btn-pro-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, #701A2B, #8E2239);
  color: #FFFFFF;
  border: 1px solid rgba(201, 165, 92, 0.4);
  font-family: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(112, 26, 43, 0.25);
}
.btn-pro-badge:hover {
  background: linear-gradient(135deg, #8E2239, #A82D47);
  box-shadow: 0 4px 14px rgba(112, 26, 43, 0.35);
  transform: translateY(-1px);
}
.btn-pro-badge.active {
  background: linear-gradient(135deg, #B38F46, #D4AF37);
  color: #1A1A1A;
  border-color: #F1D78A;
  box-shadow: 0 2px 10px rgba(212, 175, 55, 0.3);
}

.google-auth-wrap {
  display: inline-flex;
  align-items: center;
  position: relative;
}
.btn-google-signin {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 32px;
  padding: 0 11px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-google-signin:hover {
  background: var(--bg-subtle);
  border-color: var(--muted);
}
.google-user-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 32px;
  padding: 2px 10px 2px 3px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
  cursor: pointer;
}
.google-user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}
.google-user-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
}

/* Luxury Plans Modal */
.plans-modal-dialog {
  width: 92%;
  max-width: 500px;
  background: var(--surface);
  border: 1px solid rgba(201, 165, 92, 0.45);
  border-radius: 20px;
  padding: 24px 26px;
  box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.35);
  position: relative;
}
.plans-offer-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 10px;
  background: linear-gradient(110deg, #F9F1DE, #F0E3C2);
  border: 1px solid rgba(201, 165, 92, 0.5);
  color: #701A2B;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
  margin-bottom: 16px;
}
[data-theme="dark"] .plans-offer-strip {
  background: rgba(201, 165, 92, 0.15);
  color: #E2C07D;
}
.plans-seg {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  background: var(--bg-subtle);
  border: 1px solid var(--line);
  padding: 4px;
  border-radius: 12px;
  margin-bottom: 16px;
}
.plans-seg-btn {
  border: none;
  background: none;
  padding: 9px 6px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}
.plans-seg-btn.active {
  background: linear-gradient(135deg, #701A2B, #8E2239);
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(112, 26, 43, 0.3);
}
.plans-seg-btn small {
  display: block;
  font-size: 10px;
  font-weight: 500;
  opacity: 0.85;
}

.plan-card-body {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 18px;
}
.plan-price-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}
.plan-price-val {
  font-size: 34px;
  font-weight: 800;
  color: var(--terracotta);
  letter-spacing: -0.03em;
}
.plan-price-was {
  font-size: 16px;
  color: var(--muted);
  text-decoration: line-through;
}
.plan-price-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(112, 26, 43, 0.1);
  color: var(--terracotta);
  border: 1px solid rgba(112, 26, 43, 0.2);
}
.plan-feature-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}
.plan-feature-item {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--ink);
}
.plan-feature-item svg {
  flex-shrink: 0;
  color: var(--gold);
  margin-top: 2px;
}

.btn-razorpay-cta {
  width: 100%;
  height: 46px;
  border-radius: 12px;
  background: linear-gradient(135deg, #701A2B, #8E2239);
  color: #FFFFFF;
  border: 1px solid rgba(201, 165, 92, 0.4);
  font-family: inherit;
  font-size: 14.5px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 16px rgba(112, 26, 43, 0.3);
  transition: all 0.2s ease;
  margin-bottom: 16px;
}
.btn-razorpay-cta:hover {
  background: linear-gradient(135deg, #8E2239, #A82D47);
  box-shadow: 0 6px 20px rgba(112, 26, 43, 0.4);
  transform: translateY(-1px);
}

.razorpay-trust-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--bg-subtle);
  border: 1px solid rgba(201, 165, 92, 0.35);
}
.trust-shield-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(201, 165, 92, 0.12);
  border: 1px solid rgba(201, 165, 92, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--gold);
}
.trust-text-area {
  flex: 1;
}
.trust-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink);
}
.trust-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 3px 0;
}
.trust-chip {
  font-size: 9.5px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--muted);
}
.trust-sub {
  font-size: 10px;
  color: var(--muted);
}
"""

if ".btn-pro-badge" not in css:
    css += "\n" + monetization_css
    with open("static/styles.css", "w", encoding="utf-8") as f:
        f.write(css)
    with open("web/styles.css", "w", encoding="utf-8") as f:
        f.write(css)
    print("Appended monetization CSS")
else:
    print("CSS already has monetization styles")

# 2. Update static/index.html
with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Add Razorpay & Google script to <head>
if "checkout.razorpay.com" not in html:
    html = html.replace('</head>', '  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>\n  <script src="https://accounts.google.com/gsi/client" async defer></script>\n</head>')
    print("Added Razorpay & Google scripts to <head>")

# Add Pro button & Google auth to top-bar
old_actions = '''      <!-- Mobile Filters Trigger Button -->
      <button class="btn-filter-toggle" onclick="openFiltersModal()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
        <span>Filters</span>
      </button>
    </div>'''

new_actions = '''      <!-- Camouroles Pro Upgrade Trigger -->
      <button class="btn-pro-badge" id="top-pro-badge-btn" onclick="openPlansModal()" title="View Membership Plans & Unlock Roles">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        <span id="top-pro-label">Pro Upgrade</span>
      </button>

      <!-- Google Sign In Container -->
      <div class="google-auth-wrap" id="top-google-auth-wrap">
        <button class="btn-google-signin" id="btn-google-login" onclick="signInWithGoogle()" title="Sign in with Google">
          <svg width="14" height="14" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>
          <span id="google-btn-text">Sign In</span>
        </button>
      </div>

      <!-- Mobile Filters Trigger Button -->
      <button class="btn-filter-toggle" onclick="openFiltersModal()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
        <span>Filters</span>
      </button>
    </div>'''

if old_actions in html:
    html = html.replace(old_actions, new_actions)
    print("Added Pro button & Google auth to top-bar")

# Add the Plans & Pricing Modal right before </body>
plans_modal_html = """
  <!-- ==========================================================================
       PRIME PRO MEMBERSHIP & RAZORPAY CHECKOUT MODAL
       ========================================================================== -->
  <div class="job-modal-backdrop" id="plans-pricing-modal" onclick="if(event.target.id==='plans-pricing-modal') closePlansModal()">
    <div class="plans-modal-dialog" onclick="event.stopPropagation()">
      <button class="job-modal-close-btn" onclick="closePlansModal()" aria-label="Close"></button>

      <!-- Launch Week Offer Ribbon -->
      <div class="plans-offer-strip">
        <span>LAUNCH SPECIAL · 50% OFF UNLIMITED ACCESS</span>
        <span id="modal-offer-countdown">LIMITED TIME</span>
      </div>

      <div style="text-align:center; margin-bottom:14px;">
        <h2 style="font-family:'Newsreader',serif; font-size:26px; font-weight:700; color:var(--ink); margin:0 0 4px;">Camouroles Pro</h2>
        <p style="font-size:13px; color:var(--muted); margin:0;">Direct ATS links to 10,159+ live verified roles & priority AI recruiter guidance</p>
      </div>

      <!-- Segmented Plan Switcher -->
      <div class="plans-seg">
        <button class="plans-seg-btn active" id="seg-plan-month" onclick="selectPlan('month')">
          Monthly Pro (₹99)
          <small>Save 50% · ₹3.3/day</small>
        </button>
        <button class="plans-seg-btn" id="seg-plan-week" onclick="selectPlan('week')">
          Weekly Pass (₹49)
          <small>₹7/day · 7 days</small>
        </button>
      </div>

      <!-- Plan Features Card -->
      <div class="plan-card-body">
        <div class="plan-price-row">
          <span class="plan-price-val" id="plan-display-price">₹99</span>
          <span class="plan-price-was" id="plan-display-was">₹199</span>
          <span class="plan-price-tag" id="plan-display-tag">MOST POPULAR</span>
        </div>

        <div class="plan-feature-list">
          <div class="plan-feature-item">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Direct, unmasked application links to all 10,159+ verified positions (Greenhouse, Lever, Ashby, Workday)</span>
          </div>
          <div class="plan-feature-item">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Priority AI Recruiter dialogue, trade-off evaluations & customized role ranking</span>
          </div>
          <div class="plan-feature-item">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Autonomous In-RAM CV matching & skill radar across every active requisition</span>
          </div>
          <div class="plan-feature-item">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Continuous dead-link pruning protection (100% verified working URLs)</span>
          </div>
        </div>
      </div>

      <!-- Razorpay Pay CTA -->
      <button class="btn-razorpay-cta" id="btn-razorpay-submit" onclick="startRazorpayCheckout()">
        <span>Unlock Pro Access via Razorpay</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </button>

      <!-- Razorpay Authentic Trust Badge -->
      <div class="razorpay-trust-box">
        <div class="trust-shield-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div class="trust-text-area">
          <div class="trust-title">100% Secure Checkout by Razorpay</div>
          <div class="trust-chips">
            <span class="trust-chip">UPI · GPay / PhonePe</span>
            <span class="trust-chip">Cards</span>
            <span class="trust-chip">Net Banking</span>
            <span class="trust-chip">Wallets</span>
          </div>
          <div class="trust-sub">PCI-DSS Level 1 Compliant · 256-bit SSL encrypted</div>
        </div>
      </div>

    </div>
  </div>
"""

if "plans-pricing-modal" not in html:
    html = html.replace('</body>', plans_modal_html + '\n</body>')
    with open("static/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    with open("web/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Added plans-pricing-modal to HTML")
else:
    print("HTML already has plans-pricing-modal")
