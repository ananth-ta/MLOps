# DVC Lab: Versioned Data and a Reproducible Pipeline on Google Cloud Storage

This lab uses **DVC (Data Version Control)** to version a dataset and the results built from it. The original lab is kept in [instructions.md](instructions.md). It tracks one CSV with `dvc add`, pushes it to a Cloud Storage bucket using a downloaded service-account key, and explains how to roll back.

This version extends it into a complete data-versioning workflow:

- **Two real versions of the dataset** (v1 and v2), each tied to a Git tag, with `dvc diff`, rollback, and recovery from cloud storage demonstrated.
- **A reproducible pipeline** (`dvc.yaml`): prepare → train → evaluate, with parameters (`params.yaml`), tracked metrics and plots. `dvc repro` reruns only what changed.
- **Experiments** (`dvc exp run`) comparing model and preprocessing choices side by side.
- **A private Cloud Storage remote with no key files**, authenticated with your own Google login.
- **CI** that checks the committed results belong to the committed code, and that the pipeline runs on Linux.

The dataset is the [Credit Card Dataset for Clustering](https://www.kaggle.com/datasets/arjunbhasin2013/ccdata) (Kaggle, CC0 public domain): 8,950 credit-card customers described by 17 behaviour columns, with no labels. The pipeline groups customers into segments with **KMeans clustering**.

---

## Contents
- [What changed from the original lab](#what-changed-from-the-original-lab)
- [How it fits together](#how-it-fits-together)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the lab](#running-the-lab)
- [Continuous integration](#continuous-integration)
- [Known issues: DVC on Windows](#known-issues-dvc-on-windows)
- [Troubleshooting](#troubleshooting)

---

## What changed from the original lab

### Problems fixed in the original

| Problem in the original | Fix |
|---|---|
| The data file, DVC's cache (`.dvc/cache/`) and its lock files (`.dvc/tmp/`) were **committed to Git**, even though DVC's own `.gitignore` files exclude them. The point of DVC is that data does *not* go into Git. | Removed them from Git. Git now holds only small pointer files; the data lives in the bucket. |
| The pointer file didn't match the data: `data.txt.dvc` recorded a 28-byte file, the file was 29 bytes, and the cache held a third version. | Every version is now created with `dvc add` / `dvc repro`, so pointers and data always agree. |
| `.dvc/config` pointed at the instructor's bucket and a key file at `/home/ramin/...`, so it failed for everyone else. | The remote is created by [scripts/setup_remote.sh](scripts/setup_remote.sh) in **your** project. No local paths are committed. |
| A downloaded service-account key with **Owner** rights. A leaked key gives full control of the project. | Uses **Application Default Credentials** (`gcloud auth application-default login`): DVC uses your own Google login, and no key file exists. |
| `requirements.txt` pinned 200 packages including Airflow 2.7.1 and numpy 1.26, which **don't install on Python 3.13**, and it lacked `dvc-gs`, which Cloud Storage remotes need. | Five pinned packages: `dvc[gs]` 3.67.1, `kagglehub`, `pandas`, `scikit-learn`, `pyyaml`. |
| README errors: `dvc remote modify --lab2 credentialpath` is not valid syntax; the dataset needs a manual Kaggle download. | Exact, tested commands; the download is scripted ([scripts/fetch_data.py](scripts/fetch_data.py)). |
| Pipelines, params, metrics and experiments appear in the command cheat sheet but are never used. | All of them are used below. |

### Added
1. **Data versions v1 and v2.** The dataset is one Kaggle export. `fetch_data.py --rows 4500` writes only the first 4,500 customers (v1, "an earlier export"); without `--rows` it writes all 8,950 (v2, "after new customers arrived"). Rows are copied **byte for byte**, so anyone who downloads the data gets files with *exactly* the hashes committed here.
2. **Pipeline** ([dvc.yaml](dvc.yaml)):
   - `prepare`: checks the columns (a malformed new data version fails loudly), drops the ID, fills the two columns with gaps using the median, log-transforms the skewed money and count columns, and scales.
   - `train`: KMeans.
   - `evaluate`: silhouette score (higher is better), Davies–Bouldin index (lower is better), inertia, customers per cluster, and an elbow curve over k = 2…10.
3. **Parameters** in [params.yaml](params.yaml): number of clusters, scaler, log transform, elbow range. DVC records which values produced which results.
4. **Experiments** with `dvc exp run -S …`, compared with `dvc exp show`.
5. **Cross-platform hashing.** DVC hashes files byte for byte, so `.gitattributes` forces Unix line endings and every output is written with fixed line endings and number formats. The same inputs give the same hashes on Windows and Linux.
6. **CI** ([lab3_dvc.yml](../../../../.github/workflows/lab3_dvc.yml)): see [Continuous integration](#continuous-integration).
7. **Tests** ([tests/test_pipeline.py](tests/test_pipeline.py)): 20 tests on synthetic data, needing no account.

---

## How it fits together

```
 Kaggle ──fetch_data.py──▶ data/raw/CC_GENERAL.csv ──┐   (data: in the bucket, NOT in Git)
                                                      │
 Git tracks:                                          ▼
   data/raw/CC_GENERAL.csv.dvc   ◀── dvc add ──  md5 + size of the data file
   dvc.yaml  params.yaml  src/   ── dvc repro ─▶ prepare ─▶ train ─▶ evaluate
   dvc.lock                      ◀── records the md5 of every input and output of each stage
   metrics/*.yaml, *.csv         ◀── small results, kept in Git so they can be diffed

 dvc push / dvc pull  ◀──▶  gs://<project>-dvc-lab   (private bucket; your Google login)
```

A Git commit therefore pins **code + parameters + exact data version + results** together. Checking out an old commit and running `dvc checkout` brings back the matching data and outputs.

---

## Project structure
```
Lab_1/
├── data/
│   ├── raw/CC_GENERAL.csv.dvc     # pointer to the raw data (the CSV itself is in the bucket)
│   └── processed/                 # features.csv (pipeline output, in the bucket)
├── models/                        # kmeans.pkl (pipeline output, in the bucket)
├── metrics/
│   ├── metrics.yaml               # silhouette, Davies-Bouldin, inertia, n_customers, n_clusters
│   ├── elbow.csv                  # plot data: inertia for k = 2..10
│   └── cluster_sizes.csv          # plot data: customers per cluster
├── src/
│   ├── common.py                  # paths and shared helpers
│   ├── prepare.py                 # stage 1
│   ├── train.py                   # stage 2
│   └── evaluate.py                # stage 3
├── scripts/
│   ├── fetch_data.py              # download from Kaggle (--rows N for an earlier snapshot)
│   ├── setup_remote.sh            # create the bucket and DVC remote
│   ├── compare_metrics.py         # compare two metrics files within a tolerance
│   ├── check_lock.py              # CI: dvc.lock must match the committed code and params
│   └── make_synthetic_data.py     # CI: random data with the real columns
├── tests/test_pipeline.py
├── dvc.yaml                       # the pipeline
├── dvc.lock                       # exact hashes from the last run (written by DVC)
├── params.yaml
├── requirements.txt
├── .dvc/config                    # DVC settings and the remote
├── .gitignore  .gitattributes
├── instructions.md                # the original lab
└── README.md
```

---

## Prerequisites

| Requirement | Version used | Notes |
|---|---|---|
| Python | 3.13 (3.11+ works) | [python.org/downloads](https://www.python.org/downloads/). On Windows, tick **"Add python.exe to PATH"**. |
| Git | any recent | [git-scm.com](https://git-scm.com/downloads). On Windows this also installs **Git Bash**, used for the shell script. |
| Google Cloud SDK (`gcloud`) | 589.0.0 | [Install guide](https://cloud.google.com/sdk/docs/install). Windows: `winget install --id Google.CloudSDK`. |
| Google Cloud project with billing | — | Free-trial or education credits are fine. Storage for this lab costs well under $0.01/month. |
| Kaggle account | — | Free, at [kaggle.com](https://www.kaggle.com). Used once to download the data. |
| DVC and Python packages | `dvc[gs]` 3.67.1 etc. | Installed from `requirements.txt` below. |
| **Windows only:** WSL (Ubuntu) | Ubuntu 24.04, Python 3.12 | Needed for the commands that compare versions and for experiments. See [Known issues](#known-issues-dvc-on-windows). macOS and Linux don't need it. |

---

## Setup

All commands run in **Git Bash** (Windows) or a terminal (macOS/Linux), starting from the lab folder.

### 1. Get the code
```bash
git clone https://github.com/ananth-ta/MLOps.git
cd MLOps/Labs/Data_Labs/DVC_Labs/Lab_1
```

### 2. Python environment
```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows (Git Bash)
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt pytest
dvc --version                     # 3.67.1
pytest -q tests                   # 20 passed
```

### 3. Kaggle token
On [kaggle.com/settings](https://www.kaggle.com/settings), under **API**, create a token and copy the token string. Save it as a file **outside the repository**, so it can never be committed:
```bash
mkdir -p ~/.kaggle
# Paste the token as the only content of this file:
notepad ~/.kaggle/access_token     # Windows (Notepad may name it access_token.txt, which also works)
# nano ~/.kaggle/access_token      # macOS / Linux
```
Alternatively, set the token as the `KAGGLE_API_TOKEN` environment variable. Older `~/.kaggle/kaggle.json` credentials also work.

### 4. Google login for DVC
```bash
gcloud auth login                       # for gcloud commands
gcloud auth application-default login   # for DVC: lets it use your Google identity, no key file
gcloud projects list                    # note your PROJECT_ID
```

### 5. Create the bucket and DVC remote
```bash
export PROJECT_ID=your-project-id
bash scripts/setup_remote.sh
```
Expected output:
```
==> Enabling the Cloud Storage API in mlops-lab-512020
==> Creating bucket gs://mlops-lab-512020-dvc-lab in us-east1
Creating gs://mlops-lab-512020-dvc-lab/...
==> Configuring DVC remote 'gcs' (default)
Setting 'gcs' as a default remote.

gcs     gs://mlops-lab-512020-dvc-lab   (default)
==> Done. Push/pull with: dvc push / dvc pull   (private bucket: needs access to mlops-lab-512020)
```
The bucket is **private**: only accounts with access to your project can read it. This rewrites the `gcs` remote in `.dvc/config` to point at your bucket.

---

## Running the lab

The output shown is from an actual run.

### Step 1: Data version v1 (4,500 customers)
```bash
python scripts/fetch_data.py --rows 4500
dvc add data/raw/CC_GENERAL.csv
```
```
Wrote 4500 customers to data\raw\CC_GENERAL.csv
To track the changes with git, run:
	git add 'data\raw\.gitignore' 'data\raw\CC_GENERAL.csv.dvc'
```
`dvc add` moves the file into DVC's cache, lists it in `data/raw/.gitignore` so Git ignores it, and writes the pointer file `CC_GENERAL.csv.dvc`:
```yaml
outs:
- md5: 046c43e101182a529f90d7723641f00f
  size: 458859
  hash: md5
  path: CC_GENERAL.csv
```
Because `fetch_data.py` copies the rows byte for byte, your v1 file has this **same md5**. DVC recognises it as the exact v1 committed here.

### Step 2: Run the pipeline
```bash
dvc repro
```
```
Running stage 'prepare':
> python src/prepare.py
prepare: 4500 customers, 151 missing values imputed, scaler=standard, log_transform=True -> features.csv
Running stage 'train':
> python src/train.py
train: KMeans k=4 on 4500 customers, inertia=43491.6 -> kmeans.pkl
Running stage 'evaluate':
> python src/evaluate.py
evaluate: n_customers=4500, n_clusters=4, inertia=43491.64, silhouette=0.2145, davies_bouldin=1.6634
```
Run it again, and nothing reruns, because no input changed:
```
'data\raw\CC_GENERAL.csv.dvc' didn't change, skipping
Stage 'prepare' didn't change, skipping
Stage 'train' didn't change, skipping
Stage 'evaluate' didn't change, skipping
Data and pipelines are up to date.
```
`dvc dag` draws the pipeline:
```
+-----------------------------+
| data\raw\CC_GENERAL.csv.dvc |
+-----------------------------+
                *
                *
                *
          +---------+
          | prepare |
          +---------+
          **        **
        **            *
       *               **
 +-------+               *
 | train |             **
 +-------+            *
          **        **
            **    **
              *  *
          +----------+
          | evaluate |
          +----------+
```

### Step 3: Push to the bucket and commit v1
```bash
dvc push                      # 3 files pushed  (raw data, features, model)
git add .
git commit -m "Data version v1 (4,500 customers)"
git tag lab3-data-v1
```
`dvc push` uploads the data and outputs. The commit holds only code, pointers, `dvc.lock` and the small metric files.

### Step 4: Data version v2 (all 8,950 customers)
```bash
python scripts/fetch_data.py
dvc status
```
DVC notices the data changed and the pipeline is now out of date:
```
prepare:
	changed deps:
		modified:           data\raw\CC_GENERAL.csv
data\raw\CC_GENERAL.csv.dvc:
	changed outs:
		modified:           data\raw\CC_GENERAL.csv
```
```bash
dvc add data/raw/CC_GENERAL.csv
dvc repro
dvc push
git add .
git commit -m "Data version v2 (full 8,950 customers)"
git tag lab3-data-v2
```
```
prepare: 8950 customers, 314 missing values imputed, scaler=standard, log_transform=True -> features.csv
train: KMeans k=4 on 8950 customers, inertia=86547.0 -> kmeans.pkl
evaluate: n_customers=8950, n_clusters=4, inertia=86547.01, silhouette=0.2166, davies_bouldin=1.6876
```

### Step 5: Compare the versions
> **Windows:** run these in WSL. See [Known issues](#known-issues-dvc-on-windows).

```bash
dvc diff lab3-data-v1
```
```
Modified:
    data/processed/features.csv
    data/raw/CC_GENERAL.csv
    models/kmeans.pkl

files summary: 3 modified
```
```bash
dvc metrics diff lab3-data-v1
```
```
Path                  Metric          lab3-data-v1    workspace    Change
metrics/metrics.yaml  davies_bouldin  1.6634          1.6876       0.0242
metrics/metrics.yaml  inertia         43491.64        86547.01     43055.37
metrics/metrics.yaml  n_customers     4500            8950         4450
metrics/metrics.yaml  silhouette      0.2145          0.2166       0.0021
```
`dvc params diff lab3-data-v1` prints nothing: only the data changed between the versions, not the parameters. Inertia roughly doubles because it's a sum over customers. The quality scores barely move, so the four segments found in the earlier export still hold with twice the customers.

### Step 6: Roll back to v1, and return
Restore v1's pointer, lock and metrics from its tag, then let DVC restore the matching data and outputs from its cache:
```bash
git checkout lab3-data-v1 -- data/raw/CC_GENERAL.csv.dvc dvc.lock metrics
dvc checkout
```
```
M       data\processed\features.csv
M       data\raw\CC_GENERAL.csv
M       models\kmeans.pkl
```
```bash
wc -l < data/raw/CC_GENERAL.csv     # 4501   (header + 4,500 customers)
dvc status                          # Data and pipelines are up to date.
```
Data, model and metrics are back to v1 in seconds, with nothing rerun. To return to v2, do the same with `lab3-data-v2`. Restoring only these files, rather than checking out the whole commit, rolls back this lab without touching the rest of the repository.

### Step 7: Recover everything from the bucket
Simulate a lost laptop: delete the data, the outputs **and** DVC's local cache, then pull:
```bash
rm -rf .dvc/cache data/raw/CC_GENERAL.csv data/processed/features.csv models/kmeans.pkl
dvc pull
```
```
A       data\processed\features.csv
A       data\raw\CC_GENERAL.csv
A       models\kmeans.pkl
3 files fetched and 3 files added
```
`dvc status` reports `Data and pipelines are up to date.` The older version is in the bucket too. With the cache wiped, `git checkout lab3-data-v1 -- data/raw/CC_GENERAL.csv.dvc dvc.lock metrics && dvc pull` downloads v1 (`3 files fetched`, 4,500 customers).

### Step 8: Experiments
> **Windows:** `dvc exp run` fails on Windows. Run it in WSL. See [Known issues](#known-issues-dvc-on-windows).

Each experiment overrides one or more parameters, runs the whole pipeline, and records the result without a commit. **Restore `params.yaml` between experiments**: `-S` leaves the changed value in `params.yaml`, so the next experiment would otherwise build on it.
```bash
dvc exp run -n k3 -S train.n_clusters=3
git checkout HEAD -- params.yaml dvc.lock metrics && dvc checkout
dvc exp run -n k5 -S train.n_clusters=5
# ... and so on for each experiment
dvc exp show --only-changed
```
Results on all 8,950 customers. Each experiment changes **one** thing from the baseline (`main`):

| Experiment           | n_clusters | inertia | silhouette ↑ | davies_bouldin ↓ | prepare.log_transform | prepare.scaler | train.n_clusters |
|----------------------|------------|---------|--------------|------------------|-----------------------|----------------|------------------|
| main (baseline)      | 4          | 86547   | 0.2166       | 1.6876           | True                  | standard       | 4                |
| ├── [no-log]         | 4          | 99062   | 0.1977       | 1.5748           | **False**             | standard       | 4                |
| ├── [minmax]         | 4          | 4848.2  | 0.2637       | 1.4729           | True                  | **minmax**     | 4                |
| ├── [robust]         | 4          | 75110   | 0.2581       | **1.3137**       | True                  | **robust**     | 4                |
| ├── [k6]             | 6          | 71656   | 0.2172       | 1.466            | True                  | standard       | **6**            |
| ├── [k5]             | 5          | 77933   | 0.2183       | 1.6011           | True                  | standard       | **5**            |
| └── [k3]             | 3          | 95645   | 0.2245       | 1.6809           | True                  | standard       | **3**            |

What it shows:
- **The log transform matters.** Without it, silhouette drops from 0.2166 to 0.1977: a few customers with huge balances dominate the distances.
- **The scaler matters more than k.** Min–max and robust scaling give the best scores (silhouette 0.26, Davies–Bouldin down to 1.31). Inertia can't be compared across scalers, because each scaler puts the features on a different scale; min–max squeezes them into 0–1.
- **The two quality scores disagree on k.** k = 3 has the best silhouette (how well each customer fits its own cluster); k = 6 has the best Davies–Bouldin (how well separated the clusters are). Neither k is clearly better, so the baseline keeps k = 4.

Experiments are stored as hidden Git references, not commits on your branch. `dvc exp apply <name>` would make one the working version. Here the baseline stays at **k = 4**.

### Step 9: Plots (optional)
```bash
dvc plots show       # writes dvc_plots/index.html: the elbow curve and cluster sizes
```

---

## Continuous integration

[`.github/workflows/lab3_dvc.yml`](../../../../.github/workflows/lab3_dvc.yml) runs on every push or pull request that touches this lab. The data is in a **private** bucket, so CI never downloads it. It checks:

1. **Unit tests pass.**
2. **`dvc.lock` matches the committed code and parameters** ([scripts/check_lock.py](scripts/check_lock.py)). If someone edits `src/` or `params.yaml` and commits without running `dvc repro`, the committed metrics no longer belong to the committed code, and this check fails. The missing private data is expected and ignored.
3. **The full pipeline runs on Linux**, using 500 rows of synthetic data with the real columns ([scripts/make_synthetic_data.py](scripts/make_synthetic_data.py)).

Run locally, the same checks give:
```
$ python scripts/check_lock.py          # with the data and outputs deleted, as in CI
dvc.lock matches the committed code and params (data/outputs are not checked here)

$ python scripts/check_lock.py          # after changing train.n_clusters without dvc repro
dvc.lock is out of date with the committed code/params (run `dvc repro` and commit):
  train: changed deps params.yaml:train modified

$ python scripts/make_synthetic_data.py --rows 500 && dvc repro --force
Wrote 500 synthetic customers to data/raw/CC_GENERAL.csv
prepare: 500 customers, 16 missing values imputed, scaler=standard, log_transform=True -> features.csv
train: KMeans k=4 on 500 customers, inertia=7503.5 -> kmeans.pkl
evaluate: n_customers=500, n_clusters=4, inertia=7503.49, silhouette=0.0465, davies_bouldin=3.4083
```
The synthetic data is random, so its scores mean nothing; the point is that every stage runs. Don't run the smoke test in a working copy you care about, because it overwrites the data. To undo it: `git checkout HEAD -- data/raw/CC_GENERAL.csv.dvc dvc.lock metrics && dvc checkout`.

To check that the committed metrics reproduce from the real data, run this locally with access to the bucket:
```bash
dvc pull
cp metrics/metrics.yaml /tmp/committed.yaml
dvc repro --force
python scripts/compare_metrics.py /tmp/committed.yaml metrics/metrics.yaml
```

---

## Known issues: DVC on Windows

Found while building this lab, with DVC 3.67.1 (the latest release) on Windows 11:

1. **Comparing versions silently returns nothing.** For a DVC project inside a **subfolder** of a Git repository, as here, DVC builds the project's path inside old commits with Windows backslashes (`/Labs\Data_Labs\...`). Git paths always use `/`, so DVC decides old commits contain no DVC project and **skips them without an error**. `dvc diff` prints nothing; `dvc metrics diff`, `params diff` and `plots diff` show `-` for the old version; `dvc exp show` shows `-` for the baseline. The cause is in `dvc/repo/brancher.py` (`_switch_fs`).
2. **`dvc exp run` fails** with `[WinError 5] Access is denied: '...\.dvc\tmp'`.

Everything else works on Windows: `add`, `repro`, `status`, `push`, `pull`, `checkout`.

**Workaround:** run the comparison and experiment commands in **WSL** (Windows Subsystem for Linux), on the same folder:
```bash
# in WSL (Ubuntu), from the lab folder under /mnt/c/...
python3 -m venv .venv-wsl
.venv-wsl/bin/pip install -r requirements.txt     # slow on /mnt/c (~10+ min); only needed once
export PATH="$PWD/.venv-wsl/bin:$PATH"
dvc metrics diff lab3-data-v1
```
WSL's Git doesn't read Git for Windows' system-wide `core.autocrlf` setting, so it sees every file as modified, and DVC would include those false changes in experiments. Fix it once per repository: `git config --local core.autocrlf true`.

WSL also sees every file on the Windows drive as executable, so DVC may add `isexec: true` to `data/raw/CC_GENERAL.csv.dvc`. It isn't a real change; discard it with `git checkout -- data/raw/CC_GENERAL.csv.dvc`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `fetch_data.py`: 401 / unauthorized | The Kaggle token is missing or wrong: check `~/.kaggle/access_token` (or `.txt`), or set `KAGGLE_API_TOKEN`. |
| `dvc push` / `dvc pull` fails with a credentials or "anonymous caller" error | DVC has no Google login: run `gcloud auth application-default login`. |
| `dvc pull`: 403 / access denied | The bucket is private, so you need access to that project. Create your own with `scripts/setup_remote.sh` and push your own data. |
| `dvc status` reports code files `modified` right after cloning on Windows | They were checked out with Windows line endings, which changes their hashes. The lab's `.gitattributes` prevents this. If it still happens (e.g. the clone predates it), re-checkout the lab's files: `git checkout -- .` from the lab folder. **This discards uncommitted edits there**, so commit or `git stash` them first. |
| A `.dvc` file doesn't show in `git status` | The fork's root `.gitignore` ignores `*.dvc`. The lab's `.gitignore` overrides it with `!*.dvc`; don't remove that line. |
| `dvc diff` prints nothing on Windows | See [Known issues](#known-issues-dvc-on-windows). |

---

## Acknowledgements
Based on the [DVC lab](https://github.com/raminmohammadi/MLOps/tree/main/Labs/Data_Labs/DVC_Labs/Lab_1) from the IE 7374 course repository. Dataset: [Credit Card Dataset for Clustering](https://www.kaggle.com/datasets/arjunbhasin2013/ccdata) by Arjun Bhasin (CC0). Implementation and README written with assistance from Claude Code (Anthropic).
