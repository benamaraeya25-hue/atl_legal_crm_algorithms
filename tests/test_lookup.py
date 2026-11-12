import random

from caselaw.instrument import count_search_comparisons, CountedInt
from caselaw.lookup import HashTable, binary_search, build_hash_table, linear_search


def test_linear_and_binary_agree_with_membership():
    rng = random.Random(3)
    items = sorted(rng.sample(range(10_000), 500))
    for target in rng.sample(range(10_000), 200):
        expected = items.index(target) if target in items else -1
        assert linear_search(items, target) == expected
        assert binary_search(items, target) == expected


def test_search_edge_cases():
    assert linear_search([], 1) == -1
    assert binary_search([], 1) == -1
    assert binary_search([4], 4) == 0
    assert binary_search([4], 5) == -1
    assert binary_search([1, 2, 3, 4], 1) == 0
    assert binary_search([1, 2, 3, 4], 4) == 3


def test_hash_table_put_get_update_and_missing():
    t = HashTable()
    t.put("a", 1)
    t.put("b", 2)
    t.put("a", 3)                       # update, not a second entry
    assert len(t) == 2
    assert t.get("a") == 3 and t.get("b") == 2
    assert t.get("zzz") == -1
    assert t.get("zzz", "none") == "none"
    assert "a" in t and "zzz" not in t


def test_hash_table_resizes_and_keeps_every_item():
    t = HashTable(capacity=16)
    n = 5000
    for i in range(n):
        t.put(i * 7919, i)
    assert len(t) == n
    assert t.capacity > 16
    assert t.load_factor <= t.max_load
    assert all(t.get(i * 7919) == i for i in range(n))


def test_hash_table_handles_forced_collisions():
    class Collide:
        def __init__(self, v):
            self.v = v

        def __hash__(self):
            return 42                   # every key hashes the same

        def __eq__(self, other):
            return self.v == other.v

    t = HashTable()
    for i in range(50):
        t.put(Collide(i), i)
    assert all(t.get(Collide(i)) == i for i in range(50))
    assert t.longest_chain() == 50


def test_packed_keys_spread_across_the_table():
    # keys shaped like data.pack_key output: date * 1e9 + case * 1e5 + passage
    keys = [20000000 * 10 ** 9 + c * 10 ** 5 + s for c in range(200) for s in range(25)]
    t = build_hash_table(keys)
    assert t.longest_chain() <= 12


def test_search_comparison_counts():
    items = [CountedInt(i) for i in range(1024)]
    assert count_search_comparisons(linear_search, items, 1023) == 1024        # worst case
    assert count_search_comparisons(binary_search, items, 1023) <= 2 * 11 + 2  # ~2 log2 n
