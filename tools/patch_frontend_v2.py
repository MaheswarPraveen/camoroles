import re

with open("static/app.js", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update matchesSearchQuery
old_search = '''// High-Precision Tokenized Search Across All Fields (Title, Company, Skills, Description, Location, Discipline, Portal)
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
}'''

new_search = '''// High-Precision Tokenized Search Across All Fields (Title, Company, Skills, Description, Location, Discipline, Portal)
function matchesSearchQuery(job, query) {
  if (!query || !query.trim()) return true;
  const qClean = query.trim().toLowerCase();

  // Intent words that candidates naturally type like "jobs", "openings", "roles"
  const STOP_WORDS = new Set([
    'jobs', 'job', 'openings', 'opening', 'roles', 'role', 'positions', 'position',
    'careers', 'career', 'vacancies', 'vacancy', 'hiring', 'looking', 'want',
    'at', 'in', 'for', 'with', 'and', 'or', 'the', 'a', 'an', 'to', 'of', 'from'
  ]);

  const rawTokens = qClean.split(/[\\s,+/|]+/).filter(Boolean);
  const meaningfulTokens = rawTokens.filter(t => !STOP_WORDS.has(t) && t.length > 1);
  const tokens = meaningfulTokens.length ? meaningfulTokens : rawTokens;
  if (!tokens.length) return true;

  const title = (job.title || '').toLowerCase();
  const company = (job.company || '').toLowerCase();
  const desc = (job.description || '').toLowerCase();
  const loc = (job.location || '').toLowerCase();
  const discipline = (job.discipline || '').toLowerCase();
  const portal = (job.portal || job.ats_type || '').toLowerCase();
  const skills = Array.isArray(job.skills) ? job.skills.join(' ').toLowerCase() : String(job.skills || '').toLowerCase();

  // 1. Instant substring match across any core field
  if (title.includes(qClean) || company.includes(qClean) || skills.includes(qClean) || loc.includes(qClean) || desc.includes(qClean)) {
    return true;
  }

  // 2. Composite search corpus
  const fullText = `${title} ${company} ${discipline} ${skills} ${loc} ${portal} ${desc}`;
  return tokens.every(token => fullText.includes(token));
}'''

if old_search in code:
    code = code.replace(old_search, new_search)
    print("Updated matchesSearchQuery")
else:
    print("WARNING: matchesSearchQuery not found exactly")

# 2. Update onCvSelected to persist profile in memory and localStorage
old_cv_select = '''    // Render candidate profile
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
    }'''

new_cv_select = '''    // Render candidate profile
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
    }'''

if old_cv_select in code:
    code = code.replace(old_cv_select, new_cv_select)
    print("Updated onCvSelected")
else:
    print("WARNING: onCvSelected not found exactly")

# 3. Update heroChatCriteria definition and updateHeroChatCount
old_criteria = '''let heroChatHistory = [];
let heroChatCriteria = {
  discipline: 'all',
  location: 'all',
  maxExp: 10,
  keywords: ''
};'''

new_criteria = '''let heroChatHistory = [];
let heroChatCriteria = {
  discipline: 'all',
  location: 'all',
  company: 'all',
  maxExp: 10,
  keywords: ''
};'''

if old_criteria in code:
    code = code.replace(old_criteria, new_criteria)
    print("Updated heroChatCriteria")
else:
    print("WARNING: heroChatCriteria not found")

old_count_fn = '''function updateHeroChatCount() {
  let count = 0;
  for (let i = 0; i < allJobsList.length; i++) {
    const j = allJobsList[i];
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
    const dName = formatPillName(heroChatCriteria.discipline);
    const lName = formatPillName(heroChatCriteria.location);
    if (heroChatCriteria.discipline !== 'all' && heroChatCriteria.location !== 'all') {
      hintEl.textContent = `Focused on ${dName} in ${lName}`;
    } else if (heroChatCriteria.discipline !== 'all') {
      hintEl.textContent = `Focused on ${dName} positions`;
    } else if (heroChatCriteria.location !== 'all') {
      hintEl.textContent = `Filtered for ${lName} locations`;
    } else if (heroChatCriteria.keywords) {
      hintEl.textContent = `Matched for "${heroChatCriteria.keywords}"`;
    } else {
      hintEl.textContent = `Matches update live with each message`;
    }
  }
}'''

new_count_fn = '''function updateHeroChatCount() {
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
    } else if (heroChatCriteria.discipline !== 'all' && heroChatCriteria.location !== 'all') {
      hintEl.textContent = `Focused on ${formatPillName(heroChatCriteria.discipline)} in ${formatPillName(heroChatCriteria.location)}`;
    } else if (heroChatCriteria.discipline !== 'all') {
      hintEl.textContent = `Focused on ${formatPillName(heroChatCriteria.discipline)} positions`;
    } else if (heroChatCriteria.location !== 'all') {
      hintEl.textContent = `Filtered for ${formatPillName(heroChatCriteria.location)} locations`;
    } else if (heroChatCriteria.keywords) {
      hintEl.textContent = `Matched for "${heroChatCriteria.keywords}"`;
    } else {
      hintEl.textContent = `Matches update live with each message`;
    }
  }
}'''

if old_count_fn in code:
    code = code.replace(old_count_fn, new_count_fn)
    print("Updated updateHeroChatCount")
else:
    print("WARNING: updateHeroChatCount not found")

# 4. Update applyLlmControlToWebpage
old_apply_llm = '''function applyLlmControlToWebpage(data) {
  if (!data) return;

  // 1. Direct search query filter
  if (data.query !== undefined) {
    activeFilters.q = data.query;
    const deskInput = document.getElementById('desktop-search-input');
    if (deskInput) deskInput.value = data.query;
    const mobInput = document.getElementById('mobile-search-input');
    if (mobInput) mobInput.value = data.query;
  }

  // 2. Direct discipline filter
  if (data.discipline && data.discipline !== 'all') {
    activeFilters.discipline = data.discipline;
    document.querySelectorAll('[data-discipline]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-discipline') === data.discipline);
    });
  } else if (data.discipline === 'all') {
    activeFilters.discipline = 'all';
    document.querySelectorAll('[data-discipline]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-discipline') === 'all');
    });
  }

  // 3. Direct location filter
  if (data.location && data.location !== 'all') {
    activeFilters.location = data.location;
    document.querySelectorAll('[data-location]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-location') === data.location);
    });
  } else if (data.location === 'all') {
    activeFilters.location = 'all';
    document.querySelectorAll('[data-location]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-location') === 'all');
    });
  }

  // 4. Inject matched jobs into jobMatchesMap with high-conviction scores
  if (data.matched_jobs && data.matched_jobs.length > 0) {
    data.matched_jobs.forEach((j, idx) => {
      const computedScore = j.match_score || 0;
      jobMatchesMap[j.id] = {
        score: computedScore,
        explanation: j.match_reason || `AI Recruiter match for ${data.query || 'profile'}`
      };
    });
  }

  updateActivePills();
  applyFiltersAndRender();

  // 5. Update UI counters to reflect AI recruiter control
  const feedCountEl = document.getElementById('feed-count');
  if (feedCountEl) {
    feedCountEl.innerHTML = `<strong>${currentFilteredJobs.length.toLocaleString()} roles</strong> · Filtered & Ranked by AI Recruiter`;
  }

  const heroResultsBtn = document.getElementById('hero-results-btn-label');
  if (heroResultsBtn) {
    heroResultsBtn.textContent = `View Ranked Feed (${currentFilteredJobs.length.toLocaleString()}) ↓`;
  }
}'''

new_apply_llm = '''function applyLlmControlToWebpage(data) {
  if (!data) return;

  // 1. Direct company filter (strict brand matching from AI)
  if (data.target_company) {
    activeFilters.company = data.target_company;
    heroChatCriteria.company = data.target_company;
  } else if (data.target_company === '') {
    // If explicitly empty, don't force company
    heroChatCriteria.company = 'all';
  }

  // 2. Direct search query filter
  if (data.query !== undefined) {
    activeFilters.q = data.query;
    heroChatCriteria.keywords = data.query;
    const deskInput = document.getElementById('desktop-search-input');
    if (deskInput) deskInput.value = data.query;
    const mobInput = document.getElementById('mobile-search-input');
    if (mobInput) mobInput.value = data.query;
  }

  // 3. Direct discipline filter
  if (data.discipline && data.discipline !== 'all') {
    activeFilters.discipline = data.discipline;
    heroChatCriteria.discipline = data.discipline;
    document.querySelectorAll('[data-discipline]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-discipline') === data.discipline);
    });
  } else if (data.discipline === 'all') {
    activeFilters.discipline = 'all';
    heroChatCriteria.discipline = 'all';
    document.querySelectorAll('[data-discipline]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-discipline') === 'all');
    });
  }

  // 4. Direct location filter
  if (data.location && data.location !== 'all') {
    activeFilters.location = data.location;
    heroChatCriteria.location = data.location;
    document.querySelectorAll('[data-location]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-location') === data.location);
    });
  } else if (data.location === 'all') {
    activeFilters.location = 'all';
    heroChatCriteria.location = 'all';
    document.querySelectorAll('[data-location]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-location') === 'all');
    });
  }

  // 5. Inject matched jobs into jobMatchesMap with honest scores
  if (data.matched_jobs && data.matched_jobs.length > 0) {
    aiChatMatchedJobs = data.matched_jobs;
    data.matched_jobs.forEach((j) => {
      const computedScore = j.match_score || 0;
      jobMatchesMap[j.id] = {
        score: computedScore,
        explanation: j.match_reason || `AI Recruiter match for ${data.query || data.target_company || 'verified requisition'}`
      };
    });
  }

  updateActivePills();
  applyFiltersAndRender();
  updateHeroChatCount();

  // 6. Update UI counters to reflect AI recruiter control
  const feedCountEl = document.getElementById('feed-count');
  if (feedCountEl) {
    feedCountEl.innerHTML = `<strong>${currentFilteredJobs.length.toLocaleString()} roles</strong> · Filtered & Ranked by AI Recruiter`;
  }

  const heroResultsBtn = document.getElementById('hero-results-btn-label');
  if (heroResultsBtn) {
    const totalMatchCount = data.total_matches || (data.matched_jobs ? data.matched_jobs.length : currentFilteredJobs.length);
    heroResultsBtn.textContent = `View Matching Roles (${totalMatchCount.toLocaleString()}) ↓`;
  }
}'''

if old_apply_llm in code:
    code = code.replace(old_apply_llm, new_apply_llm)
    print("Updated applyLlmControlToWebpage")
else:
    print("WARNING: applyLlmControlToWebpage not found")

# 5. Update applyAiChatResultsAndScroll
old_scroll_fn = '''function applyAiChatResultsAndScroll() {
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
  applyFiltersAndRender();

  // Scroll to results feed smoothly
  const target = document.getElementById('job-rows-container') || document.querySelector('.feed-column');
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}'''

new_scroll_fn = '''function applyAiChatResultsAndScroll() {
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
}'''

if old_scroll_fn in code:
    code = code.replace(old_scroll_fn, new_scroll_fn)
    print("Updated applyAiChatResultsAndScroll")
else:
    print("WARNING: applyAiChatResultsAndScroll not found")

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(code)

with open("web/app.js", "w", encoding="utf-8") as f:
    f.write(code)

print("SUCCESS: static/app.js and web/app.js updated!")
