#!/usr/bin/env bash
# Shared setup sourced by every script: loads config.env and derives common values.
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../config.env
source "$LAB_DIR/config.env"

if [[ "$PROJECT_ID" == "your-project-id" || -z "$PROJECT_ID" ]]; then
    echo "ERROR: set PROJECT_ID in config.env first (see: gcloud projects list)" >&2
    exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
    echo "ERROR: gcloud not found. Install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install" >&2
    exit 1
fi

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}"

# Every gcloud call targets the configured project, regardless of the active gcloud config
gc() { gcloud --project "$PROJECT_ID" "$@"; }

service_exists() {
    gc run services describe "$SERVICE" --region "$REGION" >/dev/null 2>&1
}

service_url() {
    gc run services describe "$SERVICE" --region "$REGION" --format 'value(status.url)'
}

# Versions are used as image tags and (via revision_tag) as Cloud Run revision tags,
# so they must be lowercase letters, digits and hyphens, starting with a letter (e.g. v1, v2)
validate_version() {
    if [[ ! "$1" =~ ^[a-z][a-z0-9-]{0,19}$ ]]; then
        echo "ERROR: version '$1' must be lowercase letters/digits/hyphens, start with a letter, max 20 chars (e.g. v1)" >&2
        exit 1
    fi
}

# Cloud Run revision tags must be at least 3 characters, so v1 becomes rev-v1.
# The tag gives that revision its own URL: https://rev-v1---<service>-<hash>.<region>.run.app
revision_tag() { echo "rev-$1"; }
