#!/usr/bin/env bash
# Deploy an image version to Cloud Run as a new revision, with the scaling settings from config.env.
#
# Usage:
#   scripts/deploy.sh <version>                   deploy and send 100% of traffic to it
#   scripts/deploy.sh <version> --canary <pct>    deploy, then send only <pct>% of traffic to it
#
# Optional: GREETING="Hello from v2!" scripts/deploy.sh v2   changes the app's message
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

VERSION="${1:?Usage: scripts/deploy.sh <version> [--canary <percent>]}"
validate_version "$VERSION"
CANARY_PCT=""
if [[ "${2:-}" == "--canary" ]]; then
    CANARY_PCT="${3:?--canary needs a percentage, e.g. --canary 10}"
    if [[ ! "$CANARY_PCT" =~ ^[0-9]+$ ]] || (( CANARY_PCT < 1 || CANARY_PCT > 99 )); then
        echo "ERROR: canary percentage must be 1-99" >&2
        exit 1
    fi
fi
GREETING="${GREETING:-Hello, World!}"

DEPLOY_ARGS=(
    --image "$IMAGE:$VERSION"
    --region "$REGION"
    --allow-unauthenticated
    --port 8080
    --cpu "$CPU"
    --memory "$MEMORY"
    --concurrency "$CONCURRENCY"
    --min-instances "$MIN_INSTANCES"
    --max-instances "$MAX_INSTANCES"
    --timeout "$TIMEOUT"
    --set-env-vars "^@^APP_VERSION=${VERSION}@GREETING=${GREETING}"
    # The tag (e.g. rev-v1) gives this revision its own URL
    # and lets traffic be routed to it by name
    --tag "$(revision_tag "$VERSION")"
)

if [[ -n "$CANARY_PCT" ]]; then
    if ! service_exists; then
        echo "ERROR: --canary needs an existing service; deploy a first version without it" >&2
        exit 1
    fi
    echo "==> Deploying $VERSION with no traffic"
    gc run deploy "$SERVICE" "${DEPLOY_ARGS[@]}" --no-traffic
    echo "==> Sending ${CANARY_PCT}% of traffic to $VERSION"
    gc run services update-traffic "$SERVICE" --region "$REGION" --to-tags "$(revision_tag "$VERSION")=${CANARY_PCT}"
else
    echo "==> Deploying $VERSION with 100% of traffic"
    gc run deploy "$SERVICE" "${DEPLOY_ARGS[@]}"
    # deploy only shifts traffic automatically while the service routes to "latest";
    # after a canary or rollback it is pinned, so route explicitly
    gc run services update-traffic "$SERVICE" --region "$REGION" --to-latest >/dev/null
fi

echo
"$LAB_DIR/scripts/traffic.sh" status
