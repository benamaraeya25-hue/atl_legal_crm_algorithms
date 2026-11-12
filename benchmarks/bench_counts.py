"""Experiment 4: comparison counts (exact) and peak extra memory.

Comparison counts use caselaw.instrument.CountedInt, so the algorithms run unchanged.
Memory uses tracemalloc: peak extra bytes while an algorithm runs on 20,000 random keys.
Writes results/comparisons_sorting.csv, comparisons_lookup.csv and memory.csv.
"""
import random
import tracemalloc

from common import corpus, write_csv
from caselaw.instrument import CountedInt, count_search_comparisons, count_sort_comparisons
from caselaw.lookup import HashTable, binary_search, build_hash_table, linear_search
from caselaw.sorting import SORTERS

SIZES = (500, 1_000, 2_000, 4_000, 8_000)


def sorting_counts(keys_all):
    rows = []
    for n in SIZES:
        keys = keys_all[:n]
        scen = {"random": keys, "sorted": sorted(keys), "reversed": sorted(keys, reverse=True)}
        for sname, values in scen.items():
            for name, fn in SORTERS.items():
                random.seed(7)
                c = count_sort_comparisons(fn, values)
                rows.append(dict(algorithm=name, n=n, scenario=sname, comparisons=c))
                print(f"count n={n:>5} {sname:<8} {name:<26} {c:>12,}", flush=True)
    return rows


def lookup_counts(keys_all):
    rows = []
    rng = random.Random(2)
    for n in (1_000, 10_000, 100_000):
        items = sorted(keys_all[:n])
        targets = rng.sample(items, 100)
        counted = [CountedInt(v) for v in items]
        lin = sum(count_search_comparisons(linear_search, counted, t) for t in targets) / 100
        bis = sum(count_search_comparisons(binary_search, counted, t) for t in targets) / 100
        table = HashTable(track=True)
        for i, k in enumerate(items):
            table.put(k, i)
        table.comparisons = 0
        for t in targets:
            table.get(t)
        for name, val in (("Linear Search", lin), ("Binary Search", bis), ("Hash Table (own)", table.comparisons / 100)):
            rows.append(dict(method=name, n=n, avg_comparisons=f"{val:.2f}"))
            print(f"count lookup n={n:>7} {name:<18} {val:12.2f}", flush=True)
    return rows


def memory_rows(keys_all):
    rows = []
    n = 20_000
    keys = keys_all[:n]
    for name, fn in SORTERS.items():
        random.seed(7)
        tracemalloc.start()
        base = tracemalloc.get_traced_memory()[0]
        out = fn(keys)
        peak = tracemalloc.get_traced_memory()[1] - base
        tracemalloc.stop()
        del out
        rows.append(dict(structure=name, n=n, peak_extra_bytes=peak, bytes_per_item=f"{peak / n:.1f}"))
        print(f"memory {name:<28} {peak:>10,} bytes ({peak / n:.1f} per item)", flush=True)
    n = 100_000
    keys = keys_all[:n]
    for label, build in (("Hash table (own)", build_hash_table),
                         ("dict (reference)", lambda xs: {k: i for i, k in enumerate(xs)})):
        tracemalloc.start()
        base = tracemalloc.get_traced_memory()[0]
        obj = build(keys)
        peak = tracemalloc.get_traced_memory()[1] - base
        tracemalloc.stop()
        del obj
        rows.append(dict(structure=label, n=n, peak_extra_bytes=peak, bytes_per_item=f"{peak / n:.1f}"))
        print(f"memory {label:<28} {peak:>10,} bytes ({peak / n:.1f} per item)", flush=True)
    return rows


def main():
    keys_all = corpus().keys
    write_csv("comparisons_sorting.csv", sorting_counts(keys_all))
    write_csv("comparisons_lookup.csv", lookup_counts(keys_all))
    write_csv("memory.csv", memory_rows(keys_all))


if __name__ == "__main__":
    main()
