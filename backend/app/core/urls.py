"""Public-facing URL derivation.

Email links (registration confirmation, password reset, etc.) are built
from the base URL the user actually hit, not from a pinned environment
variable. Reasons:

  - Self-hosters deploy onto whatever domain they own. The scaffold
    shouldn't require them to hand-configure a URL env var for basic
    functionality to work.
  - Container-per-tenant SaaS deployments (each tenant on their own
    backend at <tenant>.moimio.app) still benefit from this: a single
    image build serves any subdomain the operator points at it without
    a per-tenant URL config step.
  - Operator ergonomics: one fewer piece of configuration to get right.

Derivation order:
  1. X-Forwarded-Proto + X-Forwarded-Host — set by Caddy's reverse_proxy
     on every backend request in our standard deployment, and the
     convention any sane reverse proxy uses. Covers the Cloudflare
     tunnel case, LAN-IP deploys, any reverse-proxied topology.
  2. request.url.scheme + the raw Host header — direct uvicorn access
     during local dev without Caddy in front.
  3. request.base_url — last-resort synthesised by Starlette; kept so
     the function always returns *something* rather than raising.

Security note: this pattern trusts the Host header that reaches the
backend. In our deployment the backend port is not exposed outside the
Docker network, so only Caddy (which we control) ever sets these
headers. If a future deployment exposes the backend directly, a
trusted-host allowlist would be a sensible hardening step — but we'll
cross that when we get there.
"""

from fastapi import Request


def get_app_base_url(request: Request) -> str:
    """Return the public-facing base URL for this request (no trailing slash)."""
    # Prefer reverse-proxy-set headers — take the first value if the
    # header is comma-separated (chained proxies).
    xf_host = request.headers.get("x-forwarded-host")
    if xf_host:
        xf_proto = request.headers.get("x-forwarded-proto") or request.url.scheme
        proto = xf_proto.split(",")[0].strip()
        host = xf_host.split(",")[0].strip()
        return f"{proto}://{host}".rstrip("/")

    # Direct connection (local dev without Caddy). Use the scheme the
    # request came in on and the raw Host header.
    host_header = request.headers.get("host")
    if host_header:
        return f"{request.url.scheme}://{host_header}".rstrip("/")

    # Synthesised fallback — Starlette always produces something here.
    return str(request.base_url).rstrip("/")
