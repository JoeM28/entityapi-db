#!/bin/bash
# Idempotent Couchbase initialiser — safe to run on every docker compose up
set -e

HOST="${COUCHBASE_HOST:-couchbase}"
USER="${CB_USERNAME:-Administrator}"
PASS="${CB_PASSWORD:-password}"
BUCKET="${CB_BUCKET:-customer_bucket}"

echo ">>> Waiting for Couchbase UI to be accessible..."
until curl -sf "http://$HOST:8091/ui/index.html" > /dev/null; do
  echo "    ...not ready, retrying in 3s"
  sleep 3
done
echo ">>> Couchbase node is up."

# ── Cluster init (skip if already initialised) ──────────────────────────────
if curl -sf -u "$USER:$PASS" "http://$HOST:8091/pools/default" > /dev/null 2>&1; then
  echo ">>> Cluster already initialised — skipping."
else
  echo ">>> Initialising cluster..."
  couchbase-cli cluster-init -c "$HOST" \
    --cluster-username "$USER" \
    --cluster-password "$PASS" \
    --services data,index,query \
    --cluster-ramsize 512 \
    --cluster-index-ramsize 256
  echo ">>> Cluster initialised."
fi

# ── Bucket creation (skip if already exists) ────────────────────────────────
if curl -sf -u "$USER:$PASS" "http://$HOST:8091/pools/default/buckets/$BUCKET" > /dev/null 2>&1; then
  echo ">>> Bucket '$BUCKET' already exists — skipping."
else
  echo ">>> Creating bucket '$BUCKET'..."
  couchbase-cli bucket-create -c "$HOST" \
    -u "$USER" -p "$PASS" \
    --bucket "$BUCKET" \
    --bucket-type couchbase \
    --bucket-ramsize 256
  echo ">>> Bucket '$BUCKET' created."
fi

echo ">>> Couchbase is ready. Startup complete."
