"""Experiment 2: look up one passage by its pinpoint key.

Searches run on the sorted key list (binary search needs it; linear search is the same
on any order). Best case = first item (linear, hash) or middle item (binary).
Worst case = key not present. Average case = 200 random existing keys.
Writes results/lookup_results.csv (microseconds per search).
"""
import random
import statistics
import time

from common import SIZES, corpus, timed, write_csv
from caselaw.lookup import HashTable, binary_search, build_hash_table, linear_search


def per_search_us(fn, targets, reps):
    """Mean microseconds per call over reps passes through targets; median of 3 runs."""
    runs = []
    for _ in range(3):
        t0 = time.perf_counter()
        for _ in range(reps):
            for t in targets:
                fn(t)
        runs.append((time.perf_counter() - t0) / (reps * len(targets)) * 1e6)
    return statistics.median(runs)


def main():
    keys_all = corpus().keys
    rows = []
    rng = random.Random(1)
    for n in SIZES:
        items = sorted(keys_all[:n])
        avg_targets = rng.sample(items, 200)
        absent = -1
        t_hash, table = timed(build_hash_table, items)
        t_dict, ref = timed(lambda xs: {k: i for i, k in enumerate(xs)}, items)
        rows.append(dict(method="Hash table build (own)", n=n, scenario="setup", microseconds=f"{t_hash * 1e6:.1f}"))
        rows.append(dict(method="dict build (reference)", n=n, scenario="setup", microseconds=f"{t_dict * 1e6:.1f}"))
        rows.append(dict(method="Hash table longest chain", n=n, scenario="setup", microseconds=table.longest_chain()))
        methods = {
            "Linear Search": lambda t: linear_search(items, t),
            "Binary Search": lambda t: binary_search(items, t),
            "Hash Table (own)": lambda t: table.get(t),
            "dict (reference)": lambda t: ref.get(t, -1),
        }
        best = {"Linear Search": items[0], "Binary Search": items[(n - 1) // 2],
                "Hash Table (own)": items[0], "dict (reference)": items[0]}
        for name, fn in methods.items():
            slow = name == "Linear Search"
            plan = {
                "best": ([best[name]], 500 if slow else 20000),
                "average": (avg_targets, 1 if slow else 20),
                "worst": ([absent], max(3, 20_000_000 // n) if slow else 20000),
            }
            for scen, (targets, reps) in plan.items():
                us = per_search_us(fn, targets, reps)
                rows.append(dict(method=name, n=n, scenario=scen, microseconds=f"{us:.3f}"))
                print(f"n={n:>8} {scen:<8} {name:<18} {us:12.3f} us", flush=True)
    write_csv("lookup_results.csv", rows)


if __name__ == "__main__":
    main()
