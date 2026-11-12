"""Experiment 3: keyword search with Top-K over passages.

Compares A naive scan + sort, B inverted index + sort, C inverted index + heap Top-K.
Queries are grouped by how many passages they match at 100,000 passages:
rare (< 0.5%), medium (0.5% to 5%), common (> 5%).
Writes results/retrieval_results.csv and results/retrieval_index.csv.
"""
import statistics
import time

from common import SIZES, corpus, timed, write_csv
from caselaw.retrieval import (InvertedIndex, candidate_keys, decode, parse_query,
                               search_index_heap, search_index_sort, search_naive,
                               select_heap, select_sort)

K = 10
QUERIES = [
    "wiretap", "obscenity", "miranda", "negligence", "taxation", "antitrust", "cruel unusual",
    "habeas", "speech", "contract", "jury", "search seizure", "interstate commerce",
    "equal protection", "due process", "constitutional", "amendment",
    "court", "state", "united states", "law", "statute",
]


def median_ms(fn, reps):
    runs = []
    for _ in range(reps):
        t, _out = timed(fn)
        runs.append(t * 1000)
    return statistics.median(runs)


def query_class(fraction):
    return "rare" if fraction < 0.005 else "medium" if fraction < 0.05 else "common"


def main():
    full = corpus()
    # Fix each query's class once, from its match rate at 100,000 passages.
    probe = full.subset(100_000)
    probe_index = InvertedIndex.build(probe.lowered)
    classes = {q: query_class(len(candidate_keys(probe_index, parse_query(q))) / 100_000) for q in QUERIES}
    del probe, probe_index

    rows, index_rows = [], []
    for n in SIZES:
        sub = full.subset(n)
        builds = []
        for r in range(3 if n <= 100_000 else 1):
            t, index = timed(InvertedIndex.build, sub.lowered)
            builds.append(t)
        postings = sum(len(ids) for ids, _ in index.postings.values())
        index_rows.append(dict(n=n, build_s=f"{statistics.median(builds):.4f}",
                               size_mb=f"{index.size_bytes() / 1e6:.2f}",
                               terms=index.n_terms(), postings=postings))
        print(f"n={n:>8} index build {statistics.median(builds):.2f}s  {index.size_bytes() / 1e6:.1f} MB", flush=True)
        reps_naive = 5 if n <= 10_000 else 3 if n <= 100_000 else 1
        reps_fast = 5 if n <= 100_000 else 3
        for q in QUERIES:
            terms = parse_query(q)
            a = search_naive(sub.lowered, terms, K)
            b = search_index_sort(index, terms, K)
            c = search_index_heap(index, terms, K)
            assert a == b == c, f"approaches disagree on {q!r} at n={n}"
            keys = candidate_keys(index, terms)
            row = dict(query=q, query_class=classes[q], n=n, matches=len(keys),
                       match_fraction=f"{len(keys) / n:.5f}",
                       naive_ms=f"{median_ms(lambda: search_naive(sub.lowered, terms, K), reps_naive):.4f}",
                       index_sort_ms=f"{median_ms(lambda: search_index_sort(index, terms, K), reps_fast):.4f}",
                       index_heap_ms=f"{median_ms(lambda: search_index_heap(index, terms, K), reps_fast):.4f}",
                       score_ms=f"{median_ms(lambda: candidate_keys(index, terms), reps_fast):.4f}",
                       select_sort_ms=f"{median_ms(lambda: select_sort(keys, K), reps_fast):.4f}",
                       select_heap_ms=f"{median_ms(lambda: select_heap(keys, K), reps_fast):.4f}")
            rows.append(row)
            print(f"n={n:>8} {q:<20} m={len(keys):>7} naive {row['naive_ms']:>10} ms  "
                  f"B {row['index_sort_ms']:>9} ms  C {row['index_heap_ms']:>9} ms", flush=True)
        del index
    write_csv("retrieval_results.csv", rows)
    write_csv("retrieval_index.csv", index_rows)


if __name__ == "__main__":
    main()
