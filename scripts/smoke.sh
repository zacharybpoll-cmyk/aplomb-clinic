#!/usr/bin/env bash
# APLOMB. — production smoke battery (Tier 1 static/SEO/cache/security/CAPI,
# Tier 2 negative server endpoints, Tier 4.1 email templates).
#
# Read-only against production. Tier 2 only hits negative/idempotent paths that
# bail before any Stripe/Supabase mutation (verified: bad-product checkout
# returns before customer creation; bad-token callback creates no session).
#
# Usage:  bash scripts/smoke.sh
#         BASE_URL=https://staging.example npm run smoke
#
# Exit code: 0 only if every gated check passes. Non-zero on any FAIL.
#
# Secrets: never hard-coded. Tier 1.10 (Meta CAPI liveness) reads
# META_CAPI_ACCESS_TOKEN from the environment and SKIPs (not FAILs) if absent.
#
# False-positive guards encoded here (see scripts/README.md):
#   #1 SPA 200-fallback  -> assert on response BODY (page-unique marker), not status.
#   #2 CF Browser-Cache-TTL clamp -> assert cache-control CONTAINS `must-revalidate`,
#      never an exact max-age (the zone rewrites max-age=0 up to 14400).

set -uo pipefail

BASE_URL="${BASE_URL:-https://getaplomb.com}"
ASSET_V="v=20260515"                 # the cache-bust the live HTML actually references
NEW_PIXEL="998365759355238"          # public Meta pixel id (not a secret)
OLD_PIXEL="1098073211496489"         # decommissioned pixel id — must be gone everywhere

PASS=0; FAIL=0; SKIP=0; WARN=0
G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; B=$'\033[34m'; D=$'\033[2m'; X=$'\033[0m'

pass(){ PASS=$((PASS+1)); printf '  %sPASS%s %s\n' "$G" "$X" "$1"; }
fail(){ FAIL=$((FAIL+1)); printf '  %sFAIL%s %s\n' "$R" "$X" "$1"; }
skip(){ SKIP=$((SKIP+1)); printf '  %sSKIP%s %s\n' "$Y" "$X" "$1"; }
warn(){ WARN=$((WARN+1)); printf '  %sWARN%s %s\n' "$Y" "$X" "$1"; }
hdr(){  printf '\n%s== %s ==%s\n' "$B" "$1" "$X"; }

cb(){ echo "cb=$RANDOM$RANDOM$$"; }   # cache-buster: defeats any poisoned edge entry

# NOTE: every fetch captures the response into a variable BEFORE grepping.
# Piping `curl | grep -q` is unsafe here: grep -q exits on first match and
# closes the pipe, curl dies with SIGPIPE (141), and `set -o pipefail` then
# reports the whole pipeline as failed even though the match succeeded — a
# false FAIL that only bites on large pages. Capture-then-grep avoids it.

# body_has URL NEEDLE DESC  — fetch (cache-busted) and search the body
body_has(){
  local url="$1" needle="$2" desc="$3" sep='?' body
  [[ "$url" == *\?* ]] && sep='&'
  body=$(curl -fsS --max-time 25 "${url}${sep}$(cb)" 2>/dev/null)
  if [[ -n "$body" && "$body" == *"$needle"* ]]; then
    pass "$desc ${D}(body contains: ${needle:0:48})${X}"
  else
    fail "$desc ${D}(body missing: ${needle:0:48})${X}"
  fi
}

# body_lacks URL NEEDLE DESC
body_lacks(){
  local url="$1" needle="$2" desc="$3" sep='?' body
  [[ "$url" == *\?* ]] && sep='&'
  body=$(curl -fsS --max-time 25 "${url}${sep}$(cb)" 2>/dev/null)
  if [[ -z "$body" ]]; then
    fail "$desc ${D}(no body returned — cannot verify absence of ${needle})${X}"
  elif [[ "$body" == *"$needle"* ]]; then
    fail "$desc ${D}(body unexpectedly contains: ${needle})${X}"
  else
    pass "$desc ${D}(absent: ${needle})${X}"
  fi
}

# header_has URL EREGEX DESC  — search the response headers
header_has(){
  local url="$1" re="$2" desc="$3" hdrs
  hdrs=$(curl -fsSI --max-time 25 "$url" 2>/dev/null)
  if printf '%s' "$hdrs" | grep -qiE -- "$re"; then
    pass "$desc"
  else
    fail "$desc ${D}(header /$re/ not found)${X}"
  fi
}

# redirect_to URL SUBSTR DESC  — assert 3xx and Location/redirect contains SUBSTR
redirect_to(){
  local url="$1" sub="$2" desc="$3"
  local out code loc
  out=$(curl -sS --max-time 25 -o /dev/null -w '%{http_code} %{redirect_url}' "$url" 2>/dev/null)
  code="${out%% *}"; loc="${out#* }"
  if [[ "$code" =~ ^3 ]] && [[ "$loc" == *"$sub"* ]]; then
    pass "$desc ${D}($code -> ${sub})${X}"
  else
    fail "$desc ${D}(got $code -> ${loc:0:70})${X}"
  fi
}

# status_eq URL CODE DESC
status_eq(){
  local url="$1" want="$2" desc="$3" got
  got=$(curl -sS --max-time 25 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)
  if [[ "$got" == "$want" ]]; then pass "$desc ${D}($got)${X}"; else fail "$desc ${D}(want $want got $got)${X}"; fi
}

# post_4xx URL DATA EXPECT_SUBSTR DESC  — POST, assert 4xx + body substring
post_4xx(){
  local url="$1" data="$2" expect="$3" desc="$4" resp code body
  resp=$(curl -sS --max-time 25 -X POST "$url" -H 'Content-Type: application/json' --data "$data" -w '\n%{http_code}' 2>/dev/null)
  code="${resp##*$'\n'}"; body="${resp%$'\n'*}"
  if [[ "$code" =~ ^4 ]] && [[ "$body" == *"$expect"* ]]; then
    pass "$desc ${D}($code; \"$expect\")${X}"
  else
    fail "$desc ${D}(want 4xx+\"$expect\"; got $code ${body:0:80})${X}"
  fi
}

printf '%sAPLOMB. smoke battery%s  base=%s\n' "$B" "$X" "$BASE_URL"

# ─────────────────────────────────────────────────────────── Tier 1 ──────────
hdr "Tier 1 — static / SEO / cache / security / CAPI"

# 1.1 analytics.js is the new build. The pixel ID lives in HTML <meta> tags by
#     design, NOT in the JS — so we assert the consent fn + absence of old pixel.
body_has  "$BASE_URL/assets/analytics.js?$ASSET_V" "adConsentGranted" "1.1 analytics.js exposes adConsentGranted (consent gate live)"
body_lacks "$BASE_URL/assets/analytics.js?$ASSET_V" "$OLD_PIXEL"      "1.1 analytics.js free of decommissioned pixel id"

# 1.2 checkout.js forwards consent into the cart payload
body_has  "$BASE_URL/assets/checkout.js?$ASSET_V" "adConsent" "1.2 checkout.js carries adConsent in cart payload"

# 1.3 pixel-id swap + versioned asset ref across home + PDPs
for p in "/" "/serum/" "/roots/" "/calm/" "/breath/"; do
  body_has  "$BASE_URL$p" "$NEW_PIXEL"                 "1.3 ${p} uses new pixel id"
  body_lacks "$BASE_URL$p" "$OLD_PIXEL"                "1.3 ${p} free of old pixel id"
done
body_has "$BASE_URL/" "analytics.js?$ASSET_V" "1.3 home references versioned analytics.js (cache-bust live)"

# 1.4 cache header fixed — assert on the URL the live HTML actually loads.
#     Guard #2: require `must-revalidate`; do NOT assert exact max-age.
header_has "$BASE_URL/assets/analytics.js?$ASSET_V" "cache-control:.*must-revalidate" "1.4 versioned analytics.js sends must-revalidate"
header_has "$BASE_URL/css/site.css?$(cb)"           "cache-control:.*must-revalidate" "1.4 css assets send must-revalidate"
# Informational only (never gates exit): the pre-PR#32 bare-URL edge entry may
# still be 'immutable' until it ages out. Not user-facing — live HTML is
# DYNAMIC (never edge-cached) and references the ?v= URL.
if curl -fsSI --max-time 20 "$BASE_URL/assets/analytics.js" 2>/dev/null | grep -qi 'immutable'; then
  warn "1.4 bare /assets/analytics.js still serves a stale 'immutable' edge entry (residual; not referenced by live HTML — optional CF cache purge to evict)"
fi

# 1.5 security headers
header_has "$BASE_URL/" "strict-transport-security"                 "1.5 HSTS present"
header_has "$BASE_URL/" "x-content-type-options:\s*nosniff"         "1.5 X-Content-Type-Options nosniff"
header_has "$BASE_URL/" "referrer-policy:\s*strict-origin"          "1.5 Referrer-Policy strict-origin-when-cross-origin"
header_has "$BASE_URL/" "permissions-policy"                         "1.5 Permissions-Policy present"
header_has "$BASE_URL/" "content-security-policy(-report-only)?:"    "1.5 CSP (report-only) present"

# 1.6 SEO / GEO files
body_has "$BASE_URL/robots.txt"  "User-agent: GPTBot"  "1.6 robots.txt has AI-crawler directives"
body_has "$BASE_URL/robots.txt"  "ClaudeBot"           "1.6 robots.txt allows ClaudeBot"
body_has "$BASE_URL/llms.txt"    "# APLOMB."           "1.6 llms.txt present"
body_has "$BASE_URL/sitemap.xml" "<lastmod>"           "1.6 sitemap has <lastmod>"
body_has "$BASE_URL/sitemap.xml" "image:image"         "1.6 sitemap has image namespace"
body_lacks "$BASE_URL/sitemap.xml" "/daily/"           "1.6 sitemap free of dead /daily/ url"

# 1.7 JSON-LD structured data
body_has "$BASE_URL/faq/"   '"@type": "FAQPage"'  "1.7 /faq/ has FAQPage schema"
body_has "$BASE_URL/about/" '"@type": "Person"'   "1.7 /about/ has Person schema"
body_has "$BASE_URL/serum/" '"@type": "Product"'  "1.7 /serum/ has Product schema"

# 1.8 anti-SPA-200 — real page bodies (guard #1: a page-unique marker)
body_has "$BASE_URL/"                     "For women on GLP-1."                 "1.8 / renders real content"
body_has "$BASE_URL/serum/"               "dermal half of GLP-1"                "1.8 /serum/ renders real content"
body_has "$BASE_URL/faq/"                 "Frequently Asked Questions."         "1.8 /faq/ renders real content"
body_has "$BASE_URL/about/"               "A line built where it should"        "1.8 /about/ renders real content"
body_has "$BASE_URL/legal/cookie-policy/" "Cookie Policy"                       "1.8 /legal/cookie-policy/ renders real content"
body_has "$BASE_URL/legal/privacy/"       "Privacy Policy"                      "1.8 /legal/privacy/ renders real content"

# 1.9 privacy/cookie copy is accurate to the consent implementation
body_has "$BASE_URL/legal/cookie-policy/" "May 15, 2026"            "1.9 cookie-policy effective-dated"
body_has "$BASE_URL/legal/cookie-policy/" "Meta Pixel"              "1.9 cookie-policy discloses Meta Pixel"
body_has "$BASE_URL/legal/privacy/"       "Global Privacy Control"  "1.9 privacy policy commits to honoring GPC"

# 1.10 Meta CAPI credential liveness. A Conversions API access token is scoped
#      to event ingestion only (it cannot read the dataset node — that returns
#      "Missing Permission"), so the correct liveness probe is a POST to
#      /events. We ALWAYS attach a test_event_code: events tagged with one are
#      excluded from standard conversion reporting/optimization and surface only
#      in the Events Manager → Test Events tab, so this never pollutes
#      production metrics. Any string works as a code (no dashboard setup
#      needed); override with META_TEST_EVENT_CODE to watch it land live.
if [[ -n "${META_CAPI_ACCESS_TOKEN:-}" ]]; then
  now=$(date +%s)
  em=$(printf '%s' "smoke@getaplomb.com" | shasum -a 256 | cut -d' ' -f1)
  tec="${META_TEST_EVENT_CODE:-APLOMB_SMOKE}"
  payload="{\"data\":[{\"event_name\":\"PageView\",\"event_time\":${now},\"action_source\":\"website\",\"event_source_url\":\"${BASE_URL}/\",\"user_data\":{\"em\":[\"${em}\"],\"client_user_agent\":\"aplomb-smoke/1.0\"}}],\"test_event_code\":\"${tec}\"}"
  capi=$(curl -sS --max-time 25 -X POST "https://graph.facebook.com/v18.0/${NEW_PIXEL}/events?access_token=${META_CAPI_ACCESS_TOKEN}" -H 'Content-Type: application/json' --data "$payload" 2>/dev/null)
  if [[ "$capi" == *'"events_received":1'* ]] && [[ "$capi" != *'"error"'* ]]; then
    pass "1.10 Meta CAPI credential live ${D}(events_received:1; Test Events code=${tec})${X}"
  else
    fail "1.10 Meta CAPI rejected the event ${D}(${capi:0:160})${X}"
  fi
else
  skip "1.10 Meta CAPI — set META_CAPI_ACCESS_TOKEN to run this check"
fi

# ─────────────────────────────────────────────────────────── Tier 2 ──────────
hdr "Tier 2 — server endpoints (negative / no mutation)"

post_4xx "$BASE_URL/api/checkout" 'not-json' \
  "Invalid JSON body." "2.1 /api/checkout rejects malformed body"

post_4xx "$BASE_URL/api/checkout" \
  '{"email":"smoke@example.com","name":"Smoke Test","lineItems":[{"productKey":"__SMOKE_NOPE__","quantity":1,"mode":"onetime"}]}' \
  "Unknown product" "2.2 /api/checkout rejects bad SKU (bails before Stripe)"

redirect_to "$BASE_URL/api/auth/callback" \
  "/account/login/?error=invalid_link" "2.3 /api/auth/callback (no token) -> invalid_link"

redirect_to "$BASE_URL/api/auth/callback?token_hash=deadbeefdeadbeef&type=magiclink" \
  "error=link_expired" "2.4 /api/auth/callback (bad token) -> link_expired"

status_eq "$BASE_URL/api/account/me" "401" "2.5 /api/account/me unauthenticated -> 401"

redirect_to "$BASE_URL/admin" "aplomb-clinic.pages.dev/admin" \
  "2.6 /admin host-rewrites to the CF-Access-gated origin"
redirect_to "https://aplomb-clinic.pages.dev/admin" "cloudflareaccess.com" \
  "2.6 admin origin is gated by Cloudflare Access (not open)"

# 2.7 webhook rejects an unsigned event BEFORE any handler/DB code runs
# (verified in source: missing/bad signature returns 400 at lines 98-107,
# before supabaseAdmin/stripe_events). Prod-safe: a rejected event mutates
# nothing.
post_4xx "$BASE_URL/api/webhooks/stripe" '{"id":"evt_smoke","type":"payment_intent.succeeded"}' \
  "" "2.7 /api/webhooks/stripe rejects an unsigned event (no handler runs)"

# ─────────────────────────────────────────────────────────── Tier 4.1 ────────
hdr "Tier 4.1 — transactional email templates"
if out=$(node website/scripts/smoke-emails.mjs 2>&1); then
  n_ok=$(printf '%s\n' "$out" | grep -oE '[0-9]+ OK' | grep -oE '[0-9]+' || echo 0)
  if printf '%s\n' "$out" | grep -qE '[0-9]+ OK, 0 FAIL'; then
    pass "4.1 email templates render ${D}(${n_ok} OK, 0 FAIL)${X}"
  else
    fail "4.1 email templates: $(printf '%s\n' "$out" | tail -1)"
  fi
else
  fail "4.1 smoke-emails.mjs threw ${D}($(printf '%s\n' "$out" | tail -1))${X}"
fi

# ─────────────────────────────────────────────────────────── summary ─────────
printf '\n%s── summary ──%s\n' "$B" "$X"
printf '  %sPASS %d%s   %sFAIL %d%s   %sSKIP %d%s   %sWARN %d%s\n' \
  "$G" "$PASS" "$X" "$R" "$FAIL" "$X" "$Y" "$SKIP" "$X" "$Y" "$WARN" "$X"
[[ "$FAIL" -eq 0 ]] && { printf '%s  smoke: GREEN%s\n' "$G" "$X"; exit 0; } \
                     || { printf '%s  smoke: RED (%d failed)%s\n' "$R" "$FAIL" "$X"; exit 1; }
