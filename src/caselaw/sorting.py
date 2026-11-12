"""Sorting algorithms, written by hand (no calls to sorted() inside them).

Every function takes a list of comparable items and returns a NEW sorted list; the
input is never modified. The experiments sort packed integer keys (see data.pack_key).

Summary (n = number of items)
    algorithm                time best    time average   time worst    extra space
    insertion sort           O(n)         O(n^2)         O(n^2)        O(1)
    merge sort               O(n log n)   O(n log n)     O(n log n)    O(n)
    quick sort, first pivot  O(n log n)   O(n log n)     O(n^2)        O(log n) on average
    quick sort, random pivot O(n log n)   O(n log n)     O(n^2) (rare) O(log n) expected
    heap sort                O(n log n)   O(n log n)     O(n log n)    O(1)
"""
from __future__ import annotations

import random


def insertion_sort(data):
    """Grow a sorted prefix; insert each new item by shifting larger items right."""
    a = list(data)
    for i in range(1, len(a)):
        current = a[i]
        j = i - 1
        while j >= 0 and a[j] > current:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = current
    return a


def merge_sort(data):
    """Split in half, sort each half recursively, merge the two sorted halves."""
    a = list(data)
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left = merge_sort(a[:mid])
    right = merge_sort(a[mid:])
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:          # <= keeps the sort stable
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def _quick_sort(a, pick_pivot):
    """Iterative quick sort with Lomuto partitioning and an explicit stack, so the
    quadratic worst case cannot overflow Python's recursion limit."""
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        p = pick_pivot(lo, hi)
        a[p], a[hi] = a[hi], a[p]           # move the pivot to the end of the range
        pivot = a[hi]
        i = lo                               # a[lo:i] holds items smaller than the pivot
        for j in range(lo, hi):
            if a[j] < pivot:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]            # pivot lands in its final position
        stack.append((lo, i - 1))
        stack.append((i + 1, hi))
    return a


def quick_sort_first_pivot(data):
    """Quick sort that always picks the first item of a range as pivot (naive)."""
    return _quick_sort(list(data), lambda lo, hi: lo)


def quick_sort_random_pivot(data):
    """Quick sort with a uniformly random pivot (makes the worst case very unlikely)."""
    return _quick_sort(list(data), lambda lo, hi: random.randint(lo, hi))


def _sift_down(a, root, end):
    """Restore the max-heap property below index root, considering a[0:end]."""
    while True:
        child = 2 * root + 1
        if child >= end:
            return
        if child + 1 < end and a[child] < a[child + 1]:
            child += 1
        if a[root] < a[child]:
            a[root], a[child] = a[child], a[root]
            root = child
        else:
            return


def heap_sort(data):
    """Build a max-heap in place (O(n)), then repeatedly move the maximum to the end."""
    a = list(data)
    n = len(a)
    for start in range(n // 2 - 1, -1, -1):
        _sift_down(a, start, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        _sift_down(a, 0, end)
    return a


def builtin_sorted(data):
    """Reference only: Python's built-in Timsort, implemented in C."""
    return sorted(data)


SORTERS = {
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Quick Sort (first pivot)": quick_sort_first_pivot,
    "Quick Sort (random pivot)": quick_sort_random_pivot,
    "Heap Sort": heap_sort,
}
REFERENCE_SORTER = ("Python sorted() (reference)", builtin_sorted)
