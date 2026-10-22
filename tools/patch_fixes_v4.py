"""
Patch fixes for:
1. Tone down logo in static/styles.css (reduce size from 72px to 40px, remove gaudy drop-shadow and rotation)
2. Add inline CTA jump button styling in static/styles.css
3. Remove 70B AI tech jargon in static/index.html and static/app.js
4. Fix phantom 'Software Engineer 4yr' profile before CV upload in static/app.js
5. Make sure filtered results show directly on main page feed upon exiting or clicking CTA
"""

import os
import re

BASE_DIR = r"C:\Claude Work\camoroles"

# =========================================================================
# 1. PATCH static/styles.css
# =========================================================================
styles_path = os.path.join(BASE_DIR, "static", "styles.css")
with open(styles_path, "r", encoding="utf-8") as f:
    css = f.read()

# Replace .brand-emblem-hero block
old_emblem_block = """.hero-brand-emblem-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 14px;
}
.brand-emblem-hero {
  width: 72px;
  height: 72px;
  object-fit: contain;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), filter 0.25s ease;
  filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.5));
  cursor: pointer;
}
.brand-emblem-hero:hover {
  transform: scale(1.08) rotate(3deg);
}"""

new_emblem_block = """.hero-brand-emblem-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
}
.brand-emblem-hero {
  width: 40px;
  height: 40px;
  object-fit: contain;
  transition: opacity 0.2s ease, transform 0.2s ease;
  opacity: 0.92;
  cursor: pointer;
}
.brand-emblem-hero:hover {
  opacity: 1;
  transform: scale(1.04);
}"""

if old_emblem_block in css:
    css = css.replace(old_emblem_block, new_emblem_block)
    print("Patched .brand-emblem-hero in static/styles.css")
else:
    print("Warning: old_emblem_block not found in static/styles.css")

# Append CTA jump button styles if not present
jump_btn_css = """
/* CHATGPT INLINE JUMP TO MAIN FEED BUTTON */
.chatgpt-feed-jump-wrap {
  margin-top: 12px;
  display: flex;
  align-items: center;
}

.chatgpt-feed-jump-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--gold);
  color: #0E0F12 !important;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(197, 160, 89, 0.25);
}

.chatgpt-feed-jump-btn:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

[data-theme="light"] .chatgpt-feed-jump-btn {
  background: #701A2B !important;
  color: #FFFFFF !important;
  box-shadow: 0 4px 14px rgba(112, 26, 43, 0.2);
}
"""

if ".chatgpt-feed-jump-btn" not in css:
    css += jump_btn_css
    print("Added .chatgpt-feed-jump-btn to static/styles.css")

with open(styles_path, "w", encoding="utf-8") as f:
    f.write(css)

# =========================================================================
# 2. PATCH static/index.html
# =========================================================================
html_path = os.path.join(BASE_DIR, "static", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Remove 70B AI Engine buzzwords
old_disclaimer = "Direct Requisitions · Powered by Frontier 70B AI Engine · Zero Intermediaries"
new_disclaimer = "Direct Requisitions · Verified Engineering Openings · Zero Intermediaries"
if old_disclaimer in html:
    html = html.replace(old_disclaimer, new_disclaimer)
    print("Patched disclaimer in static/index.html")
else:
    print("Notice: old_disclaimer not found or already replaced in static/index.html")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

# =========================================================================
# 3. PATCH static/app.js
# =========================================================================
app_path = os.path.join(BASE_DIR, "static", "app.js")
with open(app_path, "r", encoding="utf-8") as f:
    app_js = f.read()

# Replace "Analyzing candidate profile with 70B AI engine..."
old_analyzing = "Analyzing candidate profile with 70B AI engine..."
new_analyzing = "Analyzing candidate profile..."
if old_analyzing in app_js:
    app_js = app_js.replace(old_analyzing, new_analyzing)
    print("Patched 'Analyzing candidate profile...' in static/app.js")

# Patch syncChatGptCvUI
old_sync_cv = """function syncChatGptCvUI(profile) {
  const titleEl = document.getElementById('chatgpt-cv-title-text');
  const descEl = document.getElementById('chatgpt-cv-desc-text');
  const pillEl = document.getElementById('chatgpt-cv-action-pill');

  if (profile) {
    const headline = profile.headline || 'Verified Engineer';
    const skills = (profile.skills || []).slice(0, 5).join(', ');
    const exp = profile.experienceText || `${profile.experienceYears || '4'}+ yrs`;
    if (titleEl) titleEl.textContent = `Active CV: ${headline}`;
    if (descEl) descEl.textContent = `${exp} · Skills: ${skills || 'Systems & Engineering'}`;
    if (pillEl) pillEl.textContent = 'Replace PDF';
  } else {
    if (titleEl) titleEl.textContent = 'Drop Candidate CV / Resume (PDF)';
    if (descEl) descEl.textContent = 'Automatic skill extraction, experience tiering, and instant ranking';
    if (pillEl) pillEl.textContent = 'Attach PDF';
  }
}"""

new_sync_cv = """function syncChatGptCvUI(profile) {
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
}"""

if old_sync_cv in app_js:
    app_js = app_js.replace(old_sync_cv, new_sync_cv)
    print("Patched syncChatGptCvUI in static/app.js")
else:
    print("Warning: old_sync_cv not found in static/app.js")

# Patch loadProfileData
old_load_profile = """async function loadProfileData() {
  // First restore from localStorage for instant persistent CV memory
  try {
    const cachedProfile = localStorage.getItem('camouroles_cv_profile');
    if (cachedProfile) {
      currentProfileData = JSON.parse(cachedProfile);
      const cachedMatches = localStorage.getItem('camouroles_cv_matches');
      if (cachedMatches) jobMatchesMap = JSON.parse(cachedMatches);

      updateHeroCvStatusUI(currentProfileData);
      syncProfileDataToUI(currentProfileData);
      applyFiltersAndRender();
    }
  } catch (e) {}

  try {
    const res = await fetch(`${API_BASE}/profile`);
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
    // Only set default profile if candidate has not uploaded their own CV
    if (!currentProfileData && data.profile) {
      currentProfileData = data.profile;
      syncProfileDataToUI(currentProfileData);
    }
    const box = document.getElementById('candidate-data-box');
    if (box) box.style.display = 'block';
    const candHead = document.getElementById('cand-headline');
    if (candHead) candHead.textContent = profile.headline;
    const candExp = document.getElementById('cand-exp');
    if (candExp) candExp.textContent = `${profile.years_of_experience || 0} years experience`;
    const skillsContainer = document.getElementById('cand-skills');
    if (skillsContainer && profile.skills) {
      skillsContainer.innerHTML = profile.skills.slice(0, 6).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
    }
    updateHeroCvStatusUI(profile);
    syncProfileDataToUI(profile);
  } catch (err) {}
}"""

new_load_profile = """async function loadProfileData() {
  // First restore from localStorage for instant persistent CV memory only if valid user profile
  try {
    const cachedProfile = localStorage.getItem('camouroles_cv_profile');
    if (cachedProfile) {
      const parsed = JSON.parse(cachedProfile);
      // Ensure it's not a legacy mock profile with Founding Engineer
      if (parsed && parsed.headline && !parsed.headline.includes('Founding Engineer / Full-Stack') && parsed.fileName) {
        currentProfileData = parsed;
        const cachedMatches = localStorage.getItem('camouroles_cv_matches');
        if (cachedMatches) jobMatchesMap = JSON.parse(cachedMatches);

        updateHeroCvStatusUI(currentProfileData);
        syncProfileDataToUI(currentProfileData);
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
    const res = await fetch(`${API_BASE}/profile`);
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
    // Only set profile if the backend explicitly reports has_cv: true and valid profile data
    if (data.has_cv && data.profile && data.profile.headline) {
      currentProfileData = data.profile;
      syncProfileDataToUI(currentProfileData);
      syncChatGptCvUI(currentProfileData);
    } else if (!currentProfileData) {
      // Ensure UI stays in clean pre-upload state
      syncProfileDataToUI(null);
      syncChatGptCvUI(null);
    }
  } catch (err) {
    if (!currentProfileData) {
      syncProfileDataToUI(null);
      syncChatGptCvUI(null);
    }
  }
}"""

if old_load_profile in app_js:
    app_js = app_js.replace(old_load_profile, new_load_profile)
    print("Patched loadProfileData in static/app.js")
else:
    print("Warning: old_load_profile not found in static/app.js")

# Patch deleteMyData
old_delete_data = """async function deleteMyData() {
  if (!confirm("Permanently wipe your CV profile and parsed in-memory attributes?")) return;
  try {
    await fetch(`${API_BASE}/profile`, { method: 'DELETE' });
  } catch (err) {}
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

  applyFiltersAndRender();
  renderProfileTopJobs();
}"""

new_delete_data = """async function deleteMyData() {
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
}"""

if old_delete_data in app_js:
    app_js = app_js.replace(old_delete_data, new_delete_data)
    print("Patched deleteMyData in static/app.js")
else:
    print("Warning: old_delete_data not found in static/app.js")

# Patch closeChatGptInterface and closeChatGptAndShowRoles
old_close_chat = """function closeChatGptInterface() {
  const portal = document.getElementById('chatgpt-fullscreen-interface');
  if (portal) portal.style.display = 'none';
  document.body.classList.remove('chatgpt-portal-active');
}

function closeChatGptAndShowRoles() {
  closeChatGptInterface();
  showView('feed');

  if (aiChatMatchedJobs && aiChatMatchedJobs.length) {
    currentFilteredJobs = aiChatMatchedJobs;
    renderedBatchLimit = 20;
    renderJobCards(currentFilteredJobs);
    const countEl = document.getElementById('feed-count');
    if (countEl) countEl.textContent = `${currentFilteredJobs.length} verified positions active`;
  } else {
    applyFiltersAndRender();
  }

  const container = document.getElementById('job-rows-container');
  if (container) {
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}"""

new_close_chat = """function closeChatGptInterface() {
  const portal = document.getElementById('chatgpt-fullscreen-interface');
  if (portal) portal.style.display = 'none';
  document.body.classList.remove('chatgpt-portal-active');
  showView('feed');

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
}"""

if old_close_chat in app_js:
    app_js = app_js.replace(old_close_chat, new_close_chat)
    print("Patched closeChatGptInterface & closeChatGptAndShowRoles in static/app.js")
else:
    print("Warning: old_close_chat not found in static/app.js")

# Patch submitChatGptMessage to inject jump button into agent bubble
old_agent_bubble = """    // Append Agent Row
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
      </div>
    `;"""

new_agent_bubble = """    // Direct button to show results on the main page feed
    const matchCount = (data.matched_job_ids && data.matched_job_ids.length)
      ? data.matched_job_ids.length
      : (data.total_matched || (currentFilteredJobs ? currentFilteredJobs.length : allJobsList.length));
    const jumpBtnHtml = `
      <div class="chatgpt-feed-jump-wrap">
        <button class="chatgpt-feed-jump-btn" onclick="closeChatGptAndShowRoles()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          <span>View Filtered Roles in Main Feed (${matchCount.toLocaleString()})</span>
        </button>
      </div>
    `;

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
    `;"""

if old_agent_bubble in app_js:
    app_js = app_js.replace(old_agent_bubble, new_agent_bubble)
    print("Patched agentRow in submitChatGptMessage in static/app.js")
else:
    print("Warning: old_agent_bubble not found in static/app.js")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_js)

print("Patching complete!")
