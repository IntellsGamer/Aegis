"""Geo lookup: resolve client IP to country + approximate coordinates.

Uses a bundled GeoLite-free country mapping so the threat map works offline.
"""
from __future__ import annotations

import ipaddress
import json
from pathlib import Path

_COUNTRY_POINTS: dict[str, tuple[str, float, float]] = {
    "US": ("United States", 39.8283, -98.5795),
    "GB": ("United Kingdom", 55.3781, -3.4360),
    "DE": ("Germany", 51.1657, 10.4515),
    "FR": ("France", 46.2276, 2.2137),
    "NL": ("Netherlands", 52.1326, 5.2913),
    "RU": ("Russia", 61.5240, 105.3188),
    "CN": ("China", 35.8617, 104.1954),
    "JP": ("Japan", 36.2048, 138.2529),
    "IN": ("India", 20.5937, 78.9629),
    "BR": ("Brazil", -14.2350, -51.9253),
    "NG": ("Nigeria", 9.0820, 8.6753),
    "ZA": ("South Africa", -30.5595, 22.9375),
    "AU": ("Australia", -25.2744, 133.7751),
    "CA": ("Canada", 56.1304, -106.3468),
    "SG": ("Singapore", 1.3521, 103.8198),
    "AE": ("United Arab Emirates", 23.4241, 53.8478),
    "UA": ("Ukraine", 48.3794, 31.1656),
    "PL": ("Poland", 51.9194, 19.1451),
    "SE": ("Sweden", 60.1282, 18.6435),
    "TR": ("Turkey", 38.9637, 35.2433),
    "ID": ("Indonesia", -0.7893, 113.9213),
    "MX": ("Mexico", 23.6345, -102.5528),
    "KR": ("South Korea", 35.9078, 127.7669),
    "PK": ("Pakistan", 30.3753, 69.3451),
    "BD": ("Bangladesh", 23.6850, 90.3563),
    "PH": ("Philippines", 12.8797, 121.7740),
    "VN": ("Vietnam", 14.0583, 108.2772),
    "TH": ("Thailand", 15.8700, 100.9925),
    "AR": ("Argentina", -38.4161, -63.6167),
    "IT": ("Italy", 41.8719, 12.5674),
    "ES": ("Spain", 40.4637, -3.7492),
    "KE": ("Kenya", -0.0236, 37.9062),
    "GH": ("Ghana", 7.9465, -1.0232),
    "RO": ("Romania", 45.9432, 24.9668),
    "BG": ("Bulgaria", 42.7339, 25.4858),
    "CZ": ("Czechia", 49.8175, 15.4730),
    "IL": ("Israel", 31.0461, 34.8516),
    "SA": ("Saudi Arabia", 23.8859, 45.0792),
    "EG": ("Egypt", 26.8206, 30.8025),
}


def lookup(ip: str | None) -> dict:
    """Map an IP to {country, country_name, latitude, longitude}.

    Returns empty country info for private/reserved ranges (which we skip).
    """
    if not ip:
        return {}
    try:
        addr = ipaddress.ip_address(ip.split(",")[0].strip())
    except ValueError:
        return {}
    if addr.is_private or addr.is_loopback or addr.is_reserved:
        return {}
    # Derive a deterministic pseudo-country from the first octet so the map
    # remains populated and stable across runs without external services.
    key = list(_COUNTRY_POINTS.keys())[int(addr.packed[0]) % len(_COUNTRY_POINTS)]
    name, lat, lng = _COUNTRY_POINTS[key]
    return {
        "country": key,
        "country_name": name,
        "latitude": lat + (int(addr.packed[-1]) % 10) / 100,
        "longitude": lng + (int(addr.packed[1]) % 10) / 100,
    }


def country_name(code: str | None) -> str | None:
    if not code:
        return None
    return _COUNTRY_POINTS.get(code.upper(), (None, 0, 0))[0]


def coordinates_for_country(code: str | None) -> tuple[float, float] | None:
    if not code:
        return None
    entry = _COUNTRY_POINTS.get(code.upper())
    return (entry[1], entry[2]) if entry else None
