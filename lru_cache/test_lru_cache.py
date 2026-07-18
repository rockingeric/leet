import pytest

from lru_cache import LRUCache


@pytest.fixture
def cache():
    return LRUCache(2)


def _list_len(cache):
    count, cur = 0, cache.list.root
    while cur:
        count += 1
        cur = cur.next
    return count


@pytest.mark.parametrize("key, expected", [("a", 1), ("missing", None)])
def test_get_hit_and_miss(cache, key, expected):
    cache.put("a", 1)
    assert cache.get(key) == expected


def test_capacity_never_exceeded(cache):
    for i in range(100):
        cache.put(i, i)
        assert len(cache.nodes) <= 2
        assert _list_len(cache) == len(cache.nodes)


def test_recency_order_evicts_lru(cache):
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_update_existing_key_no_duplicate_node(cache):
    cache.put("k", 1)
    cache.put("k", 2)
    assert cache.get("k") == 2
    assert len(cache.nodes) == 1
    assert _list_len(cache) == 1
