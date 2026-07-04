#!/usr/bin/env bash
# Seed the running stack with open-access PDF lectures via the public API (DO-07).
# Dev-deps bootstrap moved to ./dev-setup.sh.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
SEED_DIR="./seed"
TIMEOUT="${TIMEOUT:-60}"
DEMO_USER="${DEMO_USER:-demo}"
DEMO_PASSWORD="${DEMO_PASSWORD:-demo12345}"

# Open-access arXiv lecture PDFs (stable URLs, no auth). filename<TAB>url
SOURCES=(
  "attention.pdf	https://arxiv.org/pdf/1706.03762"
  "resnet.pdf	https://arxiv.org/pdf/1512.03385"
  "vgg.pdf	https://arxiv.org/pdf/1409.1556"
  "adam.pdf	https://arxiv.org/pdf/1412.6980"
  "bert.pdf	https://arxiv.org/pdf/1810.04805"
  "gan.pdf	https://arxiv.org/pdf/1406.2661"
  "batchnorm.pdf	https://arxiv.org/pdf/1502.03167"
  "word2vec.pdf	https://arxiv.org/pdf/1301.3781"
  "densenet.pdf	https://arxiv.org/pdf/1608.06993"
  "unet.pdf	https://arxiv.org/pdf/1505.04597"
)

echo "== waiting for backend at ${API_URL} =="
for ((i = 0; i < TIMEOUT; i++)); do
  if curl -fsS "${API_URL}/api/v1/health" 2>/dev/null | grep -q '"status":"ok"'; then
    break
  fi
  [ "$i" -eq $((TIMEOUT - 1)) ] && { echo "backend not healthy after ${TIMEOUT}s" >&2; exit 1; }
  sleep 1
done

echo "== authenticating as ${DEMO_USER} =="
TOKEN=$(curl -fsS -X POST "${API_URL}/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"${DEMO_USER}\",\"password\":\"${DEMO_PASSWORD}\"}" \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
[ -n "$TOKEN" ] || { echo "login failed" >&2; exit 1; }
AUTH=(-H "Authorization: Bearer ${TOKEN}")

echo "== downloading ${#SOURCES[@]} PDFs to ${SEED_DIR} =="
mkdir -p "$SEED_DIR"
for entry in "${SOURCES[@]}"; do
  name="${entry%%$'\t'*}"
  url="${entry#*$'\t'}"
  dest="${SEED_DIR}/${name}"
  if [ -s "$dest" ]; then
    echo "  have ${name}, skip"
  else
    echo "  fetch ${name}"
    curl -fSL -o "$dest" "$url"
  fi
done

echo "== uploading via ${API_URL}/api/v1/documents/upload =="
ok=0
fail=0
for entry in "${SOURCES[@]}"; do
  name="${entry%%$'\t'*}"
  dest="${SEED_DIR}/${name}"
  if id=$(curl -fsS "${AUTH[@]}" -F "file=@${dest};type=application/pdf" \
      "${API_URL}/api/v1/documents/upload" | grep -o '"id":"[^"]*"'); then
    echo "  uploaded ${name} -> ${id}"
    ok=$((ok + 1))
  else
    echo "  FAILED ${name}" >&2
    fail=$((fail + 1))
  fi
done

echo "== summary: ${ok} uploaded, ${fail} failed =="
[ "$fail" -eq 0 ] || exit 1

echo "== waiting for indexing =="
total=${#SOURCES[@]}
for ((i = 0; i < TIMEOUT; i++)); do
  indexed=$(curl -fsS "${AUTH[@]}" "${API_URL}/api/v1/documents" | grep -o '"status":"indexed"' | wc -l | tr -d ' ')
  echo "  indexed ${indexed}/${total}"
  [ "$indexed" -ge "$total" ] && break
  [ "$i" -eq $((TIMEOUT - 1)) ] && { echo "indexing timed out" >&2; exit 1; }
  sleep 2
done

echo "== sample search =="
term="${SEARCH_TERM:-learning}"
hits=$(curl -fsS "${AUTH[@]}" "${API_URL}/api/v1/search?q=${term}" | grep -o '"total":[0-9]*' | head -1)
echo "  q='${term}' -> ${hits}"
echo "Seed complete."
