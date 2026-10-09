"""Unit tests for Query Cache (Task T16)."""

import pytest
from cache import QueryCache


def test_cache_normalization():
    q1 = "What is the notice period policy?"
    q2 = "   what is the notice   period policy?  "
    q3 = "What is the notice period policy??!"

    assert QueryCache.normalize_query(q1) == "what is the notice period policy"
    assert QueryCache.normalize_query(q2) == "what is the notice period policy"
    assert QueryCache.normalize_query(q3) == "what is the notice period policy"

    assert QueryCache.generate_key(q1) == QueryCache.generate_key(q2)
    assert QueryCache.generate_key(q2) == QueryCache.generate_key(q3)


def test_cache_hit_and_miss():
    cache = QueryCache()
    q = "What is the probation period?"

    # Miss
    assert cache.get(q) is None
    assert cache.misses == 1

    # Store
    cache.set(q, {"answer": "Six months probation"})
    assert cache.stats()["entries_count"] == 1

    # Hit
    val = cache.get("   what is the probation period?   ")
    assert val is not None
    assert val["answer"] == "Six months probation"
    assert cache.hits == 1


def test_cache_dynamic_bypass():
    cache = QueryCache()
    dyn_q = "Check status of application APP-00012."
    assert cache.is_dynamic_query(dyn_q) is True

    # Attempt to set dynamic query
    cache.set(dyn_q, {"status": "Offered"})
    # Must bypass and remain None
    assert cache.get(dyn_q) is None
    assert cache.stats()["entries_count"] == 0
