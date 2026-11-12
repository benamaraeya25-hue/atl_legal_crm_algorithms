"""Experiment 1: sort passages chronologically.

Items are packed (decision date, case, passage) integer keys from the real corpus.
Three input orders: random (average case), already sorted, reverse sorted.
Writes results/sorting_results.csv.
"""
import random

from common import SIZES, corpus, summary, timed, write_csv, write_environment
from caselaw.sorting import REFERENCE_SORTER, SORTERS

QUADRATIC_SKIP_AT = 100_000          # skip quadratic combinations from this size up
SLOW = {                             # (algorithm, scenario) pairs that are quadratic
    ("Insertion Sort", "random"), ("Insertion Sort", "reversed"),
    ("Quick Sort (first pivot)", "sorted"), ("Quick Sort (first pivot)", "reversed"),
}


def main():
    write_environment()
    keys_all = corpus().keys
    algorithms = dict(SORTERS)
    algorithms[REFERENCE_SORTER[0]] = REFERENCE_SORTER[1]
    rows = []
    for n in SIZES:
        keys = keys_all[:n]
        scenarios = {"random": keys, "sorted": sorted(keys), "reversed": sorted(keys, reverse=True)}
        expected = sorted(keys)
        for scen, data_in in scenarios.items():
            for name, fn in algorithms.items():
                row = dict(algorithm=name, n=n, scenario=scen)
                if (name, scen) in SLOW and n >= QUADRATIC_SKIP_AT:
                    row.update(status="skipped (quadratic)", repeats=0, min_s="", median_s="", max_s="")
                    rows.append(row)
                    print(f"n={n:>8} {scen:<8} {name:<28} skipped", flush=True)
                    continue
                if n == 1_000:
                    repeats = 5
                elif (name, scen) in SLOW and n == 10_000:
                    repeats = 1
                elif name == "Heap Sort" and n == 1_000_000:
                    repeats = 1
                else:
                    repeats = 3
                times = []
                for _ in range(repeats):
                    random.seed(12345)
                    t, out = timed(fn, data_in)
                    times.append(t)
                assert out == expected, f"{name} gave a wrong answer"
                lo, med, hi = summary(times)
                row.update(status="ok", repeats=repeats, min_s=f"{lo:.6f}",
                           median_s=f"{med:.6f}", max_s=f"{hi:.6f}")
                rows.append(row)
                print(f"n={n:>8} {scen:<8} {name:<28} {med:10.4f}s  (x{repeats})", flush=True)
    write_csv("sorting_results.csv", rows)


if __name__ == "__main__":
    main()
