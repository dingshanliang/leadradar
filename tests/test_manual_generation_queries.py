from leadradar.services.manual_generation_queries import expand_queries


def test_expand_queries_by_group():
    queries = expand_queries("by_group")
    assert len(queries) >= 1
    assert queries[0]["keyword_group"] == "region_brand"
    assert queries[0]["keyword"] is None
    assert "区域公用品牌" in queries[0]["query"]


def test_expand_queries_by_keyword_has_more_items():
    group_queries = expand_queries("by_group")
    keyword_queries = expand_queries("by_keyword")
    assert len(keyword_queries) > len(group_queries)
    assert keyword_queries[0]["keyword"] is not None
