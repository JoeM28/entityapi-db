#!/bin/sh
# Registers Kafka Connect connectors via the REST API.
# Runs after kafka-connect is healthy (guaranteed by depends_on condition).
# Safe to re-run — skips connectors that already exist.
set -e

CONNECT_URL="http://kafka-connect:8083"

echo ">>> Kafka Connect is ready. Registering connectors..."

# ── Couchbase source connector ────────────────────────────────────────────────
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CONNECT_URL/connectors/couchbase-source")

if [ "$STATUS" = "200" ]; then
  echo ">>> couchbase-source already registered — skipping."
else
  echo ">>> Registering couchbase-source..."
  curl -sf -X POST "$CONNECT_URL/connectors" \
    -H "Content-Type: application/json" \
    -d @/connectors/couchbase-source.json
  echo ""
  echo ">>> couchbase-source registered."
fi

echo ">>> All connectors registered. Startup complete."
