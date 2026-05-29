"""Provider registry — maps source names to (SearchProvider, FetchProvider) pairs.

Self-registration pattern: each crawler module calls ``register()`` at import
time.  Auto-discovery scans ``leadradar.crawlers`` on module load, imports
every non-private submodule, and triggers registration.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import Callable

from leadradar.crawlers.base import FetchProvider, SearchProvider

logger = logging.getLogger(__name__)


# ── public types ─────────────────────────────────────────────────


@dataclass(frozen=True)
class ProviderFactory:
    """Callable pair that produces (search, fetch) provider instances."""

    search_factory: Callable[..., SearchProvider]
    fetch_factory: Callable[..., FetchProvider]


# ── internal state ───────────────────────────────────────────────


_REGISTRY: dict[str, ProviderFactory] = {}
_SCANNED = False


# ── public API ───────────────────────────────────────────────────


def register(
    source: str,
    search_factory: Callable[..., SearchProvider],
    fetch_factory: Callable[..., FetchProvider],
) -> None:
    """Register a data source.

    Called by each crawler module at import time.  Idempotent for identical
    factories (safe across ``importlib.reload``).
    """
    if source in _REGISTRY:
        existing = _REGISTRY[source]
        if existing.search_factory is search_factory and existing.fetch_factory is fetch_factory:
            return
        raise ValueError(f"Source '{source}' already registered")
    _REGISTRY[source] = ProviderFactory(search_factory, fetch_factory)
    logger.debug("Registered source '%s'", source)


def get_providers(source: str, **kwargs) -> tuple[SearchProvider, FetchProvider]:
    """Return (search, fetch) providers for the named source.

    Supported sources: "ccgp", "ggzy", "spc", "shandong", "guangdong", ...
    Raises ValueError for unknown source names.
    """
    _ensure_discovered()
    if source not in _REGISTRY:
        available = sorted(_REGISTRY.keys())
        raise ValueError(f"Unknown source '{source}'. Available: {available}")
    factory = _REGISTRY[source]
    return factory.search_factory(**kwargs), factory.fetch_factory(**kwargs)


def list_sources() -> list[str]:
    """Return all registered source names."""
    _ensure_discovered()
    return sorted(_REGISTRY.keys())


def reset_registry() -> None:
    """Reset registry to its post-discovery state.

    Clears all registrations and forces a full re-discover (reload) of every
    crawler module.  Used in tests for isolation.
    """
    global _SCANNED
    _REGISTRY.clear()
    _SCANNED = False
    _ensure_discovered(force=True)


# ── discovery ────────────────────────────────────────────────────


def _ensure_discovered(force: bool = False) -> None:
    """Auto-discover all crawler modules."""
    global _SCANNED
    if _SCANNED and not force:
        return
    _SCANNED = True

    import sys

    from leadradar import crawlers as pkg

    def _is_initializing(mod_name: str) -> bool:
        mod = sys.modules.get(mod_name)
        if mod is None:
            return False
        spec = getattr(mod, "__spec__", None)
        if spec is None:
            return False
        return getattr(spec, "_initializing", False)

    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        if name.startswith("_") or name == "registry":
            continue
        mod_name = f"leadradar.crawlers.{name}"
        try:
            if mod_name in sys.modules:
                if force and not _is_initializing(mod_name):
                    importlib.reload(sys.modules[mod_name])
                # else: skip already-loaded or currently-loading modules
            else:
                importlib.import_module(mod_name)
        except Exception as e:
            logger.warning("Failed to discover crawler module '%s': %s", mod_name, e)


# Eager discovery on module load (decision B)
_ensure_discovered()
