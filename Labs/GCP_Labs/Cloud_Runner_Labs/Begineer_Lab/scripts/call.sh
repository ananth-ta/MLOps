#!/usr/bin/env bash
# Send N requests to the service and count which version answered each one.
# Use it after a canary deploy to see the traffic split in action.
#
# Usage: scripts/call.sh [count]        default 20
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

COUNT="${1:-20}"
URL="$(service_url)"

# Sending an identity token works whether or not the service allows unauthenticated access
TOKEN="$(gcloud auth print-identity-token 2>/dev/null || true)"
AUTH=()
[[ -n "$TOKEN" ]] && AUTH=(-H "Authorization: Bearer $TOKEN")

# ${AUTH[@]+...} expands safely when AUTH is empty, even under set -u on older bash (macOS)
echo "==> GET $URL/health"
curl -fsS ${AUTH[@]+"${AUTH[@]}"} "$URL/health"
echo
echo "==> Sending $COUNT requests to $URL/"
for _ in $(seq "$COUNT"); do
    curl -fsS ${AUTH[@]+"${AUTH[@]}"} "$URL/" | grep -o '"version": *"[^"]*"'
done | sort | uniq -c
