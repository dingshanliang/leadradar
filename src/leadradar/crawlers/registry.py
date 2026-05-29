"""Provider registry — maps source names to (SearchProvider, FetchProvider) pairs."""

from __future__ import annotations

from leadradar.crawlers.base import FetchProvider, SearchProvider

_PROVIDERS: dict[str, type] = {}


def _lazy_imports() -> dict[str, type]:
    if _PROVIDERS:
        return _PROVIDERS

    from leadradar.crawlers.ccgp import CCGPFetchProvider, CCGPSearchProvider
    from leadradar.crawlers.ggzy import GGZYFetchProvider, GGZYSearchProvider
    from leadradar.crawlers.spc import SPCFetchProvider, SPCSearchProvider
    from leadradar.crawlers.zycg import ZYCGFetchProvider, ZYCGSearchProvider
    from leadradar.crawlers.aqsc import AQSCFetchProvider, AQSCSearchProvider
    from leadradar.crawlers.provincial import (
        PROVINCES,
        ProvincialFetchProvider,
        ProvincialSearchProvider,
    )

    _PROVIDERS["ccgp"] = type(
        "CCGP",
        (),
        {"search": CCGPSearchProvider, "fetch": CCGPFetchProvider},
    )
    _PROVIDERS["ggzy"] = type(
        "GGZY",
        (),
        {"search": GGZYSearchProvider, "fetch": GGZYFetchProvider},
    )
    _PROVIDERS["spc"] = type(
        "SPC",
        (),
        {"search": SPCSearchProvider, "fetch": SPCFetchProvider},
    )
    _PROVIDERS["zycg"] = type(
        "ZYCG",
        (),
        {"search": ZYCGSearchProvider, "fetch": ZYCGFetchProvider},
    )
    _PROVIDERS["aqsc_mtyx"] = type(
        "AQSC",
        (),
        {"search": AQSCSearchProvider, "fetch": AQSCFetchProvider},
    )
    for prov in PROVINCES:
        _PROVIDERS[prov] = type(
            f"Provincial_{prov}",
            (),
            {
                "search": lambda province=prov, **kw: ProvincialSearchProvider(province, **kw),
                "fetch": lambda province=prov, **kw: ProvincialFetchProvider(province, **kw),
            },
        )
    return _PROVIDERS


def get_providers(
    source: str,
    *,
    delay_seconds: float | None = None,
    timeout: float | None = None,
) -> tuple[SearchProvider, FetchProvider]:
    """Return (search, fetch) providers for the named source.

    Supported sources: "ccgp", "ggzy", "spc", "shandong", "guangdong", "sichuan", ...
    Raises ValueError for unknown source names.
    """
    providers = _lazy_imports()
    if source not in providers:
        raise ValueError(
            f"Unknown source '{source}'. Available: {list(providers.keys())}"
        )

    cls = providers[source]
    search_kwargs: dict = {}
    fetch_kwargs: dict = {}
    if delay_seconds is not None:
        search_kwargs["delay_seconds"] = delay_seconds
        fetch_kwargs["delay_seconds"] = delay_seconds
    if timeout is not None:
        search_kwargs["timeout"] = timeout
        fetch_kwargs["timeout"] = timeout

    return cls.search(**search_kwargs), cls.fetch(**fetch_kwargs)
