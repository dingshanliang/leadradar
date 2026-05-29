"""Tests for CCGP crawler — uses fixtures, no real network access."""

from __future__ import annotations


from leadradar.crawlers.ccgp import _parse_search_results

# Simulated CCGP search result HTML (matches real structure)
_SEARCH_HTML = """
<div class="vT-srch-result">
  <ul class="vT-srch-result-list-bid">
    <li>
      <a href="http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202602/t20260209_26164260.htm">
        稷山AI智能包装设计平台的采购公告
      </a>
      <p>项目概况稷山AI智能包装设计平台招标项目，预算金额180万元。</p>
      <span>2026.02.09 20:05:17 | 采购人：稷山县工业信息化和科技局 | 代理机构：致君项目管理有限公司
        <br/><strong>公开招标公告</strong> | 山西
      </span>
    </li>
    <li>
      <a href="http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202602/t20260202_26142160.htm">
        品牌建设推广营销项目（扩大品牌曝光度、品牌LOGO及包装设计）
      </a>
      <p>品牌建设推广营销项目招标，预算金额250万元。</p>
      <span>2026.02.02 17:45:05 | 采购人：宁都县农业农村局
        <br/><strong>公开招标公告</strong> | 江西
      </span>
    </li>
  </ul>
</div>
"""


def test_parse_search_results_extracts_items():
    results = _parse_search_results(_SEARCH_HTML)
    assert len(results) == 2


def test_parse_search_results_title():
    results = _parse_search_results(_SEARCH_HTML)
    assert "包装设计" in results[0].title
    assert "品牌" in results[1].title


def test_parse_search_results_url():
    results = _parse_search_results(_SEARCH_HTML)
    assert results[0].url.startswith("http://www.ccgp.gov.cn/")
    assert "t20260209" in results[0].url


def test_parse_search_results_snippet():
    results = _parse_search_results(_SEARCH_HTML)
    assert results[0].snippet is not None
    assert "180万元" in results[0].snippet


def test_parse_search_results_date():
    results = _parse_search_results(_SEARCH_HTML)
    assert results[0].published_at == "2026-02-09"
    assert results[1].published_at == "2026-02-02"


def test_parse_search_results_empty_html():
    results = _parse_search_results("<html><body></body></html>")
    assert results == []


def test_parse_search_results_limit():
    results = _parse_search_results(_SEARCH_HTML)
    assert results[:1]  # Can slice to limit
