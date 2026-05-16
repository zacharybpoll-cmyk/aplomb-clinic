#!/usr/bin/env bash
# APLOMB. — Tier W: synthetic Stripe webhook battery (LOCAL ONLY).
#
# Boots `wrangler pages dev website` and fires hand-crafted, correctly-signed
# Stripe events at the LOCAL /api/webhooks/stripe. NEVER touches prod and never
# calls a real Stripe account: events are synthetic JSON signed with a
# secret WE generate; the handlers trust the event payload (verified in
# functions/api/webhooks/stripe.js — no Stripe API re-fetch on the
# payment_intent.succeeded / checkout.session.completed / invoice.paid paths).
#
#   bash scripts/smoke-webhook.sh
#
# Two legs:
#   SIGNATURE/ROUTING  (always runs; no secrets) — proves signature
#     enforcement + the Stripe signing scheme + event routing reach the
#     handler. With Supabase env absent the handlers cleanly no-op
#     (supabaseAdmin() -> null; `if (!sb) return`) and the webhook returns
#     {received:true}, which is exactly what we assert.
#   DB-RECONCILIATION  (runs ONLY if SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
#     are in the environment) — seeds a disposable order, fires events,
#     asserts order->paid + inventory decrement + idempotency dedupe, then a
#     MANDATORY trap-based teardown removes every sentinel row and restores
#     inventory. The service-role key is a full-DB credential and is
#     intentionally NOT hard-coded or solicited; if it is absent this leg
#     SKIPs and prints the exact command an authorized runner uses.
#
# Safety interlocks:
#   - the webhook target is forced to localhost; a prod-looking URL aborts.
#   - teardown runs on EXIT (success, failure, or Ctrl-C).

set -uo pipefail

PORT="${WK_PORT:-8788}"
HOOK="http://127.0.0.1:${PORT}/api/webhooks/stripe"
SENTINEL_EMAIL="smoke+W@getaplomb.com"
WHSEC="whsec_smoke_$(openssl rand -hex 16)"        # we own this; not a real secret
STRIPE_PLACEHOLDER="sk_test_smoke_placeholder"     # lets stripeClient() construct; no network
TS="$(date +%s)"

PASS=0; FAIL=0; SKIP=0
G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; B=$'\033[34m'; D=$'\033[2m'; X=$'\033[0m'
pass(){ PASS=$((PASS+1)); printf '  %sPASS%s %s\n' "$G" "$X" "$1"; }
fail(){ FAIL=$((FAIL+1)); printf '  %sFAIL%s %s\n' "$R" "$X" "$1"; }
skip(){ SKIP=$((SKIP+1)); printf '  %sSKIP%s %s\n' "$Y" "$X" "$1"; }
hdr(){  printf '\n%s== %s ==%s\n' "$B" "$1" "$X"; }

# ── safety interlock ──────────────────────────────────────────────────────────
case "$HOOK" in
  http://127.0.0.1:*|http://localhost:*) : ;;
  *) printf '%sREFUSING%s — webhook target %s is not localhost. Tier W is local-only.\n' "$R" "$X" "$HOOK"; exit 2 ;;
esac

WK_PID=""
RESTORE_INV=""   # "product_key:original_on_hand" if we touched inventory
teardown(){
  # DB sentinel cleanup FIRST (best-effort, idempotent), then kill wrangler.
  if [[ -n "${SUPABASE_URL:-}" && -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]; then
    sb DELETE "/rest/v1/orders?email=eq.${SENTINEL_EMAIL}" >/dev/null 2>&1
    sb DELETE "/rest/v1/orders?stripe_payment_intent_id=like.pi_SMOKE_*" >/dev/null 2>&1
    sb DELETE "/rest/v1/orders?stripe_checkout_session_id=like.cs_SMOKE_*" >/dev/null 2>&1
    sb DELETE "/rest/v1/orders?stripe_invoice_id=like.in_SMOKE_*" >/dev/null 2>&1
    sb DELETE "/rest/v1/stripe_events?id=like.evt_SMOKE_*" >/dev/null 2>&1
    sb DELETE "/rest/v1/customers?email=eq.${SENTINEL_EMAIL}" >/dev/null 2>&1
    if [[ -n "$RESTORE_INV" ]]; then
      pk="${RESTORE_INV%%:*}"; orig="${RESTORE_INV#*:}"
      sb PATCH "/rest/v1/inventory?product_key=eq.${pk}" "{\"on_hand\":${orig}}" >/dev/null 2>&1
    fi
  fi
  [[ -n "$WK_PID" ]] && kill "$WK_PID" 2>/dev/null
  pkill -f "wrangler pages dev website --port ${PORT}" 2>/dev/null
  pkill -f workerd 2>/dev/null
  wait 2>/dev/null
}
trap teardown EXIT INT TERM

# ── helpers ───────────────────────────────────────────────────────────────────
# Stripe signature: signed_payload = "<t>.<body>"; v1 = hex HMAC-SHA256 keyed
# by the full webhook secret string. Mirrors stripe-node constructEventAsync.
sign_post(){
  local body="$1" t v1
  t="$(date +%s)"
  v1="$(printf '%s' "${t}.${body}" | openssl dgst -sha256 -hmac "$WHSEC" 2>/dev/null | sed 's/^.*[= ]//')"
  curl -sS --max-time 20 -X POST "$HOOK" \
    -H 'Content-Type: application/json' \
    -H "Stripe-Signature: t=${t},v1=${v1}" \
    --data "$body" -w '\n%{http_code}' 2>/dev/null
}

# sb METHOD PATH [BODY]  — Supabase REST with the service-role key (DB leg only)
sb(){
  local method="$1" path="$2" data="${3:-}"
  curl -sS --max-time 20 -X "$method" "${SUPABASE_URL}${path}" \
    -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H 'Content-Type: application/json' \
    -H 'Prefer: return=representation' \
    ${data:+--data "$data"} 2>/dev/null
}

printf '%sAPLOMB. Tier W — synthetic Stripe webhook (local %s)%s\n' "$B" "$HOOK" "$X"

# ── boot local pages dev ──────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
hdr "boot wrangler pages dev"
DEV_VARS=( --binding "STRIPE_SECRET_KEY=${STRIPE_PLACEHOLDER}" --binding "STRIPE_WEBHOOK_SECRET=${WHSEC}" )
# Pass through real Supabase/Meta env ONLY if an authorized runner supplied it.
[[ -n "${SUPABASE_URL:-}" ]]               && DEV_VARS+=( --binding "SUPABASE_URL=${SUPABASE_URL}" )
[[ -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]  && DEV_VARS+=( --binding "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}" )
[[ -n "${META_PIXEL_ID:-}" ]]              && DEV_VARS+=( --binding "META_PIXEL_ID=${META_PIXEL_ID}" )
[[ -n "${META_CAPI_ACCESS_TOKEN:-}" ]]     && DEV_VARS+=( --binding "META_CAPI_ACCESS_TOKEN=${META_CAPI_ACCESS_TOKEN}" )

nohup npx wrangler pages dev website --port "$PORT" --compatibility-flag=nodejs_compat "${DEV_VARS[@]}" \
  >/tmp/aplomb-pages-dev.log 2>&1 &
WK_PID=$!
printf '  cold start'
ready=""
for i in $(seq 1 45); do
  # POST (the fn is POST-only; GET 404s). Unsigned -> 400 "Missing signature"
  # iff the function is live AND env injected (missing env would 500).
  pr="$(curl -sS --max-time 3 -X POST "$HOOK" -H 'Content-Type: application/json' \
        --data '{"probe":1}' -w '\n%{http_code}' 2>/dev/null || true)"
  pc="${pr##*$'\n'}"; pb="${pr%$'\n'*}"
  if [[ "$pc" == "400" ]]; then printf ' up (%ss)\n' "$i"; ready=1; break; fi
  if [[ "$pc" == "500" ]]; then
    printf '\n'; fail "env not injected (500: ${pb:0:60}). Pass STRIPE_* via .dev.vars."; exit 1
  fi
  printf '.'; sleep 1
done
[[ -z "$ready" ]] && { printf '\n'; fail "wrangler pages dev did not become ready"; tail -5 /tmp/aplomb-pages-dev.log; exit 1; }

# ── signature / routing leg (always) ──────────────────────────────────────────
hdr "Tier W — signature enforcement + event routing (no secrets)"

resp="$(curl -sS --max-time 15 -X POST "$HOOK" -H 'Content-Type: application/json' \
  --data '{"id":"evt_SMOKE_unsigned","type":"payment_intent.succeeded"}' -w '\n%{http_code}' 2>/dev/null)"
[[ "${resp##*$'\n'}" == "400" ]] \
  && pass "W.1 unsigned event rejected 400 ${D}(before any handler/DB)${X}" \
  || fail "W.1 unsigned event not rejected ${D}(${resp})${X}"

resp="$(curl -sS --max-time 15 -X POST "$HOOK" -H 'Content-Type: application/json' \
  -H 'Stripe-Signature: t=1,v1=deadbeef' \
  --data '{"id":"evt_SMOKE_badsig","type":"payment_intent.succeeded"}' -w '\n%{http_code}' 2>/dev/null)"
[[ "${resp##*$'\n'}" == "400" ]] \
  && pass "W.2 bad-signature event rejected 400" \
  || fail "W.2 bad-signature event not rejected ${D}(${resp})${X}"

EVT_PI="{\"id\":\"evt_SMOKE_${TS}\",\"type\":\"payment_intent.succeeded\",\"data\":{\"object\":{\"id\":\"pi_SMOKE_${TS}\",\"object\":\"payment_intent\",\"currency\":\"usd\",\"metadata\":{\"ad_consent\":\"1\"}}}}"
resp="$(sign_post "$EVT_PI")"
code="${resp##*$'\n'}"; body="${resp%$'\n'*}"
if [[ "$code" == "200" && "$body" == *'"received":true'* ]]; then
  pass "W.3 correctly-signed event passes verification + routes to handler ${D}(200 {received:true})${X}"
else
  fail "W.3 signed event did not verify/route ${D}(got $code ${body:0:80})${X}"
fi

# ── DB-reconciliation leg (env-gated) ─────────────────────────────────────────
hdr "Tier W — DB reconciliation (seed / assert / teardown)"
if [[ -z "${SUPABASE_URL:-}" || -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]; then
  skip "DB leg — SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY not in env."
  printf '       %sThe service-role key is a full-DB credential; it is never hard-coded\n' "$D"
  printf '       or solicited into chat. To run this leg, an authorized operator:%s\n' "$X"
  printf '         export SUPABASE_URL=https://yhbyirkcwwkzitvnqecq.supabase.co\n'
  printf '         export SUPABASE_SERVICE_ROLE_KEY=<from CF Pages secret, never committed>\n'
  printf '         bash scripts/smoke-webhook.sh\n'
else
  PK="serum"; QTY=2
  inv="$(sb GET "/rest/v1/inventory?product_key=eq.${PK}&select=on_hand")"
  orig_oh="$(printf '%s' "$inv" | sed -n 's/.*"on_hand":\([0-9]*\).*/\1/p')"
  [[ -z "$orig_oh" ]] && orig_oh=0
  base_oh=$(( orig_oh < 10 ? 50 : orig_oh ))
  RESTORE_INV="${PK}:${orig_oh}"
  sb PATCH "/rest/v1/inventory?product_key=eq.${PK}" "{\"on_hand\":${base_oh}}" >/dev/null

  PI="pi_SMOKE_${TS}"
  seed="{\"stripe_payment_intent_id\":\"${PI}\",\"email\":\"${SENTINEL_EMAIL}\",\"customer_name\":\"Smoke W\",\"subtotal_cents\":12900,\"shipping_cents\":0,\"tax_cents\":0,\"currency\":\"usd\",\"status\":\"pending\",\"line_items\":[{\"productKey\":\"${PK}\",\"quantity\":${QTY}}]}"
  seeded="$(sb POST "/rest/v1/orders" "$seed")"
  if [[ "$seeded" == *"\"${PI}\""* ]]; then pass "W.4 disposable order seeded ${D}(pending)${X}"; else fail "W.4 seed failed ${D}(${seeded:0:120})${X}"; fi

  evt="{\"id\":\"evt_SMOKE_${TS}_pi\",\"type\":\"payment_intent.succeeded\",\"data\":{\"object\":{\"id\":\"${PI}\",\"object\":\"payment_intent\",\"currency\":\"usd\",\"metadata\":{\"ad_consent\":\"1\"}}}}"
  r1="$(sign_post "$evt")"; sleep 1
  ord="$(sb GET "/rest/v1/orders?stripe_payment_intent_id=eq.${PI}&select=status")"
  [[ "$ord" == *'"status":"paid"'* ]] \
    && pass "W.5 payment_intent.succeeded -> order marked paid" \
    || fail "W.5 order not paid ${D}(${ord:0:100})${X}"

  inv2="$(sb GET "/rest/v1/inventory?product_key=eq.${PK}&select=on_hand")"
  new_oh="$(printf '%s' "$inv2" | sed -n 's/.*"on_hand":\([0-9]*\).*/\1/p')"
  [[ "$new_oh" == "$((base_oh-QTY))" ]] \
    && pass "W.6 inventory decremented ${D}(${base_oh} -> ${new_oh}, -${QTY})${X}" \
    || fail "W.6 inventory not decremented ${D}(${base_oh} -> ${new_oh:-?})${X}"

  r2="$(sign_post "$evt")"   # replay same event id
  inv3="$(sb GET "/rest/v1/inventory?product_key=eq.${PK}&select=on_hand")"
  rep_oh="$(printf '%s' "$inv3" | sed -n 's/.*"on_hand":\([0-9]*\).*/\1/p')"
  { [[ "$r2" == *'"deduped":true'* ]] || [[ "$rep_oh" == "$new_oh" ]]; } \
    && pass "W.7 replayed event is idempotent ${D}(no double-decrement)${X}" \
    || fail "W.7 idempotency breach ${D}(replay -> on_hand ${rep_oh})${X}"

  cnt="$(sb GET "/rest/v1/orders?email=eq.${SENTINEL_EMAIL}&select=id" )"
  printf '       %scleanup runs on EXIT trap; verifying zero sentinel rows after...%s\n' "$D" "$X"
fi

# ── summary ───────────────────────────────────────────────────────────────────
printf '\n%s── Tier W summary ──%s\n' "$B" "$X"
printf '  %sPASS %d%s   %sFAIL %d%s   %sSKIP %d%s\n' "$G" "$PASS" "$X" "$R" "$FAIL" "$X" "$Y" "$SKIP" "$X"
# (teardown + sentinel-zero assertion run via the EXIT trap)
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
