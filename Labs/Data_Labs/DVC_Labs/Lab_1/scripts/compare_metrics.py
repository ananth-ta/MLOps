"""Compare two metrics.yaml files, allowing a small tolerance for floating-point noise.

CI uses this after re-running the pipeline: the result must match the committed metrics.
KMeans on different CPUs/BLAS libraries can differ in the last decimal places, so exact
equality would be too strict, while a real change (different data, params or code) is far
larger than the tolerance.

Usage: python scripts/compare_metrics.py <expected.yaml> <actual.yaml> [--rel-tol 0.001]
"""
import argparse
import math
import sys

import yaml


def compare(expected, actual, rel_tol):
    problems = []
    for key in sorted(set(expected) | set(actual)):
        if key not in expected or key not in actual:
            problems.append(f"{key}: present in only one file")
        elif not math.isclose(expected[key], actual[key], rel_tol=rel_tol, abs_tol=1e-4):
            problems.append(f"{key}: expected {expected[key]}, got {actual[key]}")
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("expected")
    parser.add_argument("actual")
    parser.add_argument("--rel-tol", type=float, default=1e-3)
    args = parser.parse_args()

    with open(args.expected) as f:
        expected = yaml.safe_load(f)
    with open(args.actual) as f:
        actual = yaml.safe_load(f)

    problems = compare(expected, actual, args.rel_tol)
    if problems:
        print("Metrics do NOT reproduce:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print(f"Metrics reproduce within rel_tol={args.rel_tol}: " +
          ", ".join(f"{k}={v}" for k, v in actual.items()))


if __name__ == "__main__":
    main()
