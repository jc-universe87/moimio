"""Per-client rate limiting for public endpoints.

In memory, per process. The backend runs as a single uvicorn process
(backend/Dockerfile), so one dictionary sees every request. If it is ever
run with several workers, each enforces its own share of the limit.
"""

import ipaddress
import time
from collections import deque

from fastapi import Request


def client_ip(request: Request) -> str:
    """The address a request came from, as seen through the frontend proxy.

    The frontend's Caddy sets X-Real-IP to {client_ip}, which already looks
    past any reverse proxy on a private address in front of it (see
    frontend/Caddyfile). The header is only believed when the direct peer
    is itself on a private or loopback address, i.e. the request came
    through that proxy. A request that reaches the backend port directly
    from the internet is keyed on its own address and cannot choose
    someone else's by sending the header.
    """
    peer = request.client.host if request.client else ""
    forwarded = (request.headers.get("x-real-ip") or "").strip()
    if forwarded and _is_internal(peer):
        return forwarded
    return peer


def _is_internal(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback


class SlidingWindowLimiter:
    """At most `limit` hits per key within the last `window` seconds."""

    # Forget keys with no recent hits once this many are held, so a stream
    # of one-off addresses cannot grow the dictionary without bound.
    _PRUNE_AT = 10_000

    def __init__(self, window: float = 60.0):
        self.window = window
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key: str, limit: int) -> bool:
        """Record a hit for `key`. False when it is over the limit, in which
        case the hit is not recorded. A limit of 0 or less means no limit."""
        if limit <= 0:
            return True
        now = time.monotonic()
        cutoff = now - self.window
        if len(self._hits) >= self._PRUNE_AT:
            self._prune(cutoff)
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True

    def _prune(self, cutoff: float) -> None:
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]

    def reset(self) -> None:
        self._hits.clear()


registration_limiter = SlidingWindowLimiter(window=60.0)
