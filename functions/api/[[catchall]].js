/**
 * Camouroles Pages Functions API Gateway
 * Forwards all /api/* requests to the production edge worker
 * Ensuring a 100% clean, unified domain at https://camouroles.pages.dev
 */

export async function onRequest(context) {
  const url = new URL(context.request.url);

  // Handle CORS preflight
  if (context.request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-device',
        'Access-Control-Max-Age': '86400',
      },
    });
  }

  const targetUrl = new URL(`https://camouroles.primemax.workers.dev${url.pathname}${url.search}`);
  const reqHeaders = new Headers(context.request.headers);
  reqHeaders.set('x-forwarded-host', url.host);
  // The worker sees this proxy's address, not the visitor's; pass the real one for rate limiting,
  // with a shared key so callers can't spoof it by hitting the worker directly.
  reqHeaders.set('x-client-ip', context.request.headers.get('cf-connecting-ip') || '');
  if (context.env.PROXY_KEY) reqHeaders.set('x-proxy-key', context.env.PROXY_KEY);

  // Only the public job list may be cached; everything else is per user (profile, apply status).
  const cacheable = context.request.method === 'GET' && url.pathname === '/api/jobs';
  const init = {
    method: context.request.method,
    headers: reqHeaders,
    redirect: 'follow',
    cf: cacheable ? { cacheEverything: true, cacheTtl: 7200 } : undefined,
  };

  if (!['GET', 'HEAD'].includes(context.request.method)) {
    init.body = context.request.body;
    init.duplex = 'half';
  }

  const response = await fetch(targetUrl.toString(), init);

  const resHeaders = new Headers(response.headers);
  resHeaders.set('Access-Control-Allow-Origin', '*');
  resHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  resHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-device');
  if (url.pathname === '/api/jobs') {
    resHeaders.set('Cache-Control', 'public, max-age=1800, s-maxage=7200, stale-while-revalidate=86400');
    resHeaders.set('CDN-Cache-Control', 'max-age=7200');
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: resHeaders,
  });
}
