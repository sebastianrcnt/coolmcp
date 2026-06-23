"""Tiny in-process TTL cache for Naver responses.

Naver rate-limits aggressively (HTTP 429 under bursts), and agents often
re-request the same place — e.g. search_places(enrich=True) fans out detail
fetches, then the agent calls get_place_detail on one of them again. Caching
results briefly cuts latency, duplicate work, and 429s.

Keyed by the SEMANTIC arguments (query/coords/place_id), not by cookies: public
place data does not change with the session. Disable with NAVER_CACHE=0; tune
with NAVER_CACHE_TTL (seconds, default 120).
"""

import os
import time
from typing import Any, Awaitable, Callable, Hashable

_store: dict[Hashable, tuple[float, Any]] = {}


def _enabled() -> bool:
    return os.environ.get("NAVER_CACHE", "1").lower() not in ("0", "false", "no")


def default_ttl() -> float:
    try:
        return float(os.environ.get("NAVER_CACHE_TTL", "120"))
    except ValueError:
        return 120.0


async def get_or_set(
    key: Hashable,
    factory: Callable[[], Awaitable[Any]],
    ttl: float | None = None,
) -> Any:
    """Return a cached value for `key`, or await `factory()` and cache it.

    No per-key locking: a cache miss under concurrency may run `factory` more
    than once, which is harmless (idempotent reads) and avoids lock complexity.
    """
    if not _enabled():
        return await factory()

    now = time.monotonic()
    hit = _store.get(key)
    if hit is not None and hit[0] > now:
        return hit[1]

    value = await factory()
    _store[key] = (now + (default_ttl() if ttl is None else ttl), value)
    return value


def clear() -> None:
    """Drop all cached entries (e.g. in tests or after a known data change)."""
    _store.clear()
