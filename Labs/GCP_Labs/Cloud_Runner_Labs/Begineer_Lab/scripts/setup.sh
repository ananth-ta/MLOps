#!/usr/bin/env bash
# One-time setup: enable the required APIs and create the Artifact Registry repository.
# Safe to re-run; existing resources are left as they are.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

echo "==> Enabling APIs (Cloud Run, Artifact Registry, Cloud Build) in $PROJECT_ID"
gc services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

echo "==> Creating Artifact Registry repository '$REPO' in $REGION"
if gc artifacts repositories describe "$REPO" --location "$REGION" >/dev/null 2>&1; then
    echo "    already exists, skipping"
else
    gc artifacts repositories create "$REPO" \
        --repository-format docker \
        --location "$REGION" \
        --description "Images for the Cloud Run lab"
fi

echo "==> Setup complete. Images will be pushed to: $IMAGE"
