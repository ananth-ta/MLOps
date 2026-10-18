# Lab 1 - GitHub Actions (Testing with Pytest & Unittest)

Based on [Labs/Github_Labs/Lab1](https://github.com/raminmohammadi/MLOps/tree/main/Labs/Github_Labs/Lab1) from the course repo. The original lab instructions are kept in [instructions.md](instructions.md).

> This lab was first completed and graded in [ananth-ta/IE7374-MLOps-Labs](https://github.com/ananth-ta/IE7374-MLOps-Labs/tree/main/Lab1), commit `ad4354c`, and moved here unchanged apart from paths, CI location and this README.

## Overview
A small calculator module tested with both **pytest** and **unittest**, with two GitHub Actions workflows that run each test suite automatically on every push or pull request to `main` that touches this lab.

## Changes from the reference

### Calculator (`src/calculator.py`)
- **Descriptive names:** `fun1`–`fun4` renamed to `add`, `subtract`, `multiply`, `add_three`.
- **New functions:** `divide`, `power`, `modulo`, `average`.
- **Shared validation:** the input check repeated in every function is replaced by two helpers: `is_num` (checks one value) and `val_num` (raises `ValueError` if any input is invalid).
- **Stricter input checks:**
  - Booleans are rejected. In the reference, `fun1(True, 2)` returned `3` because `bool` is a subclass of `int` in Python.
  - NaN and ±infinity are rejected.
  - `add_three` (the reference `fun4`) had no input validation at all; it now does.
- **Edge cases handled:**
  - `divide` / `modulo` by zero (including `0.0` and `-0.0`)
  - `power(0, -1)` (zero to a negative power)
  - `power(-8, 1/3)`, which in plain Python silently returns a **complex number**
  - `power(10.0, 400)` overflow
- **One exception type:** every invalid operation raises `ValueError` with a descriptive message, instead of a mix of `ValueError`, `ZeroDivisionError` and `OverflowError`.

### Tests
- **pytest (`test/test_pytest.py`):**
  - `@pytest.mark.parametrize` replaces the repeated `assert` lines.
  - Stacked `parametrize` decorators test every function against every invalid input, in every argument position.
  - `pytest.raises(..., match=...)` checks both the exception type and its message.
  - `pytest.approx` compares float results.
- **unittest (`test/test_unittest.py`):**
  - Covers the same cases, split into one `TestCase` class per area.
  - `subTest` plays the role of `parametrize`, and `setUp` shares the invalid-input data.
  - `assertRaisesRegex` checks exception messages; `assertAlmostEqual` compares floats.
- **Verified the tests catch bugs:** changing `add` to return `x - y` made both suites fail; reverting it made them pass again.

### CI (`.github/workflows/`)
The reference workflows would not run as-is, so they were fixed:
- **Location:** the copies in `Lab1/workflows/` never ran, because GitHub only runs workflows from `.github/workflows/` at the repo root. They're replaced by `lab1_pytest.yml` and `lab1_unittest.yml` there. Those also replace the reference's root workflows `github_lab1_pytest_action.yml` and `github_lab2_unittest_action.yml`, which ran on every push to the repo but not from this folder.
- **Triggers:** run only when `Labs/Github_Labs/Lab1/` changes (`paths` filter), and from that directory (`working-directory`), so other labs in this repo don't set them off.
- **Versions:** upgraded to `actions/checkout@v4`, `actions/setup-python@v5` and `actions/upload-artifact@v4` (v2 of upload-artifact has been retired and fails), and to Python 3.13 (3.8 is end-of-life).
- **Invalid YAML removed:** the `run-nam` typo, a conflicting `branches` / `branches-ignore` pair, and the `label` / `issues` triggers.
- **Manual runs:** added `workflow_dispatch` and `pull_request` triggers.

## Project Structure
```
Lab1/
├── data/
├── src/
│   └── calculator.py
├── test/
│   ├── test_pytest.py
│   └── test_unittest.py
├── instructions.md
├── README.md
└── requirements.txt
```
Workflows live at the repo root in `.github/workflows/` (`lab1_pytest.yml`, `lab1_unittest.yml`), since GitHub only runs workflows from there.

## Prerequisites
| Requirement | Version used | Notes |
|---|---|---|
| Python | 3.13 (any 3.9+ works) | [python.org/downloads](https://www.python.org/downloads/). On Windows, tick **"Add python.exe to PATH"** in the installer. |
| Git | any recent version | [git-scm.com](https://git-scm.com/downloads) |
| pytest | 9.x | Installed from `requirements.txt` in the steps below. |

Check them: `python --version` and `git --version`.

## Running Locally
```bash
git clone https://github.com/ananth-ta/MLOps.git
cd MLOps/Labs/Github_Labs/Lab1

python -m venv .venv
# Windows (PowerShell / cmd):  .venv\Scripts\activate
# macOS / Linux / Git Bash:    source .venv/bin/activate   (Git Bash: source .venv/Scripts/activate)

pip install -r requirements.txt
pytest -v
python -m unittest -v test.test_unittest
```

### What a successful run looks like
`pytest -v` runs both test files (pytest also collects the unittest classes) and ends with:
```
============ 141 passed, 198 subtests passed in 0.37s ============
```
`python -m unittest -v test.test_unittest` ends with:
```
Ran 18 tests in 0.003s

OK
```
Any failure is listed by test name and input. For example, after deliberately breaking `add`, pytest reports `FAILED test/test_pytest.py::test_add[2-3-5]`.

## CI Results
[![Lab 1 - Testing with Pytest](https://github.com/ananth-ta/MLOps/actions/workflows/lab1_pytest.yml/badge.svg)](https://github.com/ananth-ta/MLOps/actions/workflows/lab1_pytest.yml)
[![Lab 1 - Python Unittests](https://github.com/ananth-ta/MLOps/actions/workflows/lab1_unittest.yml/badge.svg)](https://github.com/ananth-ta/MLOps/actions/workflows/lab1_unittest.yml)

Both workflows run on every push or pull request to `main` that touches `Labs/Github_Labs/Lab1/`, and can be started by hand from the Actions tab (**Run workflow**). The pytest workflow also uploads a JUnit XML report (`lab1-pytest-results`) as a build artifact, viewable on each run's summary page.

## Acknowledgements
Edge-case review, refactoring and test expansion assisted by Claude Code (Anthropic).
