#!/usr/bin/env bash
# Inspect and control how traffic is split between revisions.
#
# Usage:
#   scripts/traffic.sh status                  show URL, revisions and traffic split
#   scripts/traffic.sh split <version> <pct>   send <pct>% to <version>, the rest stays as-is
#   scripts/traffic.sh promote <version>       send 100% to <version>
#   scripts/traffic.sh rollback <version>      same as promote; use it to go back to an older version
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

CMD="${1:-status}"

case "$CMD" in
    status)
        echo "Service URL: $(service_url)"
        echo
        echo "Traffic split:"
        gc run services describe "$SERVICE" --region "$REGION" \
            --flatten 'status.traffic[]' \
            --format 'table(status.traffic.revisionName:label=REVISION, status.traffic.latestRevision:label=LATEST, status.traffic.tag:label=TAG, status.traffic.percent:label=PERCENT)'
        ;;
    split)
        VERSION="${2:?Usage: scripts/traffic.sh split <version> <percent>}"
        PCT="${3:?Usage: scripts/traffic.sh split <version> <percent>}"
        gc run services update-traffic "$SERVICE" --region "$REGION" --to-tags "$(revision_tag "$VERSION")=${PCT}"
        "$0" status
        ;;
    promote|rollback)
        VERSION="${2:?Usage: scripts/traffic.sh $CMD <version>}"
        gc run services update-traffic "$SERVICE" --region "$REGION" --to-tags "$(revision_tag "$VERSION")=100"
        "$0" status
        ;;
    *)
        echo "Unknown command '$CMD'. Use: status | split | promote | rollback" >&2
        exit 1
        ;;
esac
