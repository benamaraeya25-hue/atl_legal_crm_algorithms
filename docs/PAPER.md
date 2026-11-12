# Choosing Algorithms for a Case-Law Research Engine: Sorting, Look-up and Top-K Retrieval over One Million Court-Opinion Passages

**Eya Ben Amara** — CPS 3440 Analysis of Algorithms, Kean University, Fall 2026
Repository: https://github.com/benamaraeya25-hue/atl_legal_crm_algorithms · Site: https://benamaraeya25-hue.github.io/atl_legal_crm_algorithms/

*First draft. Numbers come from `results/*.csv` produced by `benchmarks/run_all.sh`; rerun on your own machine before submitting and update the tables.*

## 1. Abstract

Legal research tools must find, order and retrieve passages from very large collections of court opinions. I built a small research engine in pure Python on a real public dataset (8,417 U.S. Supreme Court decisions, 1946–2016) and compared hand-written algorithms for three tasks on up to 1,000,000 sentence-level passages: (1) sorting passages chronologically with insertion, merge, quick (two pivot rules) and heap sort; (2) looking up a passage by citation key with linear search, binary search and a chaining hash table; and (3) keyword search with Top-K ranking using a full scan, an inverted index with a full sort, and an inverted index with a size-K heap. Measurements agree with theory: counts of comparisons match n(n−1)/2 for the quadratic cases exactly, and runtime grows with exponents near 1.1 for n log n algorithms. Efficiency matters at this scale: a first-pivot quick sort needed 1.26 s on 10,000 already-sorted keys versus 0.011 s for random pivots; a linear lookup took 19 ms per query at one million passages versus 1.9 µs for binary search; and an inverted index with a heap answered a rare query in 0.13 ms versus 568 ms for a scan (about 4,500 times faster), at the price of a 14 s, 167 MB index build. For this application I recommend an inverted index with heap Top-K and a sorted array with binary search for citation look-up.

## 2. Introduction

A law firm's working material is text: statutes, opinions and contracts. Associates repeatedly (a) order authorities by date, (b) open a specific cited passage, and (c) search for passages about a legal concept and read the best few. Each is a classic algorithmic problem, and the right algorithm changes by orders of magnitude as the collection grows. This project asks: **for each of these three tasks, which algorithm should a case-law research engine use, and do measured costs agree with textbook analysis?**

Contributions: (i) a reproducible 1,000,000-passage corpus built from a real public dataset; (ii) hand-implemented algorithms (no library sorting or searching inside the algorithms under test; Python's `sorted()` and `dict` are used only as labeled references); (iii) 68 unit tests; (iv) multi-scale benchmarks from 1,000 to 1,000,000 with runtime, exact comparison counts and memory; and (v) analysis against asymptotic theory.

## 3. Dataset

I used the textacy-data **Supreme Court Decisions** dataset: 8,419 decisions (8,417 usable) decided 1946–2016. Decision text comes from FindLaw and metadata from the Supreme Court Database (CC BY-NC 3.0 US); the two were merged by a deduplication model, so occasional mismatches are possible. The text totals 360,344,120 characters. It is public, real, non-synthetic, and I did not generate any of it. The 111 MB file is not committed to the repository; `python -m caselaw.cli download` fetches it (see `docs/DATASET.md`).

**Passages.** Each decision is split into sentence-like passages (regex split after `.`, `!`, `?` plus whitespace, minimum 30 characters), giving 2,152,182 passages. A seeded random sample (rate 0.6, seed 3440) is shuffled and truncated to exactly 1,000,000. The 1k, 10k, 100k and 1M experiment sizes are prefixes of this list, so each is a random sample nested in the next. Each passage has an integer key `date × 10⁹ + case × 10⁵ + sentence`, which works both as a pinpoint citation and as a chronological sort key.

## 4. Problem Formulation

Let P be a multiset of n passages, each with a unique integer key k(p) and text t(p).

1. **Sorting.** Output the keys in non-decreasing order. Inputs: random order (average case), already sorted (best case for some algorithms) and reverse sorted (worst case for others).
2. **Look-up.** Given a key q, return its index in the collection or report absence. Best case: the first item (middle item for binary search). Average: 200 random present keys. Worst: an absent key.
3. **Top-K retrieval.** Given a query of terms, score each passage by the total number of occurrences of the query terms (OR semantics) and return the K = 10 best, ties broken by smaller passage id. Let m be the number of passages that contain at least one query term. Queries are grouped by match rate at 100k passages: *rare* (< 0.5%), *medium* (0.5–5%) and *common* (> 5%), 22 queries in total.

Retrieval is an *approximate* model of relevance (term frequency only); it is meant to expose algorithmic costs, not to rival a production search engine.

## 5. Algorithms

| Task | Algorithm | Idea | Time | Extra space |
|---|---|---|---|---|
| Sort | Insertion | grow a sorted prefix | O(n²); O(n) if sorted | O(1) |
| Sort | Merge | split, sort halves, merge | Θ(n log n) | O(n) |
| Sort | Quick (first pivot) | partition around first element | O(n log n) avg; **O(n²)** sorted input | O(log n) avg stack |
| Sort | Quick (random pivot) | random pivot | O(n log n) expected | O(log n) |
| Sort | Heap | binary max-heap | Θ(n log n) | O(1) |
| Look-up | Linear | scan | O(n) | O(1) |
| Look-up | Binary | halve a sorted array | O(log n) | O(1) |
| Look-up | Hash table | chaining + Fibonacci hashing, doubling at load 0.75 | O(1) expected | O(n) |
| Retrieval | A: scan + sort | regex-scan every passage, sort all matches | O(n·L + m log m) | O(m) |
| Retrieval | B: index + sort | inverted index, sort all matches | O(Σ postings + m log m) | index |
| Retrieval | C: index + heap | inverted index, size-K heap | O(Σ postings + m log K) | index + O(K) |

Why these: sorting gives the textbook spread from quadratic to optimal comparison sorts; look-up shows the three standard access structures; retrieval shows that *data-structure choice* (index) and *selection strategy* (heap versus full sort) are separate decisions, which is exactly the Top-K pattern used in real search systems. Pseudocode is in `docs/PSEUDOCODE.md`.

## 6. Correctness and Complexity Analysis

*Correctness.* Insertion sort maintains the invariant that A[0..i) is sorted. Merge sort is correct by induction and stable because ties are taken from the left half. Quick sort's partition places the pivot in its final position, with smaller elements left of it. Heap sort builds a max-heap and repeatedly moves the root to the end. Binary search keeps the invariant that the key, if present, lies in [lo, hi]. The hash table stores each key in the chain of its slot and resizes by rehashing. For retrieval, A, B and C return identical results (asserted in the benchmark for every query at every size and in unit tests); C is correct because a size-K heap that evicts its worst element always holds the K best seen so far.

*Complexity.* Insertion sort does between n−1 and n(n−1)/2 comparisons. Merge sort performs about n log₂ n − n comparisons; any comparison sort needs Ω(n log n) in the worst case (decision tree with n! leaves), so merge and heap sort are asymptotically optimal. Quick sort with first-element pivot on sorted input produces partitions of sizes 0 and n−1, giving n(n−1)/2 comparisons. A random pivot makes that outcome exponentially unlikely, giving expected O(n log n). Binary search takes ⌊log₂ n⌋+1 steps. A hash table with load factor ≤ 0.75 has expected chain length below 1 + α, hence O(1) expected look-up; doubling gives O(1) amortized insertion. Retrieval C improves on B because selecting K of m items with a heap costs O(m log K) rather than O(m log m).

## 7. Implementation

Python 3.13 (CPython), standard library only for algorithms; matplotlib for figures and pytest for tests. Source: `src/caselaw/` (`data.py`, `sorting.py`, `lookup.py`, `retrieval.py`, `instrument.py`, `cli.py`). Notable decisions: quick sort is iterative with an explicit stack so worst-case inputs do not hit Python's recursion limit; the inverted index stores postings in compact `array` objects (4-byte ids, 2-byte term counts); ranking packs `(65535 − score) << 24 | passage_id` into one integer so ascending order means best first, which lets the same sort and heap code serve retrieval. Comparison counts use a `CountedInt` wrapper that counts `<`, `<=`, `>`, `>=`, `==`, so the algorithms run unmodified. The 68 tests compare every sorter against `sorted()` on edge cases (empty, one element, duplicates, sorted, reversed), check stability of merge sort, check comparison counts against closed forms, test hash-table collisions and resizing, and verify A = B = C.

## 8. Experimental Methodology

- **Hardware:** 2 vCPU x86-64 Linux cloud container with 8.2 GB RAM, Python 3.13.18 (`results/environment.txt`). Cloud timing is noisy; absolute values will differ on other machines, relative behaviour should not.
- **Sizes:** n = 1,000; 10,000; 100,000; 1,000,000 (prefixes of one seeded corpus).
- **Repetitions:** wall-clock `time.perf_counter()` after `gc.collect()`; 5 repetitions at 1k, 3 at larger sizes (1 for the slowest cases: quadratic runs at 10k and heap sort at 1M); median reported, min and max stored. Look-up times are per search, averaged over many repetitions.
- **Skipped runs:** quadratic combinations (insertion on random and reversed, first-pivot quick sort on sorted and reversed) were not run at ≥ 100,000 because they would take hours. I do **not** report extrapolated numbers as measurements.
- **Extra metrics:** exact comparison counts (n = 500…8,000, three input orders), peak extra memory via `tracemalloc`, index build time and size, and number of matches m.
- **Controls:** fixed seeds (corpus 3440, random pivot 12345), every sorter's output asserted equal to `sorted()`, every retrieval method asserted equal to the others.
- **Reproduce:** `bash benchmarks/run_all.sh && python benchmarks/make_figures.py`.

## 9. Results

### 9.1 Sorting (median seconds)

| Algorithm | 1,000 random | 10,000 random | 100,000 random | 1,000,000 random | 1,000,000 sorted | 1,000,000 reversed |
|---|---|---|---|---|---|---|
| Insertion | 0.0137 | 1.64 | skipped | skipped | **0.109** | skipped |
| Merge | 0.0013 | 0.016 | 0.200 | 3.02 | 2.45 | 2.24 |
| Quick (first pivot) | 0.0008 | 0.014 | 0.124 | 2.25 | skipped | skipped |
| Quick (random pivot) | 0.0010 | 0.012 | 0.141 | 2.19 | 1.70 | 2.41 |
| Heap | 0.0013 | 0.019 | 0.261 | 5.09 | 3.81 | 3.47 |
| `sorted()` (reference) | 0.00016 | 0.0018 | 0.023 | 0.329 | 0.036 | 0.035 |

Figure `figures/sorting_runtime.png` shows all three input orders. Key observations: (1) insertion sort is unusable on random data beyond 10k yet is the fastest hand-written algorithm on already-sorted data (0.109 s versus 2.45 s for merge sort at one million); (2) first-pivot quick sort is fastest on random data but degrades to 1.26 s on only 10,000 sorted keys; (3) heap sort is consistently about 1.2–1.8 times slower than merge sort in Python; (4) the built-in `sorted()` (Timsort in C) is about 9 times faster than my best hand-written sort on random data and 70 times faster on sorted data.

**Exact comparisons at n = 8,000:** insertion sort 15,925,783 (random), 7,999 (sorted), 31,996,000 (reversed); first-pivot quick sort 31,996,000 on sorted and reversed input; merge sort 93,610 random; random-pivot quick sort ≈ 122,000; heap sort ≈ 183,000.

### 9.2 Look-up (microseconds per search; comparisons at n = 100,000)

| Method | n=1,000,000 best | average | worst (absent) | avg comparisons at 100k |
|---|---|---|---|---|
| Linear | 0.154 | 19,186 | 33,514 | 47,475 |
| Binary | 0.153 | 1.91 | 1.46 | 30.4 (≈ 2 per halving step) |
| Hash table (own) | 0.239 | 0.256 | 0.183 | 1.18 |
| `dict` (reference) | 0.065 | 0.064 | 0.064 | — |

Building the hash table at 1,000,000 keys took 7.65 s (the built-in `dict`: 0.26 s); the longest chain was 6. Peak extra memory at 100,000 keys was 318 bytes per item for my table versus 103 for `dict`.

### 9.3 Retrieval (1,000,000 passages, milliseconds per query, K = 10)

| Query (class) | matches m | A scan+sort | B index+sort | C index+heap |
|---|---|---|---|---|
| wiretap (rare) | 198 | 568 | 0.289 | **0.125** |
| miranda (rare) | 1,732 | 608 | 2.11 | 0.580 |
| equal protection (medium) | 14,606 | 1,107 | 21.2 | 3.67 |
| amendment (medium) | 30,064 | 882 | 41.9 | 6.65 |
| court (common) | 185,602 | 1,022 | 303 | 44.0 |

The index took 14.4 s to build and occupies 166.6 MB (97,998 terms, 21.9 million postings). For the query "court", selecting the top 10 took 264 ms with a full sort versus 5.5 ms with the heap (48 times faster); the remaining 41 ms of C's 44 ms is scoring the postings. Method A's cost is almost independent of the query (570–1,170 ms) because it always reads all one million passages.

## 10. Theory vs. Observed Performance

I fitted straight lines to log-log plots of runtime against n (`results/growth_exponents.csv`). An n log n algorithm over 10³–10⁶ should show an apparent exponent of about 1.10 (the ratio of n log n at the two ends gives log(2000)/log(1000)).

| Quantity | Theory | Observed exponent |
|---|---|---|
| Merge / quick / heap, random input, time | ≈ 1.10 | 1.12 / 1.12–1.14 / 1.19 |
| Insertion sort, sorted input, time | 1.0 | 1.05 |
| Insertion / first-pivot quick, reversed, comparisons | 2.0 | 2.00 / 2.00 |
| Merge, heap, random, comparisons | ≈ 1.1–1.15 | 1.15 / 1.16 |
| Linear search, average | 1.0 | 1.07 |
| Binary search, average | ≈ 0 (log n) | 0.13 |
| Hash table | 0 | 0.00 |
| Retrieval A (scan) | 1.0 | 0.98–1.00 |
| Retrieval B/C, rare queries | m grows ∝ n, but is tiny | 0.60 / 0.39 |
| Retrieval B/C, common queries | 1.0 (m ∝ n) | 0.99 / 0.77 |

The comparison counts match theory almost exactly: n(n−1)/2 = 31,996,000 for n = 8,000, and n−1 = 7,999 for insertion sort on sorted input. Runtimes agree in shape but show constant-factor effects theory ignores: heap sort has the same comparison growth as merge sort but its exponent is a little higher and its constants are worse, because sift-down accesses memory far apart and performs more Python-level operations (about 2n log n comparisons versus n log n). Cache and interpreter overhead also explain why quick sort with a random pivot, which makes slightly *more* comparisons than merge sort (≈122,000 versus 93,610), still runs faster in practice: it works in place with no allocation. Retrieval times scale with m, not n, for the index methods, which is why rare queries scale sub-linearly. A first-pivot quick sort that looks excellent on random input has an observable cliff on sorted input, which is common in real data because court records are often loaded in date order.

## 11. Algorithmic Efficiency vs. Computational Hardness

An *inefficient algorithm* is a slow way to solve a problem that has a fast solution; a *computationally hard problem* is one for which no fast algorithm is known (or none exists under standard assumptions). Insertion sort and first-pivot quick sort are inefficient algorithms for sorting, but sorting is easy: an optimal Θ(n log n) algorithm exists and matches the Ω(n log n) lower bound. Replacing one by the other changed the 10,000-key sorted run from 1.26 s to 0.011 s with no change in the problem.

A genuinely hard problem near this project is **legal citation coverage**: given a set of legal issues and the set of passages that address each one, find the *smallest* collection of passages that covers every issue. This is the Set Cover problem, which is NP-hard; no polynomial-time exact algorithm is known, and the greedy algorithm only guarantees a ln n approximation. I did not implement it. The distinction matters for engineering: for the hard problem, you accept an approximation; for the easy ones in this project, there is no excuse for a quadratic method on a million items.

## 12. Limitations and Ethical / Societal Considerations

*Limitations.* (1) Python's interpreter overhead hides some theoretical differences, and the C-implemented `sorted()` is much faster than any pure-Python sort, so these experiments show relative rather than absolute costs. (2) Timings come from one 2-vCPU cloud container; confidence intervals are not computed (min, median, max are stored). (3) Quadratic cases were skipped at ≥ 100k. (4) Passage splitting is a regex that splits on abbreviations such as "U.S."; this affects the passage content, not the algorithm costs. (5) Term-frequency scoring is a crude measure of relevance (no stemming, stop-word handling or phrase matching) and the three methods are compared on speed, not on retrieval quality. (6) The dataset covers only Supreme Court decisions and merged text with metadata imperfectly. (7) The hash table keys are integers, so string-key behavior is untested.

*Ethical and societal.* Court opinions are public records, but they name real people; a research engine should not be used to profile individuals. Legal professionals might over-trust a ranked list: a high term-frequency score is not legal relevance, and results must be read and verified. Faster search may widen the gap between well-resourced firms and others unless made widely available. The dataset's metadata is licensed non-commercially, so any commercial product built on this approach would need other data or permission. Finally, generative AI assisted me in producing code and drafts for this project; I am responsible for checking and defending all of it (see `CONTRIBUTIONS.md`).

## 13. Course Learning Objective Reflection

**A — Efficiency.** Searching one million passages for a rare phrase took 568 ms with a full scan and 0.125 ms with an inverted index and heap (about 4,500 times faster). Binary search found a key in 1.9 µs where linear search needed 19 ms. Efficiency is what makes interactive research possible.

**B — Complexity.** Merge sort: Θ(n log n) time in every case, O(n) extra space. Measured comparisons at n = 8,000 were 93,610 versus the bound n log₂ n ≈ 103,900, and runtime exponent was 1.12 versus an expected ≈ 1.10, so measurements were consistent with theory; peak extra memory was about 33 bytes per item versus 8 for the in-place sorters (whose 8 bytes are the output list).

**C — Hardness.** An inefficient algorithm is one worse than necessary (insertion sort on random data: 15.9 million comparisons at 8,000 items). A hard problem has no known efficient algorithm (set cover for minimal citation coverage, NP-hard). Sorting is not hard; quadratic sorting is just a poor choice.

**D — Selection.** I investigated five sorts, three look-up structures and three retrieval pipelines. For the real application: an **inverted index with heap Top-K** for keyword search (index build amortizes after about 16 queries); a **sorted array with binary search** for citation look-up, since it needs only a sorted array (a hash table's extra 7.65 s build and 3 times the memory buy a saving of about 1.6 µs per query that rarely repays it); and for sorting, a **merge sort or random-pivot quick sort** in a stable, predictable O(n log n) setting, or in practice the language's built-in sort.

## 14. Conclusion

On one million real court-opinion passages, the algorithmic choice changed runtimes by factors from 10 to 4,500 for the same output, and measured growth followed textbook analysis closely. The most valuable decisions were structural: build an inverted index, and select Top-K with a heap rather than sorting everything. Future work: stemming and phrase queries, BM25 ranking with an evaluation of retrieval quality, a compressed index, string-keyed hash tables, a C or NumPy comparison to separate algorithmic from interpreter costs, and measuring on more than one machine.

## 15. Individual Contributions

Individual project; all work by Eya Ben Amara (see `CONTRIBUTIONS.md`), with generative-AI assistance disclosed there.

## 16. References

1. T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein. *Introduction to Algorithms*, 4th ed. MIT Press, 2022.
2. D. E. Knuth. *The Art of Computer Programming, Vol. 3: Sorting and Searching*, 2nd ed. Addison-Wesley, 1998.
3. C. D. Manning, P. Raghavan, H. Schütze. *Introduction to Information Retrieval*. Cambridge University Press, 2008.
4. H. J. Spaeth et al. *Supreme Court Database*. http://supremecourtdatabase.org (CC BY-NC 3.0 US).
5. B. DeWilde. *textacy-data: Supreme Court Decisions* (v1.0). https://github.com/bdewilde/textacy-data
6. Python Software Foundation. *Python 3.13 documentation: `sorted`, `dict`, `array`, `time.perf_counter`*. https://docs.python.org/3.13/
