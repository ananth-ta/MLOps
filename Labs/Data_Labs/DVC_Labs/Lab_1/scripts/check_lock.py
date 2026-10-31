"""Fail if dvc.lock is out of date with the committed code or params.

Used in CI, where the (private) data is not available. `dvc status` there reports the data and
pipeline outputs as deleted, which is expected and ignored. What must NOT appear is a *modified*
code file, param or stage command: that means someone changed the pipeline and committed without
running `dvc repro`, so the committed metrics don't belong to the committed code.

Usage: python scripts/check_lock.py
"""
import json
import subprocess
import sys

IGNORED = {"deleted", "not in cache"}


def problems_from_status(status):
    problems = []
    for stage, changes in status.items():
        for change in changes:
            if isinstance(change, str):  # e.g. "changed command", "always changed"
                problems.append(f"{stage}: {change}")
                continue
            for kind, entries in change.items():
                for path, state in entries.items():
                    if isinstance(state, dict):  # params.yaml: {param: state}
                        problems += [f"{stage}: {kind} {path}:{p} {s}" for p, s in state.items()]
                    elif state not in IGNORED:
                        problems.append(f"{stage}: {kind} {path} {state}")
    return problems


def main():
    result = subprocess.run(["dvc", "status", "--json"], capture_output=True, text=True, check=True)
    problems = problems_from_status(json.loads(result.stdout or "{}"))
    if problems:
        print("dvc.lock is out of date with the committed code/params (run `dvc repro` and commit):")
        print("  " + "\n  ".join(problems))
        sys.exit(1)
    print("dvc.lock matches the committed code and params (data/outputs are not checked here)")


if __name__ == "__main__":
    main()
