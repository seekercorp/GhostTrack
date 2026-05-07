"""Geo lookup utilities for GhostTrack.

Provides functions to query IP geolocation data from multiple
free APIs with fallback support.
"""

import requests
import json
from typing import Optional

# Timeout for API requests in seconds
REQUEST_TIMEOUT = 10

# Ordered list of geolocation API endpoints (fallback chain)
GEO_APIS = [
    "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query",
    "https://ipapi.co/{ip}/json/",
    "https://freegeoip.app/json/{ip}",
]


def fetch_geo_data(ip: str) -> Optional[dict]:
    """Attempt to fetch geolocation data for a given IP address.

    Tries each API in GEO_APIS in order, returning the first
    successful response. Returns None if all APIs fail.

    Args:
        ip: The IP address string to look up.

    Returns:
        A dict with geolocation fields, or None on failure.
    """
    for api_template in GEO_APIS:
        url = api_template.format(ip=ip)
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                # ip-api returns a 'status' field; others may not
                if "status" in data and data["status"] != "success":
                    continue
                return normalize(data, ip)
        except (requests.RequestException, json.JSONDecodeError):
            continue
    return None


def normalize(data: dict, ip: str) -> dict:
    """Normalize API response into a consistent schema.

    Different APIs use different key names; this function maps
    them to a standard set of keys used throughout GhostTrack.

    Args:
        data: Raw JSON dict from a geolocation API.
        ip:   The queried IP address (used as fallback for 'query').

    Returns:
        A dict with standardized keys.
    """
    return {
        "ip":          data.get("query") or data.get("ip") or ip,
        "country":     data.get("country") or data.get("country_name", "N/A"),
        "country_code":data.get("countryCode") or data.get("country_code", "N/A"),
        "region":      data.get("regionName") or data.get("region") or data.get("region_name", "N/A"),
        "city":        data.get("city", "N/A"),
        "zip":         data.get("zip") or data.get("postal", "N/A"),
        "latitude":    data.get("lat") or data.get("latitude", "N/A"),
        "longitude":   data.get("lon") or data.get("longitude", "N/A"),
        "timezone":    data.get("timezone", "N/A"),
        "isp":         data.get("isp", "N/A"),
        "org":         data.get("org") or data.get("organization", "N/A"),
        "as":          data.get("as", "N/A"),
    }


def format_result(geo: dict) -> str:
    """Format a normalized geo dict into a human-readable string.

    Args:
        geo: Normalized geolocation dict from normalize().

    Returns:
        A multi-line string suitable for terminal output.
    """
    lines = [
        f"  IP Address   : {geo['ip']}",
        f"  Country      : {geo['country']} ({geo['country_code']})",
        f"  Region       : {geo['region']}",
        f"  City         : {geo['city']}",
        f"  ZIP / Postal : {geo['zip']}",
        f"  Latitude     : {geo['latitude']}",
        f"  Longitude    : {geo['longitude']}",
        f"  Timezone     : {geo['timezone']}",
        f"  ISP          : {geo['isp']}",
        f"  Organization : {geo['org']}",
        f"  AS           : {geo['as']}",
    ]
    return "\n".join(lines)
