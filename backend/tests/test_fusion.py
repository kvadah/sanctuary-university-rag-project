"""Unit tests for Reciprocal Rank Fusion (pure, no services)."""
from app.retrieval.fusion import fuse_ranked_ids, reciprocal_rank_fusion


def test_item_ranked_high_in_both_lists_wins():
    dense = ["a", "b", "c"]
    lexical = ["b", "a", "d"]
    order = fuse_ranked_ids([dense, lexical])
    # "a" and "b" each appear near the top of both lists, beating single-list hits.
    assert set(order[:2]) == {"a", "b"}
    assert set(order) == {"a", "b", "c", "d"}


def test_single_list_items_still_surface():
    order = fuse_ranked_ids([["x"], ["y"]])
    assert set(order) == {"x", "y"}


def test_rank_one_beats_rank_two_within_a_list():
    scores = reciprocal_rank_fusion([["a", "b"]])
    assert scores["a"] > scores["b"]


def test_larger_k_compresses_rank_gap():
    low_k = reciprocal_rank_fusion([["a", "b"]], k=1)
    high_k = reciprocal_rank_fusion([["a", "b"]], k=1000)
    assert (low_k["a"] - low_k["b"]) > (high_k["a"] - high_k["b"])


def test_empty_input_is_empty():
    assert reciprocal_rank_fusion([]) == {}
    assert fuse_ranked_ids([]) == []
