"""Keyword search over passages: three approaches that return identical results.

Query semantics: a passage matches if it contains at least one query word. Its score is
the total number of occurrences of the query words. Results are the K passages with the
highest score; ties are broken by the smaller passage number.

    approach                    how it finds matches          how it picks the top K
    A  naive scan               regex over every passage      merge sort of all matches
    B  inverted index + sort    posting lists                 merge sort of all matches
    C  inverted index + heap    posting lists                 size-K heap, one pass

Complexity (N passages, m matching passages, K results, L average passage length)
    A  O(N*L + m log m) per query, no extra memory
    B  O(P + m log m) per query, P = postings read; index build O(N*L), memory O(N*L)
    C  O(P + m log K) per query, same index as B
"""
from __future__ import annotations

import re
import sys
from array import array

from .sorting import _sift_down, heap_sort, merge_sort

_TOKEN = re.compile(r"\w+")
PID_BITS = 24                       # passage numbers up to 16.7 million
SCORE_CAP = 65535
PID_MASK = (1 << PID_BITS) - 1


def tokenize(text: str) -> list[str]:
    """Lower-case word tokens (letters, digits, underscore)."""
    return _TOKEN.findall(text.lower())


def parse_query(query: str) -> list[str]:
    """Unique query words, in order of first appearance."""
    seen, out = set(), []
    for t in tokenize(query):
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def rank_key(score: int, pid: int) -> int:
    """One integer whose ascending order is: higher score first, then smaller passage id."""
    return ((SCORE_CAP - (score if score < SCORE_CAP else SCORE_CAP)) << PID_BITS) | pid


def decode(key: int) -> tuple[int, int]:
    """Inverse of rank_key: returns (passage id, score)."""
    return key & PID_MASK, SCORE_CAP - (key >> PID_BITS)


# ---------------------------------------------------------------------------
# Inverted index
# ---------------------------------------------------------------------------
class InvertedIndex:
    """term -> (array of passage ids, array of term counts), ids in increasing order."""
    __slots__ = ("postings", "n_passages")

    def __init__(self, postings, n_passages):
        self.postings = postings
        self.n_passages = n_passages

    @classmethod
    def build(cls, lowered_texts):
        postings: dict[str, tuple[array, array]] = {}
        findall = _TOKEN.findall
        for pid, text in enumerate(lowered_texts):
            counts: dict[str, int] = {}
            for tok in findall(text):
                counts[tok] = counts.get(tok, 0) + 1
            for tok, c in counts.items():
                post = postings.get(tok)
                if post is None:
                    post = postings[tok] = (array("I"), array("H"))
                post[0].append(pid)
                post[1].append(c if c < 65535 else 65535)
        return cls(postings, len(lowered_texts))

    def size_bytes(self) -> int:
        """Approximate memory held by the index (dictionary, term strings, arrays)."""
        total = sys.getsizeof(self.postings)
        for term, (ids, tfs) in self.postings.items():
            total += sys.getsizeof(term) + sys.getsizeof((ids, tfs))
            total += sys.getsizeof(ids) + sys.getsizeof(tfs)
        return total

    def n_terms(self) -> int:
        return len(self.postings)

    def hits(self, term: str) -> int:
        post = self.postings.get(term)
        return len(post[0]) if post else 0


# ---------------------------------------------------------------------------
# Top-K selection
# ---------------------------------------------------------------------------
def select_sort(keys, k):
    """Sort every candidate, keep the first k. O(m log m)."""
    return merge_sort(keys)[:k]


def _sift_up(a, i):
    while i > 0:
        parent = (i - 1) // 2
        if a[parent] < a[i]:
            a[parent], a[i] = a[i], a[parent]
            i = parent
        else:
            return


def select_heap(keys, k):
    """Keep the k smallest keys in a max-heap of size k. O(m log k).

    The heap root is the worst of the current best k. A new key only matters if it beats
    the root, and then it replaces the root and sinks to its place in O(log k) steps.
    """
    heap: list[int] = []
    root = None
    for key in keys:
        if len(heap) < k:
            heap.append(key)
            _sift_up(heap, len(heap) - 1)
            if len(heap) == k:
                root = heap[0]
        elif key < root:
            heap[0] = key
            _sift_down(heap, 0, k)
            root = heap[0]
    return heap_sort(heap)


# ---------------------------------------------------------------------------
# The three search approaches
# ---------------------------------------------------------------------------
def candidate_keys(index: InvertedIndex, terms) -> list[int]:
    """Score every passage that contains a query word; return its rank keys."""
    scores: dict[int, int] = {}
    get = scores.get
    for t in set(terms):
        post = index.postings.get(t)
        if post is None:
            continue
        for pid, tf in zip(post[0], post[1]):
            scores[pid] = get(pid, 0) + tf
    cap = SCORE_CAP
    return [((cap - (s if s < cap else cap)) << PID_BITS) | pid for pid, s in scores.items()]


def search_naive(lowered_texts, terms, k=10):
    """A: scan every passage with one regex; no index."""
    terms = sorted(set(terms))
    if not terms:
        return []
    pattern = re.compile(r"\b(?:%s)\b" % "|".join(map(re.escape, terms)))
    findall = pattern.findall
    keys = []
    for pid, text in enumerate(lowered_texts):
        n = len(findall(text))
        if n:
            keys.append(rank_key(n, pid))
    return [decode(x) for x in select_sort(keys, k)]


def search_index_sort(index: InvertedIndex, terms, k=10):
    """B: posting lists find the matches, then all matches are sorted."""
    return [decode(x) for x in select_sort(candidate_keys(index, terms), k)]


def search_index_heap(index: InvertedIndex, terms, k=10):
    """C: posting lists find the matches, then a size-k heap keeps the best k."""
    return [decode(x) for x in select_heap(candidate_keys(index, terms), k)]


METHODS = {
    "A: naive scan + sort": "naive",
    "B: inverted index + sort": "index-sort",
    "C: inverted index + heap Top-K": "index-heap",
}
