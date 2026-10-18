#!/usr/bin/env bash
# Build the container image in the cloud with Cloud Build (no local Docker needed)
# and push it to Artifact Registry.
#
# Usage: scripts/build.sh <version>        e.g. scripts/build.sh v1
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

VERSION="${1:?Usage: scripts/build.sh <version>  (e.g. v1)}"
validate_version "$VERSION"

echo "==> Building $IMAGE:$VERSION with Cloud Build"
gc builds submit "$LAB_DIR" --region "$REGION" --tag "$IMAGE:$VERSION"

echo "==> Pushed $IMAGE:$VERSION"
