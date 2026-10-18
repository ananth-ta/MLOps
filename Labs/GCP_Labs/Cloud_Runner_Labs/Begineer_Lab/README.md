# Cloud Run Lab: Deploying, Scaling and Canary Releases on Google Cloud Run

This lab deploys a containerized Flask app to **Google Cloud Run**, the serverless container platform on Google Cloud Platform (GCP). The original lab (kept in [instructions.md](instructions.md)) builds an image locally, pushes it to Container Registry and deploys it by clicking through the Cloud Console.

This version turns that into a **repeatable, scripted deployment workflow**:

- a production-ready container
- images built in the cloud and stored in **Artifact Registry**
- deployments with explicit **autoscaling limits**
- **canary releases** with traffic splitting, rollback and promotion between revisions
- a **cleanup** script so nothing keeps billing

---

## Contents
- [What changed from the original lab](#what-changed-from-the-original-lab)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the lab](#running-the-lab)
- [Cleaning up](#cleaning-up)
- [Troubleshooting](#troubleshooting)

---

## What changed from the original lab

### 1. Production-ready container ([Dockerfile](Dockerfile), [requirements.txt](requirements.txt))

| Original | Now | Why |
|---|---|---|
| `python:3.8-slim` | `python:3.13-slim` | Python 3.8 is end-of-life and no longer gets security fixes. |
| `RUN pip install flask` (no version) | Pinned `requirements.txt` (`flask==3.1.3`, `gunicorn==26.2.0`) | The same image is built every time. A new Flask release can't silently change it. |
| `COPY . /app` | Copy `requirements.txt` → install → copy `app.py` | Dependencies sit in their own cached image layer, so changing only the code rebuilds in seconds. `.dockerignore` keeps tests, scripts and docs out of the image. |
| Flask development server (`python app.py`) | `gunicorn` (1 worker, 8 threads) | Flask's built-in server is for development only and handles requests poorly under load. |
| Port 8080 hard-coded | Binds to `$PORT` | Cloud Run tells the container which port to listen on through `$PORT`. Ignoring it only works by coincidence. |
| Runs as `root` | Runs as unprivileged `appuser` | If the app is compromised, the attacker has fewer privileges. |
| — | `exec gunicorn ...` | gunicorn becomes the container's main process (PID 1), so it receives Cloud Run's shutdown signal and finishes in-flight requests. |

The app ([app.py](app.py)) now returns JSON with its `version` and the Cloud Run `revision` that served the request, so traffic splits are visible. It also has a `/health` endpoint.

### 2. Artifact Registry instead of Container Registry
The original pushes to `gcr.io` (Container Registry), which Google has **shut down**, so that step no longer works. Images now go to an Artifact Registry Docker repository: `us-central1-docker.pkg.dev/<project>/cloud-run-lab/hello-cloud-run:<version>`.

Images are built with **Cloud Build** (`gcloud builds submit`), so **Docker does not need to be installed locally**.

### 3. Deployment as code, with explicit autoscaling ([config.env](config.env), [scripts/deploy.sh](scripts/deploy.sh))
Instead of clicking through the Console, every deploy applies the same settings from `config.env`:

| Setting | Value | Effect |
|---|---|---|
| `MIN_INSTANCES` | `0` | Scales to zero when idle, so **no cost without traffic**. |
| `MAX_INSTANCES` | `3` | Caps how far it scales out, which also caps cost. |
| `CONCURRENCY` | `80` | Maximum simultaneous requests per container before Cloud Run starts another instance. |
| `CPU` / `MEMORY` | `1` / `512Mi` | Resources for each instance. |
| `TIMEOUT` | `30s` | Maximum time a single request may take. |

Each deploy creates a new immutable **revision**, labelled with its version (`APP_VERSION`) and a **revision tag** (`rev-v1`, `rev-v2`, …). Each tag gets its own URL, so a version can be tested directly before it receives any real traffic.

### 4. Canary releases, rollback and promotion ([scripts/deploy.sh](scripts/deploy.sh), [scripts/traffic.sh](scripts/traffic.sh))
- `deploy.sh v2 --canary 10` deploys v2 with **0%** of traffic, then shifts **10%** to it. The other 90% stays on the current version.
- `traffic.sh split v2 50` changes the split.
- `traffic.sh promote v2` sends 100% to v2. `traffic.sh rollback v1` sends 100% back to v1 **instantly**, with no rebuild or redeploy, because the old revision still exists.
- `call.sh 50` sends 50 requests and counts which version answered each, to check the split.

### 5. Cleanup ([scripts/cleanup.sh](scripts/cleanup.sh))
Deletes the Cloud Run service, the Artifact Registry repository with all its images, and the source archives Cloud Build uploaded.

### Also added
- [tests/test_app.py](tests/test_app.py): pytest tests of the app's endpoints and environment-variable handling.
- `.gitattributes`: keeps shell scripts with Unix (LF) line endings on Windows checkouts. Otherwise bash fails with `$'\r': command not found`.

---

## Project structure
```
Begineer_Lab/
├── app.py                 # Flask app: / (greeting + version + revision) and /health
├── Dockerfile             # Production container: python:3.13-slim, gunicorn, non-root, $PORT
├── requirements.txt       # Runtime dependencies (pinned)
├── requirements-dev.txt   # + pytest, for running the tests locally
├── config.env             # Project, region, repository, service name and scaling settings
├── .dockerignore          # Files kept out of the image
├── .gcloudignore          # Files not uploaded to Cloud Build
├── .gitattributes         # Forces LF line endings for scripts
├── scripts/
│   ├── common.sh          # Shared helpers, sourced by every script
│   ├── setup.sh           # One-time: enable APIs, create the Artifact Registry repository
│   ├── build.sh           # Build the image with Cloud Build and push it to Artifact Registry
│   ├── deploy.sh          # Deploy a version (optionally as a canary)
│   ├── traffic.sh         # status | split | promote | rollback
│   ├── call.sh            # Send N requests and count responses per version
│   └── cleanup.sh         # Delete everything the lab created
├── tests/test_app.py      # pytest tests of the app
├── instructions.md        # The original lab instructions
└── README.md
```

---

## Prerequisites

| Requirement | Version used | Notes |
|---|---|---|
| Google Cloud account with **billing enabled** | — | Free-trial or education credits work. This lab costs a few cents at most; with `MIN_INSTANCES=0` an idle service costs nothing. |
| [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) | 589.0.0 | Includes `gcloud` and `gcloud storage`. |
| A bash shell | bash 5 | Linux/macOS terminal, or **Git Bash** on Windows (installed with [Git for Windows](https://git-scm.com/download/win)). |
| `git` and `curl` | any recent version | Included with Git for Windows and with macOS/Linux. |
| Python (optional) | 3.13 | Only for running the tests locally. |

**Docker is not required**: images are built in the cloud by Cloud Build.

> **Easiest option:** open [Google Cloud Shell](https://shell.cloud.google.com/) in the browser. It already has `gcloud`, `git`, `curl`, bash and Python, and is signed in to your account. Start at step 2 below.

### Installing the Google Cloud SDK
- **Windows:** `winget install --id Google.CloudSDK`, or download the installer from the link above. Then open a **new** Git Bash window.
- **macOS:** `brew install --cask google-cloud-sdk`
- **Linux:** follow the [official instructions](https://cloud.google.com/sdk/docs/install).

Check it's installed: `gcloud --version`

---

## Setup

### 1. Get the code
```bash
git clone https://github.com/ananth-ta/MLOps.git
cd MLOps/Labs/GCP_Labs/Cloud_Runner_Labs/Begineer_Lab
```

### 2. Sign in and choose a project
```bash
gcloud auth login            # opens a browser to sign in
gcloud projects list         # find your PROJECT_ID (not the project name)
```
To create a new project instead, do it in the [Cloud Console](https://console.cloud.google.com/projectcreate) and link a billing account to it under **Billing**.

### 3. Point the scripts at your project
Either edit `PROJECT_ID` in [config.env](config.env), or set it for the current shell:
```bash
export PROJECT_ID=your-project-id
```
The other settings in `config.env` (region, repository name, service name, scaling) work as they are.

### 4. One-time GCP setup
```bash
bash scripts/setup.sh
```
This enables the Cloud Run, Artifact Registry and Cloud Build APIs, and creates the `cloud-run-lab` Docker repository. Expected output:
```
==> Enabling APIs (Cloud Run, Artifact Registry, Cloud Build) in <project>
Operation "operations/..." finished successfully.
==> Creating Artifact Registry repository 'cloud-run-lab' in us-central1
Created repository [cloud-run-lab].
==> Setup complete. Images will be pushed to: us-central1-docker.pkg.dev/<project>/cloud-run-lab/hello-cloud-run
```

---

## Running the lab
All commands are run from the `Begineer_Lab/` folder. The output below is from an actual run. Your service URL and revision names will differ.

### Step 1: Build v1 in the cloud
```bash
bash scripts/build.sh v1
```
This takes about 30 seconds. Success ends with:
```
DONE
... us-central1-docker.pkg.dev/<project>/cloud-run-lab/hello-cloud-run:v1  SUCCESS
==> Pushed us-central1-docker.pkg.dev/<project>/cloud-run-lab/hello-cloud-run:v1
```

### Step 2: Deploy v1
```bash
bash scripts/deploy.sh v1
```
```
Service [hello-cloud-run] revision [hello-cloud-run-00001-riw] has been deployed and is serving 100 percent of traffic.
Service URL: https://hello-cloud-run-822350391039.us-central1.run.app
The revision can be reached directly at https://rev-v1---hello-cloud-run-7y22eckxwa-uc.a.run.app

Traffic split:
REVISION                   LATEST  TAG     PERCENT
hello-cloud-run-00001-riw  True    rev-v1  100
```

### Step 3: Call the service
```bash
bash scripts/call.sh 10
```
```
==> GET https://hello-cloud-run-7y22eckxwa-uc.a.run.app/health
{"status":"ok"}
==> Sending 10 requests to https://hello-cloud-run-7y22eckxwa-uc.a.run.app/
     10 "version":"v1"
```
Opening the service URL in a browser shows:
```json
{"message":"Hello, World!","revision":"hello-cloud-run-00001-riw","version":"v1"}
```

### Step 4: Build v2 and release it as a 10% canary
```bash
bash scripts/build.sh v2
GREETING="Hello from v2!" bash scripts/deploy.sh v2 --canary 10
```
```
Service [hello-cloud-run] revision [hello-cloud-run-00002-wum] has been deployed and is serving 0 percent of traffic.
The revision can be reached directly at https://rev-v2---hello-cloud-run-7y22eckxwa-uc.a.run.app
==> Sending 10% of traffic to v2

Traffic split:
REVISION                   LATEST  TAG     PERCENT
hello-cloud-run-00001-riw          rev-v1  90
hello-cloud-run-00002-wum          rev-v2  10
```
Check the split:
```bash
bash scripts/call.sh 50
```
```
     42 "version":"v1"
      8 "version":"v2"
```
Roughly 10% of requests reach v2. The split is random per request, so small samples vary. The `rev-v2` URL always reaches v2, so v2 can be tested directly:
```json
{"message":"Hello from v2!","revision":"hello-cloud-run-00002-wum","version":"v2"}
```

### Step 5: Roll back, then promote
Suppose the canary looked bad. Send all traffic back to v1, instantly, with no rebuild:
```bash
bash scripts/traffic.sh rollback v1
bash scripts/call.sh 20
```
```
REVISION                   LATEST  TAG     PERCENT
hello-cloud-run-00001-riw          rev-v1  100
hello-cloud-run-00002-wum          rev-v2
     20 "version":"v1"
```
Once v2 is judged good, promote it to 100%:
```bash
bash scripts/traffic.sh promote v2
bash scripts/call.sh 20
```
```
REVISION                   LATEST  TAG     PERCENT
hello-cloud-run-00001-riw          rev-v1
hello-cloud-run-00002-wum          rev-v2  100
     20 "version":"v2"
```
Other commands: `bash scripts/traffic.sh status` shows the current split, and `bash scripts/traffic.sh split v2 50` sets any percentage.

### Step 6: Monitor (Cloud Console)
In the [Cloud Run console](https://console.cloud.google.com/run), open `hello-cloud-run`:
- **Metrics:** request count, latency, container instance count (it drops to 0 when idle), CPU and memory use.
- **Revisions:** each version, its traffic share, and its scaling and environment settings.
- **Logs:** gunicorn's startup and request logs, sent straight to Cloud Logging.

### Optional: run the tests locally
```bash
python -m venv .venv
source .venv/bin/activate        # Windows Git Bash: source .venv/Scripts/activate
pip install -r requirements-dev.txt
pytest -v tests
```
Expected: `4 passed`.

---

## Cleaning up
```bash
bash scripts/cleanup.sh          # asks for confirmation; add --yes to skip it
```
This deletes the Cloud Run service, the `cloud-run-lab` repository with all its images, and the source archives in `gs://<project>_cloudbuild/source/`. To remove everything, including the enabled APIs, delete the whole project in the Console under **IAM & Admin → Settings → Shut down**.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ERROR: set PROJECT_ID in config.env first` | Edit `config.env`, or run `export PROJECT_ID=...` (step 3 of Setup). |
| `PERMISSION_DENIED: The caller does not have permission` on the **first** `build.sh` | The Cloud Build API was just enabled and needs a minute to activate. Wait and re-run. |
| `gcloud: command not found` right after installing | Open a new terminal so it picks up the updated `PATH`. |
| `$'\r': command not found` when running a script | The script has Windows line endings. Run `git checkout -- scripts/` (`.gitattributes` restores LF), or `sed -i 's/\r$//' scripts/*.sh`. |
| `403 Forbidden` when opening the URL | Your organization blocks public (`allUsers`) access. `scripts/call.sh` still works because it sends your identity token. In a browser, use `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <URL>`. |
| `tag: must be at least 3 characters long` | Cloud Run's tag rule. The scripts already handle it by turning `v1` into `rev-v1`. Pass plain versions like `v1`. |

---

## Acknowledgements
Based on the [Cloud Run beginner lab](https://github.com/raminmohammadi/MLOps/tree/main/Labs/GCP_Labs/Cloud_Runner_Labs/Begineer_Lab) from the IE 7374 course repository. Implementation and README written with assistance from Claude Code (Anthropic).
