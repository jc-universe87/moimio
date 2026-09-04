"""Outbound webhook URL policy (v1.0.4a).

Refuses webhook targets that point inside the network the server sits
on. Without this, anyone who can create a webhook endpoint (a super
admin, or anyone holding a leaked admin session) can make this server
issue HTTP requests to addresses only it can reach: the SaaS control
plane on the private network, the Caddy admin API, cloud metadata
services, or the database itself. That class of attack is called SSRF
(server-side request forgery).

Two call sites:
- `app.api.outbound_webhooks` on create and update (HTTP 422 with key
  `errors.webhooks.url_not_allowed`), so the admin gets immediate
  feedback.
- `app.services.webhook_service._attempt_delivery` immediately before
  each send, for user-managed endpoints only. A hostname can be
  re-pointed at a private address after the endpoint was created (DNS
  rebinding), so the check at creation time is necessary but not
  sufficient. SaaS-managed endpoints are exempt: the control plane
  registers its own receiver on the private network by design, and
  tenant admins cannot create or edit those.

What is refused: http(s) only; `localhost` and `*.localhost`; any
literal IP, or any address the hostname resolves to, that is private
(RFC 1918), loopback, link-local (which covers the cloud metadata
address 169.254.169.254), carrier-grade NAT 100.64.0.0/10 (Tailscale
lives there), multicast, reserved, unspecified, or the IPv6 equivalents
including IPv4-mapped forms. If the hostname resolves to several
addresses and any one of them is refused, the URL is refused.

A hostname that does not resolve at all is allowed through: it cannot
reach anything, delivery will fail on its own and be recorded normally,
and refusing it would break the common case of an admin registering an
endpoint a few minutes before its DNS record is live.

Residual risk, stated plainly: the delivery-time check resolves the
name, and the HTTP client then resolves it again for the connection. A
rebinding attack that flips the answer in that gap of a few
milliseconds is not stopped here. Closing it fully means pinning the
connection to the checked address, which is a larger change and is on
the backlog.

Self-hosters who legitimately deliver to an internal tool on their own
network can set WEBHOOK_ALLOW_PRIVATE_TARGETS=true. It is never set by
the hosted edition.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

from app.core.config import get_settings

# Address blocks refused in addition to what the `ipaddress` module
# already classifies as private, loopback, link-local, etc. Python's
# `is_private` does not cover carrier-grade NAT, and the benchmarking
# and "this host" blocks are never legitimate webhook targets.
_EXTRA_FORBIDDEN_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
    ipaddress.ip_network("100.64.0.0/10"),   # CGNAT / Tailscale
    ipaddress.ip_network("198.18.0.0/15"),   # benchmarking
    ipaddress.ip_network("192.0.0.0/24"),    # IETF protocol assignments
    ipaddress.ip_network("0.0.0.0/8"),       # "this" network
)


class WebhookUrlRejected(ValueError):
    """Raised when a webhook URL may not be used as a delivery target.

    `reason` is a short machine-readable token, never user-facing text:
    scheme | host | private
    """

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"webhook url rejected ({reason}): {detail}")


def _resolve(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Every address the hostname currently resolves to, deduplicated.

    Module-level so tests can monkeypatch it and stay off the network.
    Returns an empty list when the name does not resolve.
    """
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, ValueError):
        return []
    addrs: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    for _family, _type, _proto, _canon, sockaddr in infos:
        try:
            addrs.add(ipaddress.ip_address(sockaddr[0]))
        except ValueError:
            continue
    return sorted(addrs, key=str)


def is_forbidden_address(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True if a webhook must not be delivered to this address."""
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped
    if (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    ):
        return True
    if isinstance(addr, ipaddress.IPv6Address) and addr.is_site_local:
        return True
    return any(addr in net for net in _EXTRA_FORBIDDEN_NETWORKS if net.version == addr.version)


def check_webhook_url(url: str, *, allow_private: bool | None = None) -> None:
    """Raise WebhookUrlRejected if `url` is not an acceptable target.

    `allow_private` defaults to the WEBHOOK_ALLOW_PRIVATE_TARGETS setting.
    Even when private targets are allowed, the scheme must still be
    http or https and the URL must carry a host.
    """
    if allow_private is None:
        allow_private = get_settings().webhook_allow_private_targets

    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https"):
        raise WebhookUrlRejected("scheme", parts.scheme)

    host = parts.hostname  # lower-cased, brackets stripped from IPv6 literals
    if not host:
        raise WebhookUrlRejected("host", "missing")

    if allow_private:
        return

    host = host.rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        raise WebhookUrlRejected("host", host)

    try:
        addrs: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = [
            ipaddress.ip_address(host)
        ]
    except ValueError:
        addrs = _resolve(host)

    for addr in addrs:
        if is_forbidden_address(addr):
            raise WebhookUrlRejected("private", f"{host} -> {addr}")
