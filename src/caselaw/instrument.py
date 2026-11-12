"""Count key comparisons without touching the algorithms' code.

CountedInt wraps an integer and counts every comparison made on it. Running an
algorithm on CountedInt values gives its exact number of comparisons for that input.
"""
from __future__ import annotations


class CountedInt:
    __slots__ = ("v",)
    comparisons = 0

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        CountedInt.comparisons += 1
        return self.v < other.v

    def __le__(self, other):
        CountedInt.comparisons += 1
        return self.v <= other.v

    def __gt__(self, other):
        CountedInt.comparisons += 1
        return self.v > other.v

    def __ge__(self, other):
        CountedInt.comparisons += 1
        return self.v >= other.v

    def __eq__(self, other):
        CountedInt.comparisons += 1
        return self.v == other.v

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountedInt({self.v})"


def count_sort_comparisons(sorter, values) -> int:
    """Comparisons used by sorter on values. Also checks the output is correct."""
    items = [CountedInt(v) for v in values]
    CountedInt.comparisons = 0
    out = sorter(items)
    used = CountedInt.comparisons
    assert [x.v for x in out] == sorted(values), "sorter returned a wrong result"
    return used


def count_search_comparisons(searcher, items, target) -> int:
    """Key comparisons (== and <) used by one call searcher(items, target)."""
    CountedInt.comparisons = 0
    searcher(items, CountedInt(target))
    return CountedInt.comparisons
