"""SSRF-safe, bounded HTTP acquisition for untrusted scan targets.

The URL scanner deals with adversarial input.  Lexical inspection is harmless,
but DNS, TLS, HTML, robots, and favicon requests must never reach localhost,
private networks, cloud metadata endpoints, or arbitrary services behind a
redirect.  This module centralizes that policy and is intentionally used by
all remote fetch helpers.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

from app.config import settings


class UnsafeDestination(ValueError):
    """A scan target is not safe for server-side network acquisition."""


class UnresolvedDestination(UnsafeDestination):
    """A hostname could not be resolved, so acquisition cannot be completed."""


@dataclass(frozen=True)
class ValidatedURL:
    url: str
    host: str
    port: int
    addresses: tuple[str, ...]


def _is_public_address(raw: str) -> bool:
    address = ipaddress.ip_address(raw)
    # `is_global` excludes loopback, private, link-local, multicast, reserved,
    # unspecified, and carrier-grade/special-purpose ranges in supported Python
    # releases. IPv4-mapped IPv6 gets evaluated as its IPv4 address too.
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return bool(address.is_global)


def _resolve_public_addresses(host: str, port: int) -> tuple[str, ...]:
    try:
        answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnresolvedDestination(f"Destination hostname could not be resolved: {host}") from exc

    addresses = tuple(sorted({item[4][0] for item in answers}))
    if not addresses:
        raise UnresolvedDestination(f"Destination hostname has no usable address: {host}")
    blocked = [address for address in addresses if not _is_public_address(address)]
    if blocked:
        raise UnsafeDestination(
            f"Destination resolves to a non-public network address: {', '.join(blocked[:3])}"
        )
    return addresses


def validate_public_url(raw_url: str) -> ValidatedURL:
    """Validate a web URL and all current DNS answers before connecting.

    Non-default ports are rejected because the scanner is a web-content
    analyzer, not a general-purpose network probe. Each redirect goes through
    this function again in :func:`fetch_public_url`.
    """
    parsed = urlparse(raw_url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeDestination("Only HTTP and HTTPS destinations can be scanned")
    if not parsed.hostname:
        raise UnsafeDestination("The destination URL has no hostname")
    if parsed.username or parsed.password:
        raise UnsafeDestination("Credentials embedded in a URL are not supported")

    host = parsed.hostname.rstrip(".").lower()
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    except ValueError as exc:
        raise UnsafeDestination("The destination URL has an invalid port") from exc
    if port not in {80, 443}:
        raise UnsafeDestination("Only standard HTTP(S) ports are allowed for remote scanning")

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and not _is_public_address(str(literal)):
        raise UnsafeDestination("Private, loopback, reserved, and link-local IP targets are blocked")

    addresses = _resolve_public_addresses(host, port)
    return ValidatedURL(url=raw_url, host=host, port=port, addresses=addresses)


def _read_limited(response: httpx.Response, max_bytes: int) -> bytes:
    content_length = response.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise UnsafeDestination("Remote response exceeds the configured scan size limit")
        except ValueError:
            pass

    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_bytes():
        size += len(chunk)
        if size > max_bytes:
            raise UnsafeDestination("Remote response exceeds the configured scan size limit")
        chunks.append(chunk)
    return b"".join(chunks)


def fetch_public_url(
    url: str,
    *,
    accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    max_bytes: int | None = None,
    max_redirects: int | None = None,
) -> dict:
    """Fetch a public HTTP(S) resource with validation at every redirect.

    This deliberately avoids automatic redirects. A new destination is checked
    before every request, which keeps redirectors from bypassing URL policy.
    The caller receives a normalized, bounded response payload and redirect
    chain; the raw network client never leaks outside this module.
    """
    limit = max_bytes or settings.max_remote_response_bytes
    redirect_limit = max_redirects if max_redirects is not None else settings.max_redirects
    current = url
    chain: list[str] = []

    with httpx.Client(
        timeout=httpx.Timeout(settings.http_timeout),
        follow_redirects=False,
        headers={"User-Agent": settings.user_agent, "Accept": accept},
        verify=True,
    ) as client:
        for _ in range(redirect_limit + 1):
            validated = validate_public_url(current)
            try:
                with client.stream("GET", validated.url) as response:
                    body = _read_limited(response, limit)
                    status = response.status_code
                    headers = dict(response.headers)
                    response_url = str(response.url)
            except httpx.HTTPError as exc:
                raise UnsafeDestination(f"Remote request failed safely: {exc}") from exc

            chain.append(response_url)
            if status not in {301, 302, 303, 307, 308}:
                return {
                    "status": status,
                    "url": response_url,
                    "headers": headers,
                    "content": body,
                    "redirect_chain": chain,
                    "resolved_addresses": list(validated.addresses),
                }

            location = headers.get("location")
            if not location:
                return {
                    "status": status,
                    "url": response_url,
                    "headers": headers,
                    "content": body,
                    "redirect_chain": chain,
                    "resolved_addresses": list(validated.addresses),
                }
            current = urljoin(response_url, location)

    raise UnsafeDestination("Remote destination exceeded the configured redirect limit")
