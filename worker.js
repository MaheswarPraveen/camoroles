/**
 * Camouroles Cloudflare Worker (workers.dev)
 * 
 * Luxury Tech Job Discovery Platform
 * - Edge Static Asset Delivery via env.ASSETS
 * - Live Razorpay Order Creation & HMAC-SHA256 Verification
 * - Google Identity Services Authentication
 * - High-Speed Supabase Database Querying with Edge Caching
 * - AI Recruiter Dialogue (Zero Emojis, Candid Career Guidance)
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type, x-device',
  'Access-Control-Max-Age': '86400',
};

// Visitor identity for rate limits: the Pages proxy forwards the real IP with a shared key.
function clientKey(req, env) {
  const viaProxy = env.PROXY_KEY && req.headers.get('x-proxy-key') === env.PROXY_KEY;
  return (viaProxy && req.headers.get('x-client-ip')) || req.headers.get('cf-connecting-ip') || 'unknown';
}

async function overLimit(limiter, key) {
  if (!limiter) return false; // binding missing (e.g. local dev): don't block
  try {
    const { success } = await limiter.limit({ key });
    return !success;
  } catch (e) {
    return false;
  }
}

function jsonResponse(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...CORS_HEADERS,
      ...extraHeaders,
    },
  });
}

function errorResponse(detail, status = 400) {
  return jsonResponse({ detail, error: detail }, status);
}

// In-Worker memory cache for instantaneous responses
let cachedJobs = null;
let cachedJobsTime = 0;
const CACHE_TTL_MS = 2 * 60 * 60 * 1000; // 2 hours in-memory edge cache

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);

    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // ------------------------------------------------------------------------
    // API ENDPOINTS
    // ------------------------------------------------------------------------
    if (url.pathname.startsWith('/api/')) {
      try {
        // Upstream backend proxy fallback (if configured)
        if (env.BACKEND_UPSTREAM) {
          const target = env.BACKEND_UPSTREAM.replace(/\/+$/, '') + url.pathname + url.search;
          const headers = new Headers(req.headers);
          headers.delete('host');
          return fetch(target, {
            method: req.method,
            headers,
            body: ['GET', 'HEAD'].includes(req.method) ? undefined : req.body,
          });
        }

        // 1. GET /api/jobs -> Full verified job feed
        if (url.pathname === '/api/jobs' && req.method === 'GET') {
          return await handleGetJobs(req, env);
        }

        // 1b. GET /api/geo -> Fast edge geolocation without bypassing jobs CDN cache
        if (url.pathname === '/api/geo' && req.method === 'GET') {
          const clientCountry = req?.cf?.country || req?.headers?.get('cf-ipcountry') || null;
          const clientCity = req?.cf?.city || null;
          const clientTimezone = req?.cf?.timezone || null;
          return jsonResponse({
            country: clientCountry,
            city: clientCity,
            timezone: clientTimezone
          }, 200, { 'Cache-Control': 'no-store' });
        }

        // 2. POST /api/checkout/order -> Live Razorpay order creation
        if (url.pathname === '/api/checkout/order' && req.method === 'POST') {
          return await handleCreateOrder(req, env);
        }

        // 3. POST /api/checkout/verify -> HMAC-SHA256 payment verification
        if (url.pathname === '/api/checkout/verify' && req.method === 'POST') {
          return await handleVerifyPayment(req, env);
        }

        // 3b. POST /api/razorpay/webhook -> server-to-server payment confirmation
        if (url.pathname === '/api/razorpay/webhook' && req.method === 'POST') {
          return await handleRazorpayWebhook(req, env);
        }

        // 4. POST /api/auth/google -> Google OAuth identity exchange
        if (url.pathname === '/api/auth/google' && req.method === 'POST') {
          return await handleGoogleAuth(req, env);
        }

        // 5. GET /api/profile -> User entitlements and candidate memory
        if (url.pathname === '/api/profile' && req.method === 'GET') {
          return await handleGetProfile(req, env);
        }

        // Rate limits on the endpoints that spend AI calls
        if (['/api/ai/recruiter_chat', '/api/recruiter-chat', '/api/cv/match', '/api/cv-match'].includes(url.pathname) && req.method === 'POST') {
          const isCv = url.pathname.includes('cv');
          const who = clientKey(req, env);
          if (await overLimit(isCv ? env.CV_LIMIT : env.AI_LIMIT, who) || await overLimit(env.AI_GLOBAL_LIMIT, 'global')) {
            return jsonResponse({ detail: 'Too many requests. Please wait a minute and try again.', error: 'rate_limited' }, 429, { 'Retry-After': '60' });
          }
        }

        // 6. POST /api/ai/recruiter_chat -> AI Recruiter dialogue
        if ((url.pathname === '/api/ai/recruiter_chat' || url.pathname === '/api/recruiter-chat') && req.method === 'POST') {
          return await handleRecruiterChat(req, env);
        }

        // 7. POST /api/cv/match or /api/cv-match -> In-memory CV match scoring
        if ((url.pathname === '/api/cv/match' || url.pathname === '/api/cv-match') && req.method === 'POST') {
          return await handleCvMatch(req, env);
        }

        // 9. Free apply limits (2 signed out, 5 signed in, unlimited on Pro)
        if (url.pathname === '/api/apply' && req.method === 'POST') {
          return await handleApply(req, env);
        }
        if (url.pathname === '/api/apply/status' && req.method === 'GET') {
          return await handleApplyStatus(req, env, url);
        }

        // 8. POST /api/ai/jev_filter -> Jev System One Decision Engine
        if (url.pathname === '/api/ai/jev_filter' && req.method === 'POST') {
          return await handleJevFilter(req, env);
        }

        return errorResponse(`Route not found: ${url.pathname}`, 404);
      } catch (err) {
        return errorResponse(err.message || 'Internal Edge Error', 500);
      }
    }

    // ------------------------------------------------------------------------
    // STATIC ASSETS SERVING
    // ------------------------------------------------------------------------
    // Rewrite /static/styles.css -> /styles.css for asset binding
    if (url.pathname.startsWith('/static/')) {
      const assetUrl = new URL(req.url);
      assetUrl.pathname = url.pathname.replace(/^\/static/, '');
      return env.ASSETS.fetch(new Request(assetUrl, req));
    }

    return env.ASSETS.fetch(req);
  },
};

// ============================================================================
// 1. JOBS FEED HANDLER (Supabase + Edge Cache)
// ============================================================================
async function handleGetJobs(req, env) {
  if (!env && req && typeof req === 'object' && ('SUPABASE_URL' in req || 'SUPABASE_SERVICE_ROLE_KEY' in req || 'ASSETS' in req || 'OPENROUTER_API_KEY' in req)) {
    env = req;
    req = null;
  }
  const clientCountry = req?.cf?.country || req?.headers?.get('cf-ipcountry') || null;
  const clientCity = req?.cf?.city || null;
  const clientTimezone = req?.cf?.timezone || null;
  const geo = {
    country: clientCountry,
    city: clientCity,
    timezone: clientTimezone
  };

  const now = Date.now();
  if (cachedJobs && now - cachedJobsTime < CACHE_TTL_MS) {
    return jsonResponse(
      { totalVerified: cachedJobs.length, jobs: publicJobs(cachedJobs, env), geo },
      200,
      { 'Cache-Control': 'public, max-age=1800, s-maxage=3600, stale-while-revalidate=86400' }
    );
  }

  try {
    const sbUrl = env.SUPABASE_URL || 'https://xteoktfzftqybflpubvo.supabase.co';
    const sbKey = env.SUPABASE_SERVICE_ROLE_KEY || env.SUPABASE_ANON_KEY;

    if (!sbKey) {
      return errorResponse('Supabase key not configured on worker', 500);
    }

    // Fetch all verified active positions across all offsets (complete 10,200+ inventory)
    const offsets = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000];
    const pagePromises = offsets.map(async offset => {
      const queryUrl = `${sbUrl}/rest/v1/jobs?is_active=eq.true&order=created_at.desc&limit=1000&offset=${offset}&select=id,title,company,ats_type,location,is_remote,experience_min,experience_max,skills,apply_url,last_verified_at,created_at`;
      try {
        const res = await fetch(queryUrl, {
          headers: {
            'apikey': sbKey,
            'Authorization': `Bearer ${sbKey}`,
            'Accept': 'application/json',
          },
        });
        if (!res.ok) return [];
        return await res.json();
      } catch (e) {
        return [];
      }
    });

    const pageResults = await Promise.all(pagePromises);
    const rawRows = pageResults.flat();
    const GENERIC_COMPANIES = new Set(['startup', 'company', 'confidential', 'stealth', 'stealth startup', 'leading tech company']);
    const jobs = rawRows
      .filter(j => {
        const comp = (j.company || '').trim().toLowerCase();
        return comp && !GENERIC_COMPANIES.has(comp) && comp.length >= 3;
      })
      .map(j => {
        const title = j.title || 'Engineering Specialist';
        const comp = j.company || 'Frontier Lab';
        const skills = j.skills || [];
        const minExp = j.experience_min || 0;
        const maxExp = j.experience_max || 3;
        const rawUrl = j.apply_url || '';
        const resolvedUrl = resolveDirectApplyUrl(rawUrl, comp, title);

        return {
          id: j.id,
          title,
          company: comp,
          location: j.location || 'Worldwide Remote',
          hub: j.location || 'Worldwide Remote',
          discipline: inferDiscipline(title, skills, comp),
          minExp,
          maxExp,
          expText: `${minExp} - ${maxExp} yrs`,
          skills,
          portal: j.ats_type || 'direct',
          applyUrl: resolvedUrl,
          verifiedActiveAt: j.last_verified_at || j.created_at,
          isRemote: Boolean(j.is_remote),
          is_remote: Boolean(j.is_remote),
          atsType: j.ats_type || 'direct',
        };
      });

    if (jobs.length) { // never cache an empty list from a failed read
      cachedJobs = jobs;
      cachedJobsTime = now;
    }

    return jsonResponse(
      {
        totalVerified: jobs.length,
        jobs: publicJobs(jobs, env),
        geo
      },
      200,
      { 'Cache-Control': 'public, max-age=1800, s-maxage=3600, stale-while-revalidate=86400' }
    );
  } catch (err) {
    console.error('Error in handleGetJobs:', err);
    return errorResponse(err.message || 'Error fetching jobs', 500);
  }
}

function resolveDirectApplyUrl(applyUrl, company, title) {
  const comp = (company || '').toLowerCase();
  const t = encodeURIComponent(title || '');
  const url = applyUrl || '';
  
  if (!url || url.includes('linkedin.com') || !url.startsWith('http')) {
    if (comp.includes('nvidia')) {
      return `https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite?q=${t}`;
    }
    if (comp.includes('apple')) {
      return `https://jobs.apple.com/en-us/search?search=${t}`;
    }
    if (comp.includes('meta') || comp.includes('facebook') || comp.includes('reality labs')) {
      return `https://www.metacareers.com/jobs?q=${t}`;
    }
    if (comp.includes('google') || comp.includes('alphabet') || comp.includes('waymo')) {
      return `https://www.google.com/about/careers/applications/jobs/results/?q=${t}`;
    }
    if (comp.includes('microsoft')) {
      return `https://jobs.careers.microsoft.com/global/en/search?q=${t}`;
    }
    if (comp.includes('tesla')) {
      return `https://www.tesla.com/careers/search/?query=${t}`;
    }
    if (comp.includes('amazon') || comp.includes('aws')) {
      return `https://www.amazon.jobs/en/search?base_query=${t}`;
    }
    if (comp.includes('netflix')) {
      return `https://jobs.netflix.com/search?q=${t}`;
    }
    if (comp.includes('uber')) {
      return `https://www.uber.com/us/en/careers/list/?query=${t}`;
    }
  }
  return url;
}

// Disqualification patterns for non-technical roles when candidate is looking for tech/engineering
const NON_TECH_TITLE_PATTERNS = [
  /\bparalegal\b/i,
  /\blegal\b/i,
  /\bcounsel\b/i,
  /\battorney\b/i,
  /\blawyer\b/i,
  /\bcompliance\b/i,
  /\brecruiter\b/i,
  /\brecruiting\b/i,
  /\btalent\b/i,
  /\bsourcer\b/i,
  /\bhuman resources\b/i,
  /\bhr\b/i,
  /\bcoordinator\b/i,
  /\baccountant\b/i,
  /\baccounting\b/i,
  /\bbookkeeper\b/i,
  /\bpayroll\b/i,
  /\bcontroller\b/i,
  /\btreasury\b/i,
  /\bfinancial operations\b/i,
  /\bfinops\b/i,
  /\bfinance\b/i,
  /\bsales\b/i,
  /\bmarketing\b/i,
  /\baccount executive\b/i,
  /\bbusiness development\b/i,
  /\bbusiness operations\b/i,
  /\bmedical assistant\b/i,
  /\bnurse\b/i,
  /\breceptionist\b/i,
  /\boffice manager\b/i,
  /\bexecutive assistant\b/i,
  /\badministrative assistant\b/i,
  /\bstore manager\b/i,
  /\bretail specialist\b/i,
  /\bretail\b/i,
  /\bcredit risk\b/i,
  /\bunderwriter\b/i,
  /\bclaims\b/i,
  /\bprogram manager\b/i,
  /\bproduct manager\b/i,
  /\boperations planning\b/i,
  /\boperations lead\b/i,
  /\bproject manager\b/i,
  /\baccount manager\b/i,
  /\bcustomer success\b/i,
  /\binterpreter\b/i,
  /\btranslator\b/i,
  /\blinguist\b/i,
  /\btranscription\b/i,
  /\bwarehouse\b/i,
  /\bforklift\b/i,
  /\bshipping\b/i,
  /\breceiving\b/i,
  /\blogistics associate\b/i,
  /\bmaterials associate\b/i,
  /\binventory\b/i,
  /\binstructor\b/i,
  /\bteacher\b/i,
  /\btutor\b/i,
  /\bcurriculum\b/i,
  /\btrainer\b/i,
  /\bcoach\b/i,
  /\bdriver\b/i,
  /\bcourier\b/i,
  /\bclerk\b/i,
  /\bcustodian\b/i,
  /\bjanitor\b/i,
  /\bcashier\b/i,
  /\bbarista\b/i,
  /\bcrew member\b/i,
  /\bsecurity guard\b/i,
  /\bfacilities\b/i,
  /\bmaintenance technician\b/i,
  /\bcustomer service\b/i,
  /\bcustomer support\b/i,
  /\bsupport specialist\b/i
];

const DISCIPLINE_PATTERNS = {
  frontend: /\b(frontend|front[- ]end|react|vue|angular|svelte|web developer|web dev|javascript|typescript|flutter|ios|android|mobile developer|swift|kotlin)\b/i,
  backend: /\b(backend|back[- ]end|golang|go engineer|rust|distributed systems|microservices|cloud|api|node|server|database|infra|infrastructure|devops|sre|kubernetes)\b/i,
  ai: /\b(ai|artificial intelligence|machine learning|deep learning|ml engineer|llm|frontier model|nlp|computer vision|genai|research scientist|data scientist)\b/i,
  robotics: /\b(robot|robotics|autonomy|autonomous|ros|ros2|ardupilot|px4|uav|drone|mechatronics|kinematics|slam|motion planning)\b/i,
  trading: /\b(trading|quant|quantitative|hft|high frequency|low latency|market making|execution|order book)\b/i,
  hardware: /\b(hardware|asic|fpga|silicon|rtl|soc|risc-v|semiconductor|vlsi|circuits|pcb)\b/i,
  propulsion: /\b(propulsion|aerospace|rocket|orbital|satellite|turbomachinery|spacecraft|avionics)\b/i,
  quantum: /\b(quantum|qubit|cryogenic|qiskit|quantum error)\b/i,
  biotech: /\b(biotech|crispr|genomics|cell therapy|bioinformatics|molecular|protein|dna)\b/i,
  crypto: /\b(crypto|web3|blockchain|zero knowledge|zkp|snark|stark|smart contracts)\b/i,
  energy: /\b(energy|fusion|nuclear|geothermal|plasma|cleantech|battery|clean power)\b/i,
  maritime: /\b(maritime|ocean|submersible|auv|rov|underwater|sonar)\b/i,
  security: /\b(security|infosec|cybersecurity|appsec|pentest|cloud security)\b/i,
  safety: /\b(safety|fire|ehs|hazard|process safety|systems safety|flight safety|system safety|mission assurance|reliability)\b/i,
};

function detectRequestedDiscipline(text) {
  const t = (text || '').toLowerCase();
  for (const [disc, pattern] of Object.entries(DISCIPLINE_PATTERNS)) {
    if (pattern.test(t)) {
      return disc;
    }
  }
  return null;
}

const LOCATION_PATTERNS = {
  worldwide_remote: /\b(remote|anywhere|wfh|home)\b/i,
  uae: /\b(dubai|uae|abu dhabi|middle east|saudi|riyadh|neom)\b/i,
  india: /\b(india|bangalore|bengaluru|hyderabad|pune|delhi|noida|gurgaon)\b/i,
  sf_bay: /\b(sf|san francisco|bay area|silicon valley|palo alto|mountain view|sunnyvale|san jose|berkeley)\b/i,
  seattle: /\b(seattle|bellevue|redmond)\b/i,
  nyc: /\b(new york|nyc|manhattan|brooklyn)\b/i,
  austin: /\b(austin|texas|dallas|houston)\b/i,
  london: /\b(london|uk|united kingdom|cambridge|oxford)\b/i,
  germany: /\b(germany|berlin|munich|frankfurt)\b/i,
  singapore: /\b(singapore)\b/i,
  tokyo: /\b(tokyo|japan)\b/i,
  switzerland: /\b(zurich|switzerland|geneva)\b/i,
  canada: /\b(canada|toronto|vancouver|montreal|waterloo)\b/i,
  australia: /\b(australia|sydney|melbourne)\b/i,
  france: /\b(france|paris|lyon|marseille|toulouse)\b/i
};

function detectRequestedLocation(text) {
  const t = (text || '').toLowerCase();
  for (const [locKey, pattern] of Object.entries(LOCATION_PATTERNS)) {
    if (pattern.test(t)) {
      return locKey;
    }
  }
  return null;
}

function formatLocationName(locKey) {
  const names = {
    worldwide_remote: 'Worldwide Remote',
    uae: 'UAE & Dubai',
    india: 'India',
    sf_bay: 'SF Bay Area',
    seattle: 'Seattle',
    nyc: 'New York City',
    austin: 'Austin & Texas',
    london: 'London & UK',
    germany: 'Germany',
    singapore: 'Singapore',
    tokyo: 'Tokyo',
    switzerland: 'Switzerland',
    canada: 'Canada',
    australia: 'Australia',
    france: 'France'
  };
  return names[locKey] || locKey;
}

function inferDiscipline(title, skills, company) {
  const t = (title || '').toLowerCase();
  const c = (company || '').toLowerCase();

  // 1. Immediately disqualify non-technical roles
  if (NON_TECH_TITLE_PATTERNS.some(rx => rx.test(t))) return 'operations';

  // 2. Strict pattern matching on title
  if (/\b(safety|fire|ehs|hazard|system safety|systems safety|flight safety|process safety|mission assurance)\b/i.test(t)) return 'safety';
  if (/\b(robot|robotics|autonomy|autonomous|ros|ros2|slam|mechatronics|kinematics|ardupilot|px4|uav|drone)\b/i.test(t)) return 'robotics';
  if (/\b(bio|crispr|genom|cell therapy|protein|dna|rna|bioinformatics)\b/i.test(t)) return 'biotech';
  if (/\b(quantum|qubit|cryo|microwave|qiskit|qec)\b/i.test(t)) return 'quantum';
  if (/\b(propulsion|rocket|orbital|turbomachinery|avionics|spacecraft)\b/i.test(t) || (/\b(aerospace|space)\b/i.test(t) && /\b(engineer|lead|architect|scientist)\b/i.test(t))) return 'propulsion';
  if (/\b(maritime|submersible|auv|rov|sonar)\b/i.test(t) || (/\b(ocean|marine)\b/i.test(t) && /\b(engineer|robotics|systems)\b/i.test(t))) return 'maritime';
  if (/\b(fusion|nuclear|plasma|reactor|tokamak|geothermal)\b/i.test(t)) return 'energy';
  if (/\b(asic|fpga|rtl|silicon|soc|verilog|risc-v|semiconductor|vlsi)\b/i.test(t) || (/\bhardware\b/i.test(t) && /\b(engineer|architect|lead)\b/i.test(t))) return 'hardware';
  if (/\b(hft|trading|low latency|kernel bypass|dpdk|order book|market making)\b/i.test(t) || (/\bquant\b/i.test(t) && /\b(engineer|researcher|strategist|developer)\b/i.test(t))) return 'trading';
  if (/\b(zero knowledge|zk-|zkp|snark|stark|cryptograph)\b/i.test(t)) return 'crypto';
  
  // AI & Machine Learning (strict word boundaries - avoid matching "retail", "maintenance", "detail")
  if (/\b(ai|artificial intelligence|machine learning|deep learning|llm|computer vision|nlp|neural|genai)\b/i.test(t) || /\b(data scientist|research scientist|ml engineer)\b/i.test(t)) return 'ai';

  // Frontend (strict word boundaries - avoid matching "recruiter", "equity")
  if (/\b(frontend|front[- ]end|react|vue|angular|flutter|ios|android|swift|kotlin)\b/i.test(t) || /\b(ui|ux)\b/i.test(t) || (/\bweb\b/i.test(t) && /\b(developer|engineer|lead)\b/i.test(t))) return 'frontend';

  // Company domain heuristics ONLY for engineering/technical titles
  const isEngineerTitle = /\b(engineer|developer|architect|researcher|scientist|lead|tech lead|programmer|swe)\b/i.test(t);
  if (isEngineerTitle) {
    if (/\b(robotics|boston dynamics|figure|physical intelligence|skydio|zoox|waymo|nuro)\b/i.test(c)) return 'robotics';
    if (/\b(groq|tenstorrent|cerebras)\b/i.test(c)) return 'hardware';
    if (/\b(citadel|jane street|optiver|jump)\b/i.test(c)) return 'trading';
    if (/\b(helion|fervo|oklo)\b/i.test(c)) return 'energy';
    if (/\b(saildrone)\b/i.test(c)) return 'maritime';
    if (/\b(rigetti|ionq|quera)\b/i.test(c)) return 'quantum';
    if (/\b(starkware|succinct)\b/i.test(c)) return 'crypto';
    return 'backend';
  }

  // Backend / Cloud / Infrastructure explicit check
  if (/\b(backend|back[- ]end|golang|go|rust|distributed|microservices|cloud|api|node|server|database|infra|infrastructure|devops|sre|kubernetes|platform|systems)\b/i.test(t)) {
    return 'backend';
  }

  return 'operations';
}

// ============================================================================
// 2. RAZORPAY ORDER CREATION
// ============================================================================
// Verifies the Supabase access token sent by the browser and returns the user, or null.
async function getAuthUser(req, env) {
  const authHeader = req?.headers?.get('Authorization') || '';
  if (!authHeader.startsWith('Bearer ')) return null;
  const token = authHeader.slice(7).trim();
  if (!token || token.split('.').length !== 3) return null;
  const sbUrl = env.SUPABASE_URL || 'https://xteoktfzftqybflpubvo.supabase.co';
  const apiKey = env.SUPABASE_ANON_KEY || env.SUPABASE_SERVICE_ROLE_KEY;
  try {
    const res = await fetch(`${sbUrl}/auth/v1/user`, {
      headers: { 'apikey': apiKey, 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) return null;
    const u = await res.json();
    return u && u.id ? u : null;
  } catch (e) {
    return null;
  }
}

function sbAdmin(env, path, init = {}) {
  const sbUrl = env.SUPABASE_URL || 'https://xteoktfzftqybflpubvo.supabase.co';
  const sbKey = env.SUPABASE_SERVICE_ROLE_KEY;
  return fetch(`${sbUrl}/rest/v1/${path}`, {
    ...init,
    headers: {
      'apikey': sbKey,
      'Authorization': `Bearer ${sbKey}`,
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
  });
}

const PLAN_PRICES = { week: { paise: 2900, days: 7 }, month: { paise: 9900, days: 30 } };

// Browser id used for guest purchases and free-apply counts (crypto.randomUUID from the page).
const DEVICE_RX = /^[A-Za-z0-9-]{8,64}$/;
function cleanDeviceId(v) {
  const id = String(v || '').trim();
  return DEVICE_RX.test(id) ? id : '';
}

async function handleCreateOrder(req, env) {
  // Signing in is optional: a guest's Pro is kept on their browser's device id until they sign in.
  const user = await getAuthUser(req, env);
  if (!env.SUPABASE_SERVICE_ROLE_KEY) return errorResponse('Database key not configured on worker', 500);

  const body = await req.json().catch(() => ({}));
  const deviceId = cleanDeviceId(body.device_id);
  if (!user && !deviceId) return errorResponse('Could not identify this browser. Refresh and try again.', 400);
  const plan = body.plan === 'week' ? 'week' : 'month';
  const amountPaise = PLAN_PRICES[plan].paise; // Rs 29 or Rs 99

  const rzpKey = env.RAZORPAY_KEY_ID || 'rzp_live_TjW0ZP4t3xCyrO';
  const rzpSecret = env.RAZORPAY_KEY_SECRET;
  if (!rzpSecret) {
    return errorResponse('Razorpay secret key not configured on worker', 500);
  }

  const authHeader = 'Basic ' + btoa(`${rzpKey}:${rzpSecret}`);
  const rzpRes = await fetch('https://api.razorpay.com/v1/orders', {
    method: 'POST',
    headers: {
      'Authorization': authHeader,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      amount: amountPaise,
      currency: 'INR',
      receipt: `rcpt_${Date.now()}`,
      notes: { plan, user_id: user?.id || 'guest', device_id: deviceId || '' },
    }),
  });

  if (!rzpRes.ok) {
    const errText = await rzpRes.text();
    return errorResponse(`Razorpay order failed: ${errText}`, 500);
  }

  const order = await rzpRes.json();

  const logRes = await sbAdmin(env, 'job_orders', {
    method: 'POST',
    headers: { 'Prefer': 'return=minimal' },
    body: JSON.stringify({ id: order.id, user_id: user?.id || null, device_id: deviceId || null, amount: amountPaise, plan, status: 'created' }),
  });
  if (!logRes.ok) {
    console.error('job_orders insert failed:', logRes.status, await logRes.text().catch(() => ''));
    return errorResponse('Could not start the order. Please try again.', 500);
  }

  return jsonResponse({
    order_id: order.id,
    amount: amountPaise,
    key_id: rzpKey,
  });
}

// ============================================================================
// 3. RAZORPAY HMAC SIGNATURE VERIFICATION
// ============================================================================
async function handleVerifyPayment(req, env) {
  const user = await getAuthUser(req, env);
  if (!env.SUPABASE_SERVICE_ROLE_KEY) return errorResponse('Database key not configured on worker', 500);
  const body = await req.json().catch(() => ({}));
  const deviceId = cleanDeviceId(body.device_id);
  const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = body;

  if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature) {
    return errorResponse('Missing required payment parameters', 400);
  }

  const rzpSecret = env.RAZORPAY_KEY_SECRET;
  if (!rzpSecret) {
    return errorResponse('Razorpay secret not configured on worker', 500);
  }

  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(rzpSecret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const msg = enc.encode(`${razorpay_order_id}|${razorpay_payment_id}`);
  const sigBuffer = await crypto.subtle.sign('HMAC', key, msg);
  const expectedSig = Array.from(new Uint8Array(sigBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  if (expectedSig !== razorpay_signature) {
    return errorResponse('Invalid payment signature', 400);
  }

  // The order must belong to this account (or, for a guest order, this browser); the plan comes from the stored order.
  const orderRes = await sbAdmin(env, `job_orders?id=eq.${encodeURIComponent(razorpay_order_id)}&select=user_id,device_id,plan,status`);
  const orderRows = orderRes.ok ? await orderRes.json() : [];
  const orderRow = orderRows[0];
  if (!orderRow) return errorResponse('Order not found', 404);
  const owns = orderRow.user_id ? orderRow.user_id === user?.id : Boolean(deviceId) && orderRow.device_id === deviceId;
  if (!owns) return errorResponse('This order belongs to a different account', 403);

  const granted = await grantPaidOrder(env, razorpay_order_id, razorpay_payment_id);
  if (!granted.ok) {
    return errorResponse('Payment received but access was not saved. Contact support with your payment id.', 500);
  }
  return jsonResponse({ success: true, unlimited_until: granted.unlimited_until });
}

// Marks the order paid and extends Pro in one database transaction (safe to repeat).
async function grantPaidOrder(env, orderId, paymentId) {
  const res = await sbAdmin(env, 'rpc/job_order_grant', {
    method: 'POST',
    body: JSON.stringify({ p_order: orderId, p_payment: paymentId || null }),
  });
  if (!res.ok) {
    console.error('job_order_grant failed:', res.status, await res.text().catch(() => ''));
    return { ok: false };
  }
  return res.json();
}

async function hmacHex(secret, message) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, typeof message === 'string' ? enc.encode(message) : message);
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

// Razorpay calls this after a payment, even if the buyer closed the tab before the page confirmed it.
// Dashboard: Settings -> Webhooks -> URL https://camouroles.pages.dev/api/razorpay/webhook,
// events order.paid + payment.captured, secret = RAZORPAY_WEBHOOK_SECRET.
async function handleRazorpayWebhook(req, env) {
  const secret = env.RAZORPAY_WEBHOOK_SECRET;
  if (!secret || !env.SUPABASE_SERVICE_ROLE_KEY) return errorResponse('Webhook not configured', 500);
  const raw = await req.arrayBuffer();
  const given = req.headers.get('x-razorpay-signature') || '';
  const expected = await hmacHex(secret, new Uint8Array(raw));
  if (given.length !== expected.length || given !== expected) return errorResponse('Invalid signature', 400);

  let event = {};
  try { event = JSON.parse(new TextDecoder().decode(raw)); } catch (e) { return errorResponse('Bad JSON', 400); }
  if (!['order.paid', 'payment.captured'].includes(event.event)) return jsonResponse({ ignored: event.event || 'unknown' });

  const payment = event.payload?.payment?.entity || {};
  const orderId = event.payload?.order?.entity?.id || payment.order_id;
  if (!orderId) return jsonResponse({ ignored: 'no order id' });
  if (payment.status && !['captured', 'authorized'].includes(payment.status)) return jsonResponse({ ignored: payment.status });

  const granted = await grantPaidOrder(env, orderId, payment.id);
  if (!granted.ok) {
    // Orders from other apps on the same Razorpay account are not ours: acknowledge so Razorpay stops retrying.
    if (granted.error === 'order_not_found') return jsonResponse({ ignored: 'not a CamouRoles order' });
    return errorResponse('Grant failed', 500); // 5xx makes Razorpay retry later
  }
  return jsonResponse({ ok: true, already: granted.already });
}

// ============================================================================
// 4. GOOGLE AUTH & USER PROFILE
// ============================================================================
async function handleGoogleAuth(req, env) {
  // Sign-in happens through Supabase Auth in the browser; this old endpoint no longer issues identities.
  return errorResponse('Use Supabase sign-in', 410);
}

// ============================================================================
// 5. PROFILE & ENTITLEMENTS STATUS
// ============================================================================
async function handleGetProfile(req, env) {
  const authUser = await getAuthUser(req, env);
  const userId = authUser?.id || null;
  const deviceId = cleanDeviceId(new URL(req.url).searchParams.get('device_id'));
  const until = await proUntil(env, userId, deviceId);
  const isUnlimited = Boolean(until);

  return jsonResponse({
    authenticated: Boolean(userId),
    user_id: userId,
    email: authUser?.email || null,
    has_cv: false,
    profile: null,
    headline: null,
    experience_years: 0,
    skills: [],
    summary: '',
    free_unlocks_left: isUnlimited ? 9999 : 3,
    is_unlimited: isUnlimited,
    unlimited_until: until,
    stats: {
      total_matches: 0,
      unlocked_count: 0,
    },
  }, 200, { 'Cache-Control': 'no-store' });
}

// Active Pro end time for an account or a guest browser, or null. A signed-in browser that bought
// Pro as a guest hands its remaining time to the account here.
async function proUntil(env, userId, deviceId) {
  if (!env.SUPABASE_SERVICE_ROLE_KEY) return null;
  let until = null;
  try {
    if (userId && deviceId) {
      const res = await sbAdmin(env, 'rpc/claim_guest_pro', { method: 'POST', body: JSON.stringify({ p_user: userId, p_device: deviceId }) });
      if (res.ok) until = await res.json();
    } else if (userId) {
      const res = await sbAdmin(env, `user_entitlements?user_id=eq.${encodeURIComponent(userId)}&select=unlimited_until`);
      if (res.ok) until = (await res.json())[0]?.unlimited_until || null;
    } else if (deviceId) {
      const res = await sbAdmin(env, `guest_entitlements?device_id=eq.${encodeURIComponent(deviceId)}&select=unlimited_until`);
      if (res.ok) until = (await res.json())[0]?.unlimited_until || null;
    }
  } catch (e) {
    console.error('pro lookup failed:', e.message);
  }
  return until && new Date(until).getTime() > Date.now() ? until : null;
}

// ============================================================================
// 6. LLM CALLER: Groq free tier first, OpenRouter free model when Groq's daily cap is used up
// ============================================================================
async function callFrontierLlm(messages, env, jsonMode = false, maxTokens = 600) {
  const orKey = env.OPENROUTER_API_KEY;
  const groqKey = env.GROQ_API_KEY;

  // 1. Groq: GPT-OSS 120B, then Qwen 27B (each has its own 1,000 calls/day)
  if (groqKey) {
    for (const gModel of ['openai/gpt-oss-120b', 'qwen/qwen3.8-27b']) {
      try {
        const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${groqKey}`,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
          },
          body: JSON.stringify({
            model: gModel,
            messages,
            temperature: jsonMode ? 0.1 : 0.6,
            max_tokens: maxTokens + 400, // room for the model's short reasoning before the answer
            reasoning_effort: 'low'
          })
        });
        if (res.ok) {
          const data = await res.json();
          const content = data.choices?.[0]?.message?.content || '';
          if (content) {
            return content.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim();
          }
        }
      } catch (e) {
        console.warn(`Groq call error for ${gModel}:`, e);
      }
    }
  }

  // 2. Overflow: OpenRouter free models (50 calls/day on a key with no credits)
  if (orKey) {
    for (const orModel of ['minimax/minimax-m3.1-flash:free', 'openrouter/free']) {
      try {
        const payload = {
          model: orModel,
          messages,
          temperature: jsonMode ? 0.1 : 0.65,
          max_tokens: maxTokens + 400
        };
        if (jsonMode) {
          payload.response_format = { type: 'json_object' };
        }
        const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${orKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const data = await res.json();
          const content = data.choices?.[0]?.message?.content || '';
          if (content) {
            return content.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim();
          }
        } else {
          console.warn('OpenRouter non-OK status:', orModel, res.status);
        }
      } catch (e) {
        console.warn(`OpenRouter call error for ${orModel}:`, e);
      }
    }
  }

  return null;
}

// ============================================================================
// 7. AI RECRUITER: turns the conversation into search filters
// The model only understands the request and writes a short lead-in. The browser runs the
// search on the full catalogue with the same filters as the filter sheet, so every job and
// number the candidate sees is real.
// ============================================================================
const RECRUITER_FIELDS = {
  ai_ml: 'AI & ML', backend: 'Backend', frontend: 'Frontend', devops: 'DevOps & Cloud', robotics: 'Robotics',
  spacetech: 'Space & Aerospace', electrical_hardware: 'Hardware & Electrical', defense_cyber: 'Defense & Cyber',
  climate_cleanenergy: 'Climate & Energy', biotech_health: 'Biotech & Health', game_dev: 'Games',
  design: 'Product Design', business: 'Business & Ops', hr: 'HR & People', civil_construction: 'Civil & Construction',
  safety: 'Safety',
};
const RECRUITER_LOCATIONS = {
  worldwide_remote: 'Remote', india: 'India', usa: 'United States', uae: 'UAE & Gulf', london: 'United Kingdom',
  germany: 'Germany', canada: 'Canada', singapore: 'Singapore', netherlands: 'Netherlands',
  switzerland: 'Switzerland', france: 'France', japan: 'Japan', australia: 'Australia',
};
const RECRUITER_EXPERIENCE = ['all', '0-1', '1-3', '3-6', '6+'];

// Keyword fallback when no model is reachable: worker pattern keys -> filter-sheet keys
const FALLBACK_FIELD = {
  ai: 'ai_ml', backend: 'backend', frontend: 'frontend', robotics: 'robotics', hardware: 'electrical_hardware',
  propulsion: 'spacetech', biotech: 'biotech_health', energy: 'climate_cleanenergy', security: 'defense_cyber', safety: 'safety',
};
const FALLBACK_LOCATION = {
  sf_bay: 'usa', seattle: 'usa', nyc: 'usa', austin: 'usa', tokyo: 'japan',
};

function cleanRecruiterPlan(raw, current) {
  const p = raw && typeof raw === 'object' ? raw : {};
  const list = (v, allowed) => [...new Set((Array.isArray(v) ? v : []).map((x) => String(x).toLowerCase().trim()))].filter((k) => k in allowed);
  const text = (v, max) => String(v || '').replace(/\s+/g, ' ').trim().slice(0, max);
  const reset = p.reset === true;
  const plan = {
    action: ['search', 'ask', 'chat'].includes(p.action) ? p.action : 'search',
    say: text(p.say, 320),
    question: text(p.question, 180),
    query: text(p.query, 60).toLowerCase(),
    fields: list(p.fields, RECRUITER_FIELDS),
    locations: list(p.locations, RECRUITER_LOCATIONS),
    experience: RECRUITER_EXPERIENCE.includes(p.experience) ? p.experience : 'all',
    company: text(p.company, 40),
    reset,
  };
  // A pure "chat" turn keeps whatever the candidate already has on screen.
  if (plan.action === 'chat' && !reset) {
    Object.assign(plan, { query: current.query, fields: current.fields, locations: current.locations, experience: current.experience, company: current.company });
  }
  return plan;
}

function currentFiltersFrom(body) {
  const f = body.current_filters || {};
  const split = (v, allowed) => String(v || 'all').split(',').map((s) => s.trim()).filter((k) => k in allowed);
  return {
    query: String(f.q || '').slice(0, 60),
    fields: split(f.discipline, RECRUITER_FIELDS),
    locations: split(f.location, RECRUITER_LOCATIONS),
    experience: RECRUITER_EXPERIENCE.includes(f.expPreset) ? f.expPreset : 'all',
    company: f.company && f.company !== 'all' ? String(f.company).slice(0, 40) : '',
  };
}

function fallbackRecruiterPlan(message, current) {
  const t = message.toLowerCase();
  const disc = detectRequestedDiscipline(t);
  const loc = detectRequestedLocation(t);
  const locKey = loc ? (FALLBACK_LOCATION[loc] || loc) : null;
  return {
    action: 'search',
    say: 'Here is what I found for that.',
    question: '',
    query: disc ? '' : message.replace(/\b(show|find|me|jobs?|roles?|openings?|in|for|a|an|the|please|any|some)\b/gi, ' ').replace(/\s+/g, ' ').trim().slice(0, 40).toLowerCase(),
    fields: disc && FALLBACK_FIELD[disc] ? [FALLBACK_FIELD[disc]] : current.fields,
    locations: locKey && locKey in RECRUITER_LOCATIONS ? [locKey] : current.locations,
    experience: current.experience,
    company: current.company,
    reset: false,
  };
}

async function handleRecruiterChat(req, env) {
  const body = await req.json().catch(() => ({}));
  const message = String(body.message || '').trim().slice(0, 800);
  if (!message) return errorResponse('Empty message', 400);

  const current = currentFiltersFrom(body);
  const history = [];
  for (const h of (Array.isArray(body.conversation) ? body.conversation : []).slice(-8)) {
    const content = String(h.content || h.text || '').trim().slice(0, 600);
    if (!content) continue;
    history.push({ role: h.role === 'user' || h.role === 'candidate' ? 'user' : 'assistant', content });
  }
  if (history.length && history[history.length - 1].role === 'user' && history[history.length - 1].content === message) history.pop();

  const fieldList = Object.entries(RECRUITER_FIELDS).map(([k, v]) => `${k} (${v})`).join(', ');
  const locationList = Object.entries(RECRUITER_LOCATIONS).map(([k, v]) => `${k} (${v})`).join(', ');
  const system = `You are the recruiter assistant inside CamouRoles, a job board of verified openings (mostly tech roles worldwide, many in India). You talk with a job seeker and turn what they want into search filters. The website runs the search on the real catalogue and shows the results under your message, so you never name specific openings and never state counts.

Reply with JSON only:
{"action":"search|ask|chat","say":"","question":"","query":"","fields":[],"locations":[],"experience":"all","company":"","reset":false}

action:
- "search": you know enough to search (a role, skill, field or company). Fill the filters.
- "ask": nothing to search on yet (for example "hi" or "find me a job"). Ask what kind of role they want in "question".
- "chat": a general question (CV tips, interviews, salaries, how the site works). Answer it in "say"; leave filters as they are.
say: one or two short, warm, natural sentences in the user's language. No lists, no emojis, no made-up facts about specific jobs, companies or numbers. Don't repeat greetings.
question: one short follow-up that would sharpen the search (location, experience or remote), only when that detail is still unknown. Never ask again for something already known. Empty otherwise.
query: role or skill words to match in job titles and skills, like "data engineer", "react", "embedded". Empty when a broad field fits better.
fields: zero or more of: ${fieldList}.
locations: zero or more of: ${locationList}. Map cities and regions to these (Bangalore -> india, Dubai or Gulf -> uae, San Francisco or "US" -> usa, London or "UK" -> london). "Remote" or "work from home" -> worldwide_remote.
experience: the candidate's own experience: "all" (unknown), "0-1", "1-3", "3-6" or "6+".
company: a company the user named, else "".
Keep the current filters unless the user changes them: "also" or "and" adds to a list, "only" or "instead" replaces it, "start over" or "clear" sets reset true with empty filters. An empty list means "any"; so when locations is empty, "remote is fine too" or "X also works" leaves it empty instead of narrowing to X.
When a candidate CV is given, you know this person:
- Set experience from the CV's years unless the user says otherwise.
- "Jobs for me", "what fits my profile", "match my CV" and similar mean: search from the CV (its headline or main skill as query, its field in fields, its years as experience). Use action "search", not "ask".
- Talk to them as someone who has read their CV: refer to their background briefly and naturally in "say" when it helps (for example their years or main skill), and give advice that fits their level. Never invent CV details that are not given.
- Do not ask for things the CV already tells you.`;

  const cv = String(body.cv_summary || '').trim().slice(0, 900);
  const context = `Current filters: ${JSON.stringify(current)}\n${cv ? `Candidate CV: ${cv}` : 'No CV uploaded yet.'}`;

  const raw = await callFrontierLlm(
    [{ role: 'system', content: system }, { role: 'system', content: context }, ...history, { role: 'user', content: message }],
    env, true, 350
  );

  let plan = null;
  if (raw) {
    try {
      const m = raw.match(/\{[\s\S]*\}/);
      if (m) plan = cleanRecruiterPlan(JSON.parse(m[0]), current);
    } catch (e) {
      console.warn('Recruiter plan parse error:', e);
    }
  }
  const usedFallback = !plan;
  if (!plan) plan = fallbackRecruiterPlan(message, current);
  if (!plan.say) plan.say = plan.action === 'ask' ? 'Happy to help you find the right role.' : 'Here is what I found.';
  if (plan.action === 'ask' && !plan.question) plan.question = 'What kind of role are you looking for?';

  return jsonResponse({
    reply: [plan.say, plan.question].filter(Boolean).join(' '),
    plan,
    source: usedFallback ? 'keywords' : 'llm',
  });
}

// ============================================================================
// 8. CV MATCHING
// The model reads the CV once into a profile: the job titles this person should apply for,
// their seniority level and their concrete skills. Jobs are then ranked by how well the title
// fits, then skills, and anything two or more levels away from the candidate is left out.
// ============================================================================
const CV_LEVELS = ['student', 'junior', 'mid', 'senior', 'lead'];
const LEVEL_WORDS = /\b(senior|sr|junior|jr|lead|staff|principal|head|chief|director|manager|vp|intern|internship|trainee|associate|entry|level|i|ii|iii|iv|v|1|2|3|4)\b/g;
const WEAK_TITLE_WORDS = new Set(['engineer', 'engineering', 'developer', 'specialist', 'analyst', 'consultant', 'associate', 'manager', 'technician', 'officer', 'executive', 'and', 'of', 'the', 'for', 'with', 'in', 'to', 'a', 'an', 'team', 'remote', 'hybrid']);

function titleWords(s) {
  return String(s || '').toLowerCase().replace(/[^a-z0-9+#.\s/-]/g, ' ').replace(LEVEL_WORDS, ' ')
    .split(/[\s/,()-]+/).map((w) => w.replace(/\.$/, '')).filter((w) => w.length > 1 || w === 'c');
}

function wordIn(text, word) {
  const esc = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(^|[^a-z0-9+#])${esc}(s|es|ing|ed|er|ers)?(?![a-z0-9+#])`).test(text);
}

// 0 intern/new grad ... 4 staff/principal/manager and above
function jobLevel(job) {
  const t = ` ${String(job.title || '').toLowerCase()} `;
  if (/\b(intern|internship|trainee|apprentice|new grad|graduate|fellowship|co-op|student)\b/.test(t)) return 0;
  if (/\b(staff|principal|distinguished|director|head of|vp|vice president|chief|architect)\b/.test(t)) return 4;
  if (/\b(manager|lead)\b/.test(t) && !/\bproduct manager\b|\bproject manager\b|\baccount manager\b/.test(t)) return 4;
  if (/\b(senior|sr\.?|iii|iv)\b/.test(t)) return 3;
  if (/\b(junior|jr\.?|entry|associate|early career)\b|\bi\b|\b1\b/.test(t)) return 1;
  if (/\bii\b|\b2\b/.test(t)) return 2;
  // No level in the title: most such postings take a range of people. (Stored experience numbers are
  // unreliable for older jobs, so they are not used here.)
  return null;
}

function candidateLevel(profile) {
  const byName = CV_LEVELS.indexOf(String(profile.level || '').toLowerCase());
  if (byName >= 0) return byName;
  const y = Number(profile.experienceYears) || 0;
  return y < 0.5 ? 0 : y < 2.5 ? 1 : y < 5.5 ? 2 : y < 9 ? 3 : 4;
}

function scoreJobsForProfile(profile, jobs) {
  const candLevel = candidateLevel(profile);
  const targets = [...new Set([...(profile.targetTitles || []), profile.headline].filter(Boolean))]
    .map((t) => ({ text: t, words: titleWords(t) }))
    .filter((t) => t.words.length);
  const skills = [...new Set((profile.skills || []).map((s) => String(s).toLowerCase().trim()).filter((s) => s.length > 0 && s.length < 30))];
  const homeCountries = new Set((profile.locations || []).map((l) => String(l).toLowerCase()));
  const COUNTRY_RX = {
    india: /\b(india|bengaluru|bangalore|hyderabad|pune|mumbai|delhi|gurgaon|gurugram|noida|chennai|kolkata|ahmedabad)\b|,\s*ind\b/,
    usa: /\b(united states|usa|california|new york|texas|washington|seattle|san francisco|boston|austin)\b|,\s*(ca|ny|tx|wa|ma)\b/,
    uae: /\b(uae|dubai|abu dhabi|emirates)\b/,
    london: /\b(london|united kingdom|uk)\b/,
    germany: /\b(germany|berlin|munich)\b/,
    worldwide_remote: /\bremote\b/,
  };

  const scored = [];
  for (const job of jobs) {
    const title = String(job.title || '').toLowerCase();
    if (!title) continue;
    const jl = jobLevel(job);
    // Plain titles fit juniors to seniors; for a student they are a stretch, for a lead a step down.
    const diff = jl === null ? (candLevel === 0 ? 1 : candLevel === 4 ? -1 : 0) : jl - candLevel;
    if (diff >= 2 || diff <= -2) continue; // far too senior or far too junior

    // Title fit: share of the target title's meaningful words found in the job title.
    let titleFit = 0;
    let bestTarget = '';
    for (const t of targets) {
      let have = 0;
      let total = 0;
      for (const w of t.words) {
        const weight = WEAK_TITLE_WORDS.has(w) ? 0.35 : 1;
        total += weight;
        if (wordIn(title, w)) have += weight;
      }
      const fit = total ? have / total : 0;
      if (fit > titleFit) { titleFit = fit; bestTarget = t.text; }
    }

    const jobText = `${title} | ${(job.skills || []).join(' | ').toLowerCase()}`;
    const matchedSkills = skills.filter((s) => wordIn(jobText, s));

    // Relevant only if the role itself fits, or the title plus several skills line up.
    if (!(titleFit >= 0.6 || (titleFit >= 0.3 && matchedSkills.length >= 2) || matchedSkills.length >= 3)) continue;

    const loc = String(job.location || '').toLowerCase();
    const nearHome = [...homeCountries].some((c) => COUNTRY_RX[c] && COUNTRY_RX[c].test(loc));

    let pct = 28 + titleFit * 45 + Math.min(matchedSkills.length, 4) * 4 + (diff === 0 ? 8 : 0) + (nearHome ? 8 : 0);
    if (diff === 1) pct -= 8;   // one step above their level: a stretch
    if (diff === -1) pct -= 5;  // one step below: they are over-qualified
    pct = Math.max(35, Math.min(97, Math.round(pct)));

    const reasons = [];
    if (titleFit >= 0.6 && bestTarget) reasons.push(`Fits "${bestTarget}"`);
    if (matchedSkills.length) reasons.push(`Skills: ${matchedSkills.slice(0, 3).join(', ')}`);
    reasons.push(diff === 0 ? 'Right level' : diff === 1 ? 'A step up' : 'Below your level');
    scored.push({ id: job.id, score: pct, explanation: reasons.join(' · ') });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored;
}

const CV_FIELD_KEYS = 'ai_ml, backend, frontend, devops, robotics, spacetech, electrical_hardware, defense_cyber, climate_cleanenergy, biotech_health, game_dev, design, business, hr, civil_construction, safety';
const CV_LOCATION_KEYS = 'india, usa, uae, london, germany, canada, singapore, netherlands, switzerland, france, japan, australia, worldwide_remote';

async function parseCvWithLlm(cvText, env) {
  const prompt = `You read a candidate's CV and describe who they are as a job seeker. Reply with JSON only:
{"headline":"","experienceYears":0,"level":"","targetTitles":[],"skills":[],"fields":[],"locations":[],"summary":""}
- headline: their current or most recent job title as written (or "Student" / "Fresh graduate").
- experienceYears: total full-time professional experience in years (internships count as a quarter, studies as zero). Use the dates in the CV.
- level: "student" (no full-time work), "junior" (under ~2.5 years), "mid" (2.5-5.5), "senior" (5.5-9) or "lead" (9+ or managing teams).
- targetTitles: 5 to 8 concrete job titles this person should apply for next, at their level, most likely first. Use real market titles (for example "Embedded Firmware Engineer", "Embedded Software Engineer"). Do not add "Senior" unless level is senior or lead; for students and juniors prefer "Intern", "Graduate", "Junior" or plain titles.
- skills: up to 12 concrete skills, tools or technologies actually in the CV, short names.
- fields: 1 to 3 of: ${CV_FIELD_KEYS}.
- locations: where they live or want to work, from: ${CV_LOCATION_KEYS}. Empty if unknown.
- summary: two plain sentences about their background.
Never invent facts that are not in the CV.`;
  const out = await callFrontierLlm([
    { role: 'system', content: prompt },
    { role: 'user', content: `CV text:\n${cvText.slice(0, 7000)}` },
  ], env, true, 500);
  if (!out) return null;
  try {
    const m = out.match(/\{[\s\S]*\}/);
    return m ? JSON.parse(m[0]) : null;
  } catch (e) {
    console.warn('CV JSON parse error:', e);
    return null;
  }
}

function cleanCvProfile(p, fileName) {
  const years = Math.max(0, Math.min(45, Number(p.experienceYears) || 0));
  const level = CV_LEVELS.includes(String(p.level).toLowerCase()) ? String(p.level).toLowerCase() : CV_LEVELS[candidateLevel({ experienceYears: years })];
  const list = (v, n) => (Array.isArray(v) ? v : []).map((x) => String(x).trim()).filter(Boolean).slice(0, n);
  return {
    fileName: fileName || 'CV.pdf',
    headline: String(p.headline || 'Candidate').slice(0, 80),
    experienceYears: Math.round(years * 10) / 10,
    experienceText: years < 0.5 ? 'Student / fresher' : `${Math.round(years * 10) / 10} yrs experience`,
    level,
    targetTitles: list(p.targetTitles, 8),
    skills: list(p.skills, 12),
    fields: list(p.fields, 3),
    discipline: list(p.fields, 1)[0] || '',
    locations: list(p.locations, 4).map((l) => l.toLowerCase()),
    summary: String(p.summary || '').slice(0, 400),
    matchVersion: 2,
  };
}

async function handleCvMatch(req, env) {
  let cvText = '';
  let fileName = 'CV.pdf';
  let givenProfile = null;

  const contentType = req.headers.get('content-type') || '';
  if (contentType.includes('multipart/form-data')) {
    try {
      const formData = await req.formData();
      const file = formData.get('file');
      cvText = String(formData.get('extracted_text') || '');
      if (file && typeof file === 'object') fileName = file.name || fileName;
    } catch (e) {
      console.warn('Multipart parse warning:', e);
    }
  } else {
    const body = await req.json().catch(() => ({}));
    cvText = String(body.cv_text || body.text || '');
    fileName = body.file_name || fileName;
    if (body.profile && typeof body.profile === 'object') givenProfile = body.profile; // re-rank a saved profile
  }

  let profile = null;
  if (givenProfile && Array.isArray(givenProfile.targetTitles) && givenProfile.targetTitles.length) {
    profile = cleanCvProfile(givenProfile, givenProfile.fileName);
  } else {
    const text = cvText.replace(/\s+/g, ' ').trim();
    // Raw PDF bytes are not CV text; better to say so than to guess a profile.
    if (text.length < 80 || /^%PDF|endobj|\/FlateDecode/.test(text.slice(0, 400))) {
      return jsonResponse({
        success: false,
        error: 'Could not read text from this PDF. Please upload a text-based PDF (not a scan or photo).',
        profile: null, matches: {}, top_jobs: [], total_evaluated: 0, total_matched: 0,
      }, 422);
    }
    const parsed = await parseCvWithLlm(text, env);
    if (!parsed) {
      return jsonResponse({
        success: false,
        error: 'Our CV reader is busy right now. Please try again in a minute.',
        profile: null, matches: {}, top_jobs: [], total_evaluated: 0, total_matched: 0,
      }, 503);
    }
    profile = cleanCvProfile(parsed, fileName);
  }

  let allJobs = cachedJobs;
  if (!allJobs || allJobs.length === 0) {
    await handleGetJobs(null, env);
    allJobs = cachedJobs || [];
  }

  const ranked = scoreJobsForProfile(profile, allJobs).slice(0, 150);
  const matches = {};
  for (const m of ranked) matches[m.id] = { score: m.score, explanation: m.explanation };

  return jsonResponse({
    success: true,
    profile,
    matches,
    top_jobs: ranked.map((m) => m.id),
    total_evaluated: allJobs.length,
    total_matched: ranked.length,
    message: ranked.length ? undefined : 'No open roles fit your profile closely right now. New jobs are added every few hours.',
  });
}

// ============================================================================
// 9. FREE APPLY LIMITS
// With APPLY_GATE=on the job list goes out without apply links; a link is handed out
// only through /api/apply after the count check, so the limit can't be skipped.
// ============================================================================
const ANON_FREE_APPLIES = 2;
const FREE_APPLIES = 5;
const UUID_RX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function publicJobs(jobs, env) {
  if (env?.APPLY_GATE !== 'on') return jobs;
  return jobs.map((j) => {
    let host = '';
    try { host = new URL(j.applyUrl).hostname.replace(/^www\./, ''); } catch (e) {}
    return { ...j, applyUrl: null, applyHost: host, gated: true };
  });
}

async function hasUnlimited(userId, env, deviceId) {
  return Boolean(await proUntil(env, userId, cleanDeviceId(deviceId)));
}

async function claimApply(env, userId, deviceId, jobId, unlimited) {
  const res = await sbAdmin(env, 'rpc/job_apply_claim', {
    method: 'POST',
    body: JSON.stringify({
      p_user: userId, p_device: deviceId || null, p_job: jobId,
      p_anon_limit: ANON_FREE_APPLIES, p_user_limit: FREE_APPLIES, p_unlimited: unlimited,
    }),
  });
  if (!res.ok) throw new Error(`apply check failed (${res.status})`);
  return res.json();
}

function applySummary(r, user, pro) {
  const limit = user ? FREE_APPLIES : ANON_FREE_APPLIES;
  return {
    signed_in: Boolean(user),
    pro,
    used: r.used,
    limit,
    left: pro ? null : Math.max(0, limit - r.used),
  };
}

async function handleApply(req, env) {
  if (!env.SUPABASE_SERVICE_ROLE_KEY) return errorResponse('Database key not configured on worker', 500);
  const body = await req.json().catch(() => ({}));
  const jobId = String(body.job_id || '');
  const deviceId = String(body.device_id || '').slice(0, 64);
  if (!UUID_RX.test(jobId)) return errorResponse('Unknown job', 400);

  if (!cachedJobs || !cachedJobs.length) await handleGetJobs(null, env);
  const job = (cachedJobs || []).find((j) => j.id === jobId);
  if (!job || !job.applyUrl) return errorResponse('This job is no longer listed', 404);

  const user = await getAuthUser(req, env);
  const pro = await hasUnlimited(user?.id || null, env, deviceId);
  const r = await claimApply(env, user?.id || null, deviceId, jobId, pro);
  const summary = applySummary(r, user, pro);
  if (!r.allowed) {
    return jsonResponse({ allowed: false, need: r.need, ...summary, left: 0 }, r.need === 'login' ? 401 : 402);
  }
  return jsonResponse({ allowed: true, url: job.applyUrl, ...summary });
}

async function handleApplyStatus(req, env, url) {
  if (!env.SUPABASE_SERVICE_ROLE_KEY) return errorResponse('Database key not configured on worker', 500);
  const deviceId = String(url.searchParams.get('device_id') || '').slice(0, 64);
  const user = await getAuthUser(req, env);
  const pro = await hasUnlimited(user?.id || null, env, deviceId);
  const r = await claimApply(env, user?.id || null, deviceId, null, pro);
  return jsonResponse({ gated: env.APPLY_GATE === 'on', ...applySummary(r, user, pro) }, 200, { 'Cache-Control': 'no-store' });
}

async function handleJevFilter(req, env) {
  // Alias for backward-compatibility with any existing search calls
  const body = await req.json().catch(() => ({}));
  const stateText = `${body.message || ''} ${body.cv_summary || ''}`.trim();
  return jsonResponse({
    success: true,
    decision: {
      discipline: 'all',
      experience_tier: '3-6',
      is_remote_mandatory: 0.3,
      target_hub: 'all',
      skills: []
    }
  });
}

