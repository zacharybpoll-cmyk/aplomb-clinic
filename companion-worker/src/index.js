// APLOMB. companion cron Worker.
//
// Pages Functions (aplomb-clinic) does not support `triggers.crons` in
// wrangler.toml. This Worker is the scheduler. On each cron event it POSTs
// to the corresponding /cron/* endpoint on the Pages project with the
// shared secret. The Pages endpoint does the actual database + email work.

const SCHEDULE = {
  '0 9 * * *':  '/cron/renewal-reminder',
  '15 9 * * *': '/cron/review-requests',
  '30 9 * * *': '/cron/welcome-series',
};

export default {
  async scheduled(event, env, ctx) {
    const path = SCHEDULE[event.cron];
    if (!path) {
      console.log(`[cron] unknown trigger ${event.cron}`);
      return;
    }
    const base = env.PAGES_BASE_URL || 'https://getaplomb.com';
    const url = `${base}${path}`;
    const t0 = Date.now();
    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: {
          'X-Cron-Secret': env.CRON_SHARED_SECRET || '',
          'Content-Type': 'application/json',
        },
      });
      const body = await r.text();
      const ms = Date.now() - t0;
      console.log(`[cron ${event.cron} → ${path}] ${r.status} ${ms}ms ${body.slice(0, 200)}`);
    } catch (e) {
      console.error(`[cron ${event.cron} → ${path}] failed:`, e && e.message);
    }
  },

  // Optional manual-trigger HTTP route for testing. Requires the same secret.
  // Visit /run/<endpoint> e.g. /run/welcome-series with header X-Cron-Secret.
  async fetch(request, env) {
    const url = new URL(request.url);
    const m = url.pathname.match(/^\/run\/(renewal-reminder|review-requests|welcome-series)$/);
    if (!m) return new Response('aplomb-clinic-cron — see wrangler.toml for the schedule', { status: 200 });
    const provided = request.headers.get('x-cron-secret') || '';
    if (!env.CRON_SHARED_SECRET || provided !== env.CRON_SHARED_SECRET) {
      return new Response('Forbidden', { status: 401 });
    }
    const base = env.PAGES_BASE_URL || 'https://getaplomb.com';
    const r = await fetch(`${base}/cron/${m[1]}`, {
      method: 'POST',
      headers: {
        'X-Cron-Secret': env.CRON_SHARED_SECRET,
        'Content-Type': 'application/json',
      },
    });
    return new Response(await r.text(), { status: r.status });
  },
};
