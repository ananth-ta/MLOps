#!/usr/bin/env bash
# Create a private Cloud Storage bucket and configure it as this project's default DVC remote:
#   gcs     gs://<bucket>     push/pull with your own Google login
#
# Authentication uses Application Default Credentials (`gcloud auth application-default login`),
# so no service-account key file is created or stored anywhere.
#
# Usage: PROJECT_ID=my-project bash scripts/setup_remote.sh [--public]
#   --public   ALSO make the bucket publicly readable and add a read-only `public` remote
#              (https://storage.googleapis.com/<bucket>), so anyone can `dvc pull -r public`
#              without an account. Off by default; only use it for data you may publish.
# Optional: BUCKET (default <project>-dvc-lab), REGION (default us-east1)
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID first, e.g. export PROJECT_ID=my-project (see: gcloud projects list)}"
BUCKET="${BUCKET:-${PROJECT_ID}-dvc-lab}"
REGION="${REGION:-us-east1}"
PUBLIC=false
[[ "${1:-}" == "--public" ]] && PUBLIC=true

cd "$(dirname "${BASH_SOURCE[0]}")/.."

for tool in gcloud dvc; do
    command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: $tool not found (activate .venv for dvc)" >&2; exit 1; }
done

echo "==> Enabling the Cloud Storage API in $PROJECT_ID"
gcloud services enable storage.googleapis.com --project "$PROJECT_ID"

echo "==> Creating bucket gs://$BUCKET in $REGION"
if gcloud storage buckets describe "gs://$BUCKET" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "    already exists, skipping"
else
    # Uniform bucket-level access: permissions are set on the bucket, not per object
    gcloud storage buckets create "gs://$BUCKET" --project "$PROJECT_ID" \
        --location "$REGION" --uniform-bucket-level-access
fi

echo "==> Configuring DVC remote 'gcs' (default)"
dvc remote add --force --default gcs "gs://$BUCKET"
# Bill requests to this project; the credentials come from your gcloud login
dvc remote modify gcs projectname "$PROJECT_ID"

if $PUBLIC; then
    echo "==> Granting public read access to gs://$BUCKET"
    gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --project "$PROJECT_ID" \
        --member allUsers --role roles/storage.objectViewer >/dev/null
    echo "==> Configuring DVC remote 'public' (read-only HTTPS)"
    dvc remote add --force public "https://storage.googleapis.com/$BUCKET"
fi

echo
dvc remote list
if $PUBLIC; then
    echo "==> Done. Push with: dvc push   |   Anyone can pull with: dvc pull -r public"
else
    echo "==> Done. Push/pull with: dvc push / dvc pull   (private bucket: needs access to $PROJECT_ID)"
fi
