"""Tests for the self-registration provider registry."""

from __future__ import annotations

import pytest

from leadradar.crawlers.base import FetchProvider, SearchProvider
from leadradar.crawlers.ccgp import CCGPFetchProvider, CCGPSearchProvider
from leadradar.crawlers.plap import PLAPFetchProvider, PLAPSearchProvider
from leadradar.crawlers.provincial import (
    PROVINCES,
    ProvincialFetchProvider,
    ProvincialSearchProvider,
)
from leadradar.crawlers.registry import (
    ProviderFactory,
    _REGISTRY,
    get_providers,
    list_sources,
    register,
    reset_registry,
)


# ── fixtures ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _cleanup_registry():
    """Restore registry state after each test."""
    original = dict(_REGISTRY)
    yield
    _REGISTRY.clear()
    _REGISTRY.update(original)


class _MockSearchProvider(SearchProvider):
    def __init__(self, *, custom_param: str = "default"):
        self.custom_param = custom_param

    async def search(self, query: str, *, limit: int = 20) -> list:
        return []


class _MockFetchProvider(FetchProvider):
    def __init__(self, *, custom_param: str = "default"):
        self.custom_param = custom_param

    async def fetch(self, url: str):
        from leadradar.crawlers.base import RawPage

        return RawPage(url=url, status_code=200, content_type=None, text="")


# ── get_providers ────────────────────────────────────────────────


class TestGetProviders:
    def test_ccgp_returns_correct_types(self):
        search, fetch = get_providers("ccgp")
        assert isinstance(search, CCGPSearchProvider)
        assert isinstance(fetch, CCGPFetchProvider)

    def test_plap_returns_correct_types(self):
        search, fetch = get_providers("plap")
        assert isinstance(search, PLAPSearchProvider)
        assert isinstance(fetch, PLAPFetchProvider)

    def test_provincial_returns_correct_types(self):
        search, fetch = get_providers("shandong")
        assert isinstance(search, ProvincialSearchProvider)
        assert isinstance(fetch, ProvincialFetchProvider)
        assert search._config.name == "山东省政府采购网"

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown source 'nonexistent'"):
            get_providers("nonexistent")

    def test_kwargs_passed_to_provider(self):
        """get_providers should forward kwargs to the provider constructors."""
        search, fetch = get_providers("ccgp", delay_seconds=1.5, timeout=10.0)
        assert search._delay == 1.5
        assert search._timeout == 10.0
        assert fetch._delay == 1.5
        assert fetch._timeout == 10.0

    def test_plap_delay_seconds_kwarg(self):
        """PLAP provider accepts delay_seconds kwarg."""
        search, _fetch = get_providers("plap", delay_seconds=7.0)
        assert search._delay == 7.0


# ── list_sources ─────────────────────────────────────────────────


class TestListSources:
    def test_includes_all_provinces(self):
        sources = list_sources()
        for prov in PROVINCES:
            assert prov in sources

    def test_includes_standard_sources(self):
        sources = list_sources()
        for name in ("ccgp", "ggzy", "spc", "zycg", "aqsc_mtyx", "greenfood", "plap"):
            assert name in sources

    def test_returns_sorted_list(self):
        sources = list_sources()
        assert sources == sorted(sources)


# ── register ─────────────────────────────────────────────────────


class TestRegister:
    def test_new_source_is_registered(self):
        register("mock_test", _MockSearchProvider, _MockFetchProvider)
        search, fetch = get_providers("mock_test")
        assert isinstance(search, _MockSearchProvider)
        assert isinstance(fetch, _MockFetchProvider)

    def test_duplicate_registration_raises(self):
        register("mock_dup", _MockSearchProvider, _MockFetchProvider)
        with pytest.raises(ValueError, match="already registered"):
            register("mock_dup", CCGPSearchProvider, CCGPFetchProvider)


# ── reset_registry ───────────────────────────────────────────────


class TestResetRegistry:
    def test_reset_restores_registry(self):
        assert "ccgp" in _REGISTRY
        reset_registry()
        # reset_registry triggers immediate re-discovery (reloads modules)
        assert "ccgp" in _REGISTRY
        search, fetch = get_providers("ccgp")
        # Note: after reload, isinstance against the *original* class fails
        # because reload creates a new class object.  Check by name instead.
        assert type(search).__name__ == "CCGPSearchProvider"
        assert type(fetch).__name__ == "CCGPFetchProvider"


# ── ProviderFactory ──────────────────────────────────────────────


class TestProviderFactory:
    def test_frozen_dataclass(self):
        factory = ProviderFactory(
            search_factory=_MockSearchProvider,
            fetch_factory=_MockFetchProvider,
        )
        with pytest.raises(AttributeError):
            factory.search_factory = CCGPSearchProvider  # type: ignore[misc]
