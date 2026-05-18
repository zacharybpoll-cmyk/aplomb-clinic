#!/usr/bin/env node
// APLOMB. — thin Facebook Page control via the Meta Graph API.
//
//   Why this exists: browser automation of facebook.com is unreliable (Meta
//   defends its DOM). The Graph API is the supported, stable path. This script
//   is the *only* thing that touches the Page token — no third party, no MCP.
//
//   Scope: organic Page content only (publish, schedule, read, moderate,
//   insights). It deliberately does NOT touch the live v18.0 CAPI code in
//   functions/api/webhooks/stripe.js, and does NOT do Ads/Marketing API.
//
//   Conventions mirrored from the smoke harness:
//     - secrets come from the environment, never hard-coded, never echoed
//     - read-only by default; every write needs an explicit --confirm
//     - report the real Graph API error (message/code/fbtrace_id), verbatim
//
//   Usage:  npm run fb -- <command> [flags]
//           node scripts/fb-page.mjs help
//
//   Env (process.env or a gitignored scripts/.fb.env — see .fb.env.example):
//     FB_PAGE_ID            the getaplomb.com Page id           (required)
//     FB_PAGE_ACCESS_TOKEN  System User or long-lived Page token (required)
//     FB_API_VERSION        Graph API version (default v23.0)
//     FB_APP_ID/FB_APP_SECRET/FB_USER_TOKEN  only for `bootstrap-token`
//     FB_CONFIRM=1          alternative to passing --confirm on writes

import { readFile, appendFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ENV_FILE = resolve(HERE, '.fb.env');

// ── env loading ──────────────────────────────────────────────────────────────
// Native, dependency-free. process.env wins; scripts/.fb.env fills the gaps.
async function loadEnvFile() {
  let raw;
  try {
    raw = await readFile(ENV_FILE, 'utf8');
  } catch {
    return; // absent is fine — env may be exported in the shell instead
  }
  for (const line of raw.split('\n')) {
    const s = line.trim();
    if (!s || s.startsWith('#')) continue;
    const eq = s.indexOf('=');
    if (eq === -1) continue;
    const key = s.slice(0, eq).trim();
    let val = s.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = val;
  }
}

const cfg = {};
function requireEnv(name) {
  const v = process.env[name];
  if (!v) {
    die(
      `Missing ${name}.\n` +
        `Set it in scripts/.fb.env (gitignored — see scripts/.fb.env.example) ` +
        `or export it in your shell. Never paste the token into chat.`
    );
  }
  return v;
}
const redact = (t) => (t && t.length > 8 ? `…${t.slice(-4)}` : '(set)');

// ── tiny arg parser ──────────────────────────────────────────────────────────
function parseArgs(argv) {
  const positionals = [];
  const flags = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const body = a.slice(2);
      const eq = body.indexOf('=');
      if (eq !== -1) {
        flags[body.slice(0, eq)] = body.slice(eq + 1);
      } else if (i + 1 < argv.length && !argv[i + 1].startsWith('--')) {
        flags[body] = argv[++i];
      } else {
        flags[body] = true; // boolean flag
      }
    } else {
      positionals.push(a);
    }
  }
  return { positionals, flags };
}

function die(msg) {
  console.error(`✗ ${msg}`);
  process.exit(1);
}

// ── Graph API ────────────────────────────────────────────────────────────────
function apiBase() {
  const v = process.env.FB_API_VERSION || 'v23.0';
  return `https://graph.facebook.com/${v}`;
}

async function graph(method, path, { query = {}, form = null } = {}) {
  const url = new URL(`${apiBase()}/${path}`);
  for (const [k, val] of Object.entries(query)) {
    if (val !== undefined && val !== null) url.searchParams.set(k, String(val));
  }
  const init = { method };
  if (form) init.body = form; // FormData → fetch sets multipart boundary
  const res = await fetch(url, init);
  let json;
  const text = await res.text();
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { raw: text };
  }
  if (!res.ok || json.error) {
    const e = json.error || {};
    die(
      `Graph API ${res.status} on ${method} /${path}\n` +
        `  message: ${e.message || json.raw || 'unknown'}\n` +
        `  type:    ${e.type || '-'}   code: ${e.code ?? '-'}` +
        `${e.error_subcode ? ` subcode: ${e.error_subcode}` : ''}\n` +
        `  fbtrace_id: ${e.fbtrace_id || '-'}`
    );
  }
  return json;
}

function pageToken() {
  return requireEnv('FB_PAGE_ACCESS_TOKEN');
}
function pageId() {
  return requireEnv('FB_PAGE_ID');
}

// Writes are outward-facing and hard to reverse — gate them.
function assertConfirmed(flags, what) {
  if (flags.confirm === true || process.env.FB_CONFIRM === '1') return;
  die(
    `Refusing to ${what} without confirmation.\n` +
      `  Re-run with --confirm (or set FB_CONFIRM=1) once you've checked the content.`
  );
}

// ── commands ─────────────────────────────────────────────────────────────────
const commands = {
  async whoami() {
    const token = pageToken();
    const id = pageId();
    const me = await graph('GET', 'me', {
      query: { access_token: token, fields: 'id,name' },
    });
    const page = await graph('GET', id, {
      query: {
        access_token: token,
        fields: 'name,category,fan_count,followers_count,link',
      },
    });
    console.log(`✓ Token resolves to: ${me.name} (id ${me.id})`);
    if (me.id !== id) {
      console.log(
        `⚠ FB_PAGE_ID (${id}) != token identity (${me.id}). ` +
          `For a Page token these should match.`
      );
    }
    console.log(
      `  Page: ${page.name} — ${page.category || 'n/a'}\n` +
        `  followers: ${page.followers_count ?? page.fan_count ?? '?'}\n` +
        `  link: ${page.link || '-'}`
    );
    // Scope/expiry introspection only if app creds are available.
    const appId = process.env.FB_APP_ID;
    const appSecret = process.env.FB_APP_SECRET;
    if (appId && appSecret) {
      const dbg = await graph('GET', 'debug_token', {
        query: {
          input_token: token,
          access_token: `${appId}|${appSecret}`,
        },
      });
      const d = dbg.data || {};
      const exp = d.expires_at
        ? new Date(d.expires_at * 1000).toISOString()
        : 'never';
      console.log(
        `  token type: ${d.type || '?'}   expires: ${
          d.expires_at === 0 ? 'never' : exp
        }\n` + `  scopes: ${(d.scopes || []).join(', ') || '(none reported)'}`
      );
    } else {
      console.log(
        `  (set FB_APP_ID + FB_APP_SECRET to also print token scopes/expiry)`
      );
    }
  },

  // One-time: short-lived user token → long-lived user token → Page token.
  // Writes the Page token straight into scripts/.fb.env so it never has to
  // pass through stdout / the chat transcript.
  async ['bootstrap-token']() {
    const appId = requireEnv('FB_APP_ID');
    const appSecret = requireEnv('FB_APP_SECRET');
    const userToken = requireEnv('FB_USER_TOKEN');
    const id = pageId();
    const ll = await graph('GET', 'oauth/access_token', {
      query: {
        grant_type: 'fb_exchange_token',
        client_id: appId,
        client_secret: appSecret,
        fb_exchange_token: userToken,
      },
    });
    const accounts = await graph('GET', 'me/accounts', {
      query: { access_token: ll.access_token, fields: 'id,name,access_token' },
    });
    const match = (accounts.data || []).find((p) => p.id === id);
    if (!match) {
      die(
        `Page ${id} not in this user's /me/accounts. ` +
          `Either FB_PAGE_ID is wrong or the user is not an admin of it. ` +
          `Pages seen: ${(accounts.data || [])
            .map((p) => `${p.name}(${p.id})`)
            .join(', ') || 'none'}`
      );
    }
    await appendFile(
      ENV_FILE,
      `\n# Page token written by bootstrap-token ${new Date().toISOString()}\n` +
        `FB_PAGE_ACCESS_TOKEN=${match.access_token}\n`
    );
    console.log(
      `✓ Long-lived Page token for "${match.name}" written to scripts/.fb.env ` +
        `(${redact(match.access_token)}).\n` +
        `  This Page token does not expire. Run: npm run fb -- whoami`
    );
  },

  // Resolve the whole "which portfolio owns the Page / what is 31102…"
  // question from the API instead of the Business Settings UI. Needs only a
  // short-lived USER token (scopes: business_management, pages_show_list,
  // pages_read_engagement). Read-only.
  async discover(_pos, flags) {
    const userToken = requireEnv('FB_USER_TOKEN');
    const q = { access_token: userToken };
    const me = await graph('GET', 'me', { query: { ...q, fields: 'id,name' } });
    console.log(`You: ${me.name} (id ${me.id})\n`);

    const KNOWN = '1183365767175630'; // "Get Aplomb" — known controllable
    const prefix = String(flags['id-prefix'] || '31102');

    const biz = await graph('GET', 'me/businesses', {
      query: { ...q, fields: 'id,name,verification_status', limit: 100 },
    });
    console.log('Business portfolios you are attached to:');
    for (const b of biz.data || []) {
      const tag =
        b.id === KNOWN
          ? '  ← known controllable ("Get Aplomb")'
          : b.id.startsWith(prefix)
          ? `  ← matches the ${prefix}… you mentioned`
          : '';
      console.log(`  ${b.id}  ${b.name}  [${b.verification_status || '?'}]${tag}`);
    }
    if (!biz.data || !biz.data.length)
      console.log('  (none — you may not be on any portfolio with this token)');

    const acc = await graph('GET', 'me/accounts', {
      query: { ...q, fields: 'id,name,tasks,link,business{id,name}', limit: 100 },
    });
    console.log('\nPages you can access:');
    let aplomb = null;
    for (const p of acc.data || []) {
      const owner = p.business
        ? `${p.business.name} (${p.business.id})`
        : 'NO portfolio (personal-only)';
      const canPost = (p.tasks || []).some((t) =>
        ['CREATE_CONTENT', 'MANAGE'].includes(t)
      );
      console.log(
        `  ${p.name}  id ${p.id}\n` +
          `    owner: ${owner}\n` +
          `    your tasks: ${(p.tasks || []).join(', ') || '(none)'}  ` +
          `→ can post: ${canPost ? 'YES' : 'NO'}`
      );
      if (/aplomb/i.test(p.name) || /getaplomb/i.test(p.link || '')) aplomb = p;
    }
    if (!acc.data || !acc.data.length) console.log('  (none)');

    console.log('\n— Verdict —');
    if (!aplomb) {
      console.log(
        'No Page with "aplomb" in the name found on this token. Either the ' +
          'token lacks pages_show_list, or your user is not assigned to the ' +
          'Page. Tell me the Page name and I will adjust.'
      );
      return;
    }
    const ownerBiz = aplomb.business;
    const canPost = (aplomb.tasks || []).some((t) =>
      ['CREATE_CONTENT', 'MANAGE'].includes(t)
    );
    console.log(`Page "${aplomb.name}" id ${aplomb.id}`);
    console.log(
      `Owned by: ${
        ownerBiz ? `${ownerBiz.name} (${ownerBiz.id})` : 'no portfolio'
      }`
    );
    if (ownerBiz && ownerBiz.id.startsWith(prefix))
      console.log(`So "${prefix}…" = the portfolio "${ownerBiz.name}".`);
    console.log(
      canPost
        ? `You CAN create content on it (tasks: ${aplomb.tasks.join(', ')}).\n` +
            `Next: set FB_PAGE_ID=${aplomb.id} in scripts/.fb.env, then I run ` +
            `bootstrap-token to mint the non-expiring Page token. No portfolio ` +
            `move needed.`
        : `You do NOT have content/manage tasks on it (tasks: ${
            aplomb.tasks?.join(', ') || 'none'
          }).\nThis is the access gap — you must be granted CREATE_CONTENT/` +
            `MANAGE on the Page (or Admin on its portfolio) before a posting ` +
            `token can exist.`
    );
  },

  async posts(_pos, flags) {
    const limit = flags.limit || 10;
    const r = await graph('GET', `${pageId()}/published_posts`, {
      query: {
        access_token: pageToken(),
        fields: 'id,created_time,message,permalink_url',
        limit,
      },
    });
    for (const p of r.data || []) {
      const msg = (p.message || '(no text)').replace(/\s+/g, ' ').slice(0, 90);
      console.log(`${p.created_time}  ${p.id}\n  ${msg}\n  ${p.permalink_url}`);
    }
    if (!r.data || !r.data.length) console.log('(no published posts)');
  },

  async comments(pos) {
    const postId = pos[0] || die('usage: comments <postId>');
    const r = await graph('GET', `${postId}/comments`, {
      query: {
        access_token: pageToken(),
        fields: 'id,from,message,created_time',
        limit: 50,
      },
    });
    for (const c of r.data || []) {
      console.log(
        `${c.created_time}  ${c.id}  ${c.from?.name || 'unknown'}\n  ${
          c.message || ''
        }`
      );
    }
    if (!r.data || !r.data.length) console.log('(no comments)');
  },

  async insights() {
    // impressions/page_fans were deprecated Nov 2025 → use *_views metrics.
    const r = await graph('GET', `${pageId()}/insights`, {
      query: {
        access_token: pageToken(),
        metric: 'page_views_total,page_post_engagements,page_daily_follows',
        period: 'days_28',
      },
    });
    for (const m of r.data || []) {
      const last = m.values?.[m.values.length - 1];
      console.log(`${m.name}: ${last ? JSON.stringify(last.value) : 'n/a'}`);
    }
    if (!r.data || !r.data.length)
      console.log('(no insights — Page may be too new)');
  },

  async post(_pos, flags) {
    const message = flags.message;
    if (!message && !flags.link) die('post needs --message and/or --link');
    assertConfirmed(flags, 'publish a post');
    const query = { access_token: pageToken() };
    if (message) query.message = message;
    if (flags.link) query.link = flags.link;
    if (flags.schedule) {
      const ts = Math.floor(new Date(flags.schedule).getTime() / 1000);
      if (!ts) die(`--schedule must be an ISO 8601 datetime (got ${flags.schedule})`);
      const now = Math.floor(Date.now() / 1000);
      if (ts < now + 600 || ts > now + 75 * 86400) {
        die('Scheduled time must be 10 minutes to 75 days from now (Graph API rule).');
      }
      query.published = 'false';
      query.scheduled_publish_time = ts;
    }
    const r = await graph('POST', `${pageId()}/feed`, { query });
    console.log(
      flags.schedule
        ? `✓ Scheduled. id ${r.id} (publishes ${flags.schedule})`
        : `✓ Published. id ${r.id}`
    );
  },

  async photo(_pos, flags) {
    const img = flags.image || die('photo needs --image PATH');
    assertConfirmed(flags, 'publish a photo');
    const buf = await readFile(resolve(process.cwd(), img));
    const fd = new FormData();
    fd.set('access_token', pageToken());
    if (flags.message) fd.set('caption', flags.message);
    fd.set('source', new Blob([buf]), img.split('/').pop());
    const r = await graph('POST', `${pageId()}/photos`, { form: fd });
    console.log(`✓ Photo published. post_id ${r.post_id || r.id}`);
  },

  async reply(pos, flags) {
    const commentId = pos[0] || die('usage: reply <commentId> --message "…"');
    const message = flags.message || die('reply needs --message');
    assertConfirmed(flags, 'reply to a comment');
    const r = await graph('POST', `${commentId}/comments`, {
      query: { access_token: pageToken(), message },
    });
    console.log(`✓ Replied. id ${r.id}`);
  },

  async hide(pos, flags) {
    const commentId = pos[0] || die('usage: hide <commentId>');
    assertConfirmed(flags, 'hide a comment');
    await graph('POST', commentId, {
      query: { access_token: pageToken(), is_hidden: 'true' },
    });
    console.log(`✓ Hidden ${commentId}`);
  },

  async delete(pos, flags) {
    const id = pos[0] || die('usage: delete <postId|commentId>');
    assertConfirmed(flags, `delete ${id}`);
    await graph('DELETE', id, { query: { access_token: pageToken() } });
    console.log(`✓ Deleted ${id}`);
  },

  help() {
    console.log(
      `APLOMB. Facebook Page control — npm run fb -- <command>\n\n` +
        `  whoami                         verify token + identity (+scopes if app creds set)\n` +
        `  discover                       (user token) list portfolios + Pages + who owns what\n` +
        `  bootstrap-token                one-time: user token → Page token → scripts/.fb.env\n` +
        `  posts [--limit N]              list recent published posts\n` +
        `  comments <postId>              list comments on a post\n` +
        `  insights                       Page views / engagement (28d)\n` +
        `  post --message "…" [--link URL] [--schedule ISO8601] --confirm\n` +
        `  photo --image PATH [--message "…"] --confirm\n` +
        `  reply <commentId> --message "…" --confirm\n` +
        `  hide <commentId> --confirm\n` +
        `  delete <postId|commentId> --confirm\n\n` +
        `Reads need no flag. Writes need --confirm (or FB_CONFIRM=1).\n` +
        `Secrets: scripts/.fb.env (gitignored) or shell env. Never pasted in chat.`
    );
  },
};

// ── entry ────────────────────────────────────────────────────────────────────
async function main() {
  await loadEnvFile();
  const { positionals, flags } = parseArgs(process.argv.slice(2));
  const cmd = positionals.shift() || 'help';
  const fn = commands[cmd];
  if (!fn) {
    console.error(`Unknown command: ${cmd}\n`);
    commands.help();
    process.exit(1);
  }
  await fn(positionals, flags);
}

main().catch((err) => {
  // Never let a raw token surface in an unexpected stack trace.
  const msg = String(err && err.stack ? err.stack : err);
  console.error(`✗ ${msg.replace(/access_token=[^&\s]+/g, 'access_token=[redacted]')}`);
  process.exit(1);
});
