# Pseudocode and complexity

## Insertion sort — O(n²) worst/average, O(n) best (already sorted)
```
for i = 1 to n-1: x = A[i]; j = i-1
    while j >= 0 and A[j] > x: A[j+1] = A[j]; j--
    A[j+1] = x
```
## Merge sort — Θ(n log n) all cases, O(n) extra space, stable
```
sort(A): if |A| <= 1 return A
    L = sort(left half); R = sort(right half); return merge(L, R)
```
## Quick sort (Lomuto partition) — O(n log n) average, O(n²) worst (first pivot on sorted input)
```
partition(A, lo, hi): pivot = A[hi]; i = lo
    for j = lo to hi-1: if A[j] < pivot: swap A[i], A[j]; i++
    swap A[i], A[hi]; return i
```
First-pivot variant uses A[lo]; random-pivot variant swaps a random element to the pivot position first.
Implemented iteratively with an explicit stack (no recursion limit).
## Heap sort — Θ(n log n) all cases, in place
```
build max-heap bottom-up (O(n)); repeat n-1 times: swap root with last, shrink heap, sift-down
```
## Linear search — O(n). Binary search — O(log n), needs sorted input. Hash table — O(1) expected
Chaining table, Fibonacci hashing `((hash(k) * 11400714819323198485) mod 2^64) >> (64 - bits)`, doubles when load factor > 0.75.
## Keyword retrieval (Top-K, OR semantics, score = total term occurrences)
- **A:** scan every passage with a regex, score it, sort all matches (merge sort). O(n·L + m log m)
- **B:** inverted index (term → postings); score the postings of query terms; sort all m matches. O(Σ postings + m log m)
- **C:** same index; keep a size-K max-heap of the best candidates. O(Σ postings + m log K)
Build index once: O(total tokens) time and space.
