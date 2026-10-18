#!/usr/bin/env bash
# Delete everything this lab created so nothing keeps billing:
# the Cloud Run service, the Artifact Registry repository (and all images in it),
# and the source archives Cloud Build uploaded.
#
# Usage: scripts/cleanup.sh            asks before deleting
#        scripts/cleanup.sh --yes      no prompt
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

echo "This will delete from project $PROJECT_ID:"
echo "  - Cloud Run service:            $SERVICE ($REGION)"
echo "  - Artifact Registry repository: $REPO ($REGION), including all images"
echo "  - Cloud Build source uploads:   gs://${PROJECT_ID}_cloudbuild/source/"
if [[ "${1:-}" != "--yes" ]]; then
    read -r -p "Continue? [y/N] " answer
    [[ "$answer" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

if service_exists; then
    echo "==> Deleting Cloud Run service $SERVICE"
    gc run services delete "$SERVICE" --region "$REGION" --quiet
else
    echo "==> Cloud Run service $SERVICE not found, skipping"
fi

if gc artifacts repositories describe "$REPO" --location "$REGION" >/dev/null 2>&1; then
    echo "==> Deleting Artifact Registry repository $REPO"
    gc artifacts repositories delete "$REPO" --location "$REGION" --quiet
else
    echo "==> Repository $REPO not found, skipping"
fi

echo "==> Deleting Cloud Build source uploads"
gc storage rm --recursive "gs://${PROJECT_ID}_cloudbuild/source/**" 2>/dev/null \
    || echo "    nothing to delete"

echo "==> Cleanup complete. The APIs stay enabled; enabled APIs cost nothing on their own."
