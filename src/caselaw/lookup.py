"""Exact-key look-up: linear search, binary search and a hand-written hash table.

Summary (n = number of items)
    method          build        search best   search average   search worst
    linear search   none         O(1)          O(n)             O(n)
    binary search   needs sort   O(1)          O(log n)         O(log n)
    hash table      O(n)         O(1)          O(1) expected    O(n) if all keys collide
"""
from __future__ import annotations


def linear_search(items, target):
    """Check items one by one. Works on unsorted data. Returns the index or -1."""
    for i, value in enumerate(items):
        if value == target:
            return i
    return -1


def binary_search(sorted_items, target):
    """Halve the search range each step. Requires sorted input. Returns index or -1."""
    lo, hi = 0, len(sorted_items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = sorted_items[mid]
        if value == target:
            return mid
        if value < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


class HashTable:
    """Hash table with separate chaining and automatic resizing.

    * capacity is always a power of two
    * slot = Fibonacci hashing of hash(key): multiply by 2^64/golden ratio, keep the top bits
    * each slot holds a small list of [key, value] pairs (the chain)
    * when items > max_load * capacity the table doubles and every item is re-inserted

    Expected O(1) put/get while the load factor stays below max_load.
    """
    _GOLDEN = 0x9E3779B97F4A7C15
    _MASK64 = (1 << 64) - 1

    def __init__(self, capacity: int = 1024, max_load: float = 0.75, track: bool = False):
        bits = max(4, (capacity - 1).bit_length())
        self._bits = bits
        self._slots = [None] * (1 << bits)
        self._count = 0
        self.max_load = max_load
        self.track = track             # count key comparisons (used by the experiments)
        self.comparisons = 0

    def __len__(self):
        return self._count

    @property
    def capacity(self):
        return len(self._slots)

    @property
    def load_factor(self):
        return self._count / len(self._slots)

    def _slot(self, key):
        return ((hash(key) * self._GOLDEN) & self._MASK64) >> (64 - self._bits)

    def put(self, key, value):
        i = self._slot(key)
        chain = self._slots[i]
        if chain is None:
            self._slots[i] = [[key, value]]
        else:
            for pair in chain:
                if self.track:
                    self.comparisons += 1
                if pair[0] == key:
                    pair[1] = value
                    return
            chain.append([key, value])
        self._count += 1
        if self._count > self.max_load * len(self._slots):
            self._resize()

    def get(self, key, default=-1):
        chain = self._slots[self._slot(key)]
        if chain is not None:
            for pair in chain:
                if self.track:
                    self.comparisons += 1
                if pair[0] == key:
                    return pair[1]
        return default

    def __contains__(self, key):
        return self.get(key, None) is not None

    def _resize(self):
        old = self._slots
        self._bits += 1
        self._slots = [None] * (1 << self._bits)
        for chain in old:
            if chain is not None:
                for key, value in chain:
                    i = self._slot(key)
                    if self._slots[i] is None:
                        self._slots[i] = [[key, value]]
                    else:
                        self._slots[i].append([key, value])

    def longest_chain(self):
        return max((len(c) for c in self._slots if c is not None), default=0)


def build_hash_table(keys):
    """Index every key by its position in the sequence."""
    table = HashTable()
    for i, key in enumerate(keys):
        table.put(key, i)
    return table
