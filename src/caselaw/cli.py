"""Command-line interface: a small case research tool built on the algorithms.

    python -m caselaw.cli download
    python -m caselaw.cli stats
    python -m caselaw.cli search "equal protection" --k 5 --method index-heap
    python -m caselaw.cli lookup "329 U.S. 1"
    python -m caselaw.cli timeline --n 8

Run from the repository root with PYTHONPATH=src (or after `pip install -e .`).
"""
from __future__ import annotations

import argparse
import sys
import time

from . import data
from .lookup import HashTable, binary_search, linear_search
from .retrieval import (InvertedIndex, parse_query, search_index_heap,
                        search_index_sort, search_naive)
from .sorting import merge_sort


def _corpus(passages: int):
    if not data.cache_path().exists():
        print("First run: preparing the passage corpus (about a minute, cached afterwards)...",
              file=sys.stderr)
    return data.load_or_build().subset(passages)


def _snippet(text: str, width: int = 230) -> str:
    return text if len(text) <= width else text[: width - 3] + "..."


def cmd_search(args):
    corpus = _corpus(args.passages)
    terms = parse_query(args.query)
    if not terms:
        print("empty query")
        return 1
    t0 = time.perf_counter()
    if args.method == "naive":
        hits = search_naive(corpus.lowered, terms, args.k)
        build = 0.0
    else:
        index = InvertedIndex.build(corpus.lowered)
        build = time.perf_counter() - t0
        fn = search_index_sort if args.method == "index-sort" else search_index_heap
        t0 = time.perf_counter()
        hits = fn(index, terms, args.k)
    took = time.perf_counter() - t0
    print(f"{len(corpus):,} passages | method: {args.method} | words: {terms}")
    if build:
        print(f"index built in {build:.2f} s (once); query took {took * 1000:.1f} ms\n")
    else:
        print(f"query took {took * 1000:.1f} ms\n")
    for rank, (pid, score) in enumerate(hits, 1):
        _, case_idx, _ = data.unpack_key(corpus.keys[pid])
        case = corpus.cases[case_idx]
        print(f"{rank:>2}. score {score:<3} {case['name'][:60]} ({case['date']}, {case['cite'] or 'no cite'})")
        print(f"      {_snippet(corpus.texts[pid])}")
    return 0


def cmd_lookup(args):
    corpus = _corpus(10)
    cites = [c["cite"] for c in corpus.cases if c["cite"]]
    names = [c["name"].upper() for c in corpus.cases]
    key = args.key.strip()
    pool = cites if key in cites else names
    key = key if pool is cites else key.upper()
    ordered = merge_sort(pool)
    table = HashTable()
    for i, v in enumerate(pool):
        table.put(v, i)
    print(f"looking up {key!r} among {len(pool):,} {'citations' if pool is cites else 'case names'}")
    for label, fn in (("linear search", lambda: linear_search(pool, key)),
                      ("binary search", lambda: binary_search(ordered, key)),
                      ("hash table", lambda: table.get(key))):
        t0 = time.perf_counter()
        for _ in range(200):
            pos = fn()
        us = (time.perf_counter() - t0) / 200 * 1e6
        print(f"  {label:<14} position {pos:>6}   {us:8.2f} microseconds")
    match = next((c for c in corpus.cases
                  if c["cite"] == key or c["name"].upper() == key), None)
    if match:
        print(f"\n{match['name']}\n  decided {match['date']}   citation {match['cite'] or 'none'}")
    else:
        print("\nno such case")
    return 0


def cmd_timeline(args):
    corpus = _corpus(args.passages)
    order = merge_sort(corpus.keys)
    lookup = {k: i for i, k in enumerate(corpus.keys)}
    print(f"earliest {args.n} of {len(corpus):,} passages, sorted by decision date (merge sort)\n")
    for key in order[: args.n]:
        date, case_idx, _ = data.unpack_key(key)
        print(f"{date}  {corpus.cases[case_idx]['name'][:50]}")
        print(f"      {_snippet(corpus.texts[lookup[key]], 160)}")
    return 0


def cmd_stats(_args):
    corpus = _corpus(10)
    s = corpus.stats
    print(f"decisions:               {s['cases']:,}")
    print(f"characters of text:      {s['chars_total']:,}")
    print(f"passages (>= {data.MIN_PASSAGE_CHARS} chars): {s['passages_total']:,}")
    print(f"passages in experiments: {s['passages_kept']:,} (random sample, seed {s['seed']})")
    dates = sorted(c["date"] for c in corpus.cases)
    print(f"decision dates:          {dates[0]} to {dates[-1]}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="caselaw", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download", help="fetch the dataset into data/raw/")
    sub.add_parser("stats", help="dataset summary")
    s = sub.add_parser("search", help="keyword search with Top-K results")
    s.add_argument("query")
    s.add_argument("--k", type=int, default=5)
    s.add_argument("--method", choices=["naive", "index-sort", "index-heap"], default="index-heap")
    s.add_argument("--passages", type=int, default=100_000)
    lk = sub.add_parser("lookup", help="find a decision by citation or exact case name")
    lk.add_argument("key")
    t = sub.add_parser("timeline", help="show passages in date order (sorting demo)")
    t.add_argument("--n", type=int, default=8)
    t.add_argument("--passages", type=int, default=20_000)
    args = p.parse_args(argv)
    if args.cmd == "download":
        data.download()
        return 0
    return {"search": cmd_search, "lookup": cmd_lookup, "timeline": cmd_timeline,
            "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
