"""Provenance-safe optional GeoIP enrichment.

AEGIS must never invent a country or coordinate from an IP address. If an
operator installs a licensed/local GeoIP City database and configures its path,
this module returns the country and the provider's coarse coordinates. Without
that source, it returns no location; public maps can still aggregate approved
reports that carry an independently verified country.
"""
from __future__ import annotations

import ipaddress
from pathlib import Path

from app.config import settings

# Country centroids are display anchors for country-level aggregates, never a
# claimed incident or victim location. The map API marks them accordingly.
_COUNTRY_CENTROIDS: dict[str, tuple[str, float, float]] = {
    "US": ("United States", 39.8283, -98.5795), "GB": ("United Kingdom", 55.3781, -3.4360),
    "DE": ("Germany", 51.1657, 10.4515), "FR": ("France", 46.2276, 2.2137),
    "NL": ("Netherlands", 52.1326, 5.2913), "RU": ("Russia", 61.5240, 105.3188),
    "CN": ("China", 35.8617, 104.1954), "JP": ("Japan", 36.2048, 138.2529),
    "IN": ("India", 20.5937, 78.9629), "BR": ("Brazil", -14.2350, -51.9253),
    "NG": ("Nigeria", 9.0820, 8.6753), "ZA": ("South Africa", -30.5595, 22.9375),
    "AU": ("Australia", -25.2744, 133.7751), "CA": ("Canada", 56.1304, -106.3468),
    "SG": ("Singapore", 1.3521, 103.8198), "AE": ("United Arab Emirates", 23.4241, 53.8478),
    "UA": ("Ukraine", 48.3794, 31.1656), "PL": ("Poland", 51.9194, 19.1451),
    "SE": ("Sweden", 60.1282, 18.6435), "TR": ("Türkiye", 38.9637, 35.2433),
    "ID": ("Indonesia", -0.7893, 113.9213), "MX": ("Mexico", 23.6345, -102.5528),
    "KR": ("South Korea", 35.9078, 127.7669), "PK": ("Pakistan", 30.3753, 69.3451),
    "BD": ("Bangladesh", 23.6850, 90.3563), "PH": ("Philippines", 12.8797, 121.7740),
    "VN": ("Vietnam", 14.0583, 108.2772), "TH": ("Thailand", 15.8700, 100.9925),
    "AR": ("Argentina", -38.4161, -63.6167), "IT": ("Italy", 41.8719, 12.5674),
    "ES": ("Spain", 40.4637, -3.7492), "KE": ("Kenya", -0.0236, 37.9062),
    "GH": ("Ghana", 7.9465, -1.0232), "RO": ("Romania", 45.9432, 24.9668),
    "BG": ("Bulgaria", 42.7339, 25.4858), "CZ": ("Czechia", 49.8175, 15.4730),
    "IL": ("Israel", 31.0461, 34.8516), "SA": ("Saudi Arabia", 23.8859, 45.0792),
    "EG": ("Egypt", 26.8206, 30.8025), "IR": ("Iran", 32.4279, 53.6880),
}


def _public_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    try:
        address = ipaddress.ip_address(ip.split(",")[0].strip())
    except ValueError:
        return None
    return str(address) if address.is_global else None


def lookup(ip: str | None) -> dict:
    """Return optional real GeoIP enrichment or an empty result.

    `AEGIS_GEOIP_CITY_DB` must point at a local MaxMind-compatible MMDB file.
    No network lookup and no pseudo-location fallback are performed.
    """
    public_ip = _public_ip(ip)
    if not public_ip or not settings.geoip_city_db:
        return {}
    database_path = Path(settings.geoip_city_db).expanduser()
    if not database_path.is_file():
        return {}
    try:
        import geoip2.database

        with geoip2.database.Reader(str(database_path)) as reader:
            record = reader.city(public_ip)
        country = record.country.iso_code
        if not country:
            return {}
        latitude = record.location.latitude
        longitude = record.location.longitude
        return {
            "country": country,
            "country_name": record.country.name or country,
            "latitude": float(latitude) if latitude is not None else None,
            "longitude": float(longitude) if longitude is not None else None,
            "location_source": "local_geoip_mmdb",
            "location_precision": "provider_coarse",
        }
    except Exception:
        return {}


def country_name(code: str | None) -> str | None:
    if not code:
        return None
    return _COUNTRY_CENTROIDS.get(code.upper(), (None, 0, 0))[0]


def country_centroid(code: str | None) -> tuple[float, float] | None:
    """Return a display anchor for an already verified country aggregate."""
    if not code:
        return None
    entry = _COUNTRY_CENTROIDS.get(code.upper())
    return (entry[1], entry[2]) if entry else None
