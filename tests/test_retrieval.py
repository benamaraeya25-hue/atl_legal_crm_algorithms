import random

from caselaw import data
from caselaw.retrieval import (InvertedIndex, decode, parse_query, rank_key,
                               search_index_heap, search_index_sort, search_naive,
                               select_heap, select_sort, tokenize)

TEXTS = [
    "The Court held that due process requires notice.",
    "Equal protection of the laws applies to every person.",
    "Due process and equal protection are both guaranteed.",
    "The judgment of the court below is affirmed.",
    "Habeas corpus relief was denied by the court.",
    "Court court court: the court said so.",
    "No relevant words in this passage at all here.",
]
LOWER = [t.lower() for t in TEXTS]


def test_tokenize_and_parse_query():
    assert tokenize("Due Process, equal-protection!") == ["due", "process", "equal", "protection"]
    assert parse_query("Court court COURT habeas") == ["court", "habeas"]
    assert parse_query("   ") == []


def test_rank_key_orders_by_score_then_passage_id():
    keys = [rank_key(2, 5), rank_key(9, 7), rank_key(9, 3), rank_key(1, 0)]
    assert [decode(k) for k in sorted(keys)] == [(3, 9), (7, 9), (5, 2), (0, 1)]


def test_known_query_results():
    index = InvertedIndex.build(LOWER)
    # 'court' appears 1x in 0, 1x in 3, 1x in 4, and 4x in 5
    assert search_index_heap(index, ["court"], 3) == [(5, 4), (0, 1), (3, 1)]
    # two-word query: passage 2 has due+process+equal+protection... only due/process counted
    assert search_index_sort(index, ["due", "process"], 2) == [(0, 2), (2, 2)]
    assert search_index_sort(index, ["nonexistentword"], 5) == []


def test_three_approaches_agree_on_small_corpus():
    index = InvertedIndex.build(LOWER)
    for query in (["court"], ["due", "process"], ["equal", "protection", "court"], ["habeas"]):
        for k in (1, 2, 10):
            a = search_naive(LOWER, query, k)
            b = search_index_sort(index, query, k)
            c = search_index_heap(index, query, k)
            assert a == b == c


def test_three_approaches_agree_on_random_corpus():
    rng = random.Random(8)
    vocab = [f"w{i}" for i in range(60)]
    lowered = [" ".join(rng.choice(vocab) for _ in range(rng.randint(3, 25))) for _ in range(800)]
    index = InvertedIndex.build(lowered)
    for _ in range(40):
        query = rng.sample(vocab, rng.randint(1, 3))
        k = rng.choice([1, 5, 10, 50])
        a = search_naive(lowered, query, k)
        assert a == search_index_sort(index, query, k) == search_index_heap(index, query, k)


def test_select_heap_matches_sort_for_any_k():
    rng = random.Random(5)
    keys = [rng.randint(0, 10 ** 6) for _ in range(500)]
    for k in (1, 3, 10, 499, 500, 900):
        assert select_heap(keys, k) == select_sort(keys, k) == sorted(keys)[:k]


def test_select_heap_on_few_candidates():
    assert select_heap([], 5) == []
    assert select_heap([9, 2], 5) == [2, 9]


def test_data_helpers():
    passages = data.split_passages("Short. This sentence is long enough to keep around. Another long enough sentence follows here!")
    assert passages == ["This sentence is long enough to keep around.",
                        "Another long enough sentence follows here!"]
    key = data.pack_key("1946-11-18", 12, 345)
    assert data.unpack_key(key) == (19461118, 12, 345)
    assert data.pack_key("1946-11-18", 12, 345) < data.pack_key("1946-11-19", 0, 0)
    assert data.pack_key("1946-11-18", 12, 345) < data.pack_key("1946-11-18", 13, 0)
