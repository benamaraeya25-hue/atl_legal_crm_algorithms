import random

import pytest

from caselaw.instrument import count_sort_comparisons
from caselaw.sorting import (SORTERS, heap_sort, insertion_sort, merge_sort,
                             quick_sort_first_pivot, quick_sort_random_pivot)

CASES = {
    "empty": [],
    "single": [7],
    "two sorted": [1, 2],
    "two reversed": [2, 1],
    "already sorted": list(range(200)),
    "reverse sorted": list(range(200, 0, -1)),
    "all equal": [5] * 50,
    "duplicates": [random.Random(1).randint(0, 9) for _ in range(300)],
    "negatives": [3, -1, -7, 0, 12, -7, 5],
}


@pytest.mark.parametrize("name", list(SORTERS))
@pytest.mark.parametrize("case", list(CASES))
def test_sorts_match_builtin(name, case):
    data = CASES[case]
    assert SORTERS[name](data) == sorted(data)


@pytest.mark.parametrize("name", list(SORTERS))
def test_random_inputs_and_input_not_modified(name):
    rng = random.Random(42)
    for n in (3, 10, 57, 500):
        data = [rng.randint(-1000, 1000) for _ in range(n)]
        copy = list(data)
        assert SORTERS[name](data) == sorted(data)
        assert data == copy, "the sorter must not modify its input"


def test_merge_sort_is_stable():
    items = [(1, "b"), (0, "x"), (1, "a"), (0, "y")]

    class Keyed:
        def __init__(self, t):
            self.t = t

        def __le__(self, other):
            return self.t[0] <= other.t[0]

    out = merge_sort([Keyed(t) for t in items])
    assert [k.t for k in out] == [(0, "x"), (0, "y"), (1, "b"), (1, "a")]


def test_quicksort_worst_case_does_not_hit_recursion_limit():
    data = list(range(3000))                   # first pivot is the worst case here
    assert quick_sort_first_pivot(data) == data


def test_comparison_counts_follow_theory():
    n = 400
    ordered = list(range(n))
    reverse = ordered[::-1]
    # insertion sort: n-1 comparisons when sorted, about n^2/2 when reversed
    assert count_sort_comparisons(insertion_sort, ordered) == n - 1
    assert count_sort_comparisons(insertion_sort, reverse) == n * (n - 1) // 2
    # first-pivot quick sort on sorted input is quadratic; random pivot is not
    assert count_sort_comparisons(quick_sort_first_pivot, ordered) > n * n // 3
    assert count_sort_comparisons(quick_sort_random_pivot, ordered) < 10 * n * 9
    # merge and heap sort stay near n log2 n
    import math
    bound = 2 * n * math.log2(n)
    assert count_sort_comparisons(merge_sort, reverse) < bound
    assert count_sort_comparisons(heap_sort, reverse) < bound
