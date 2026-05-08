"""IP address validation and preprocessing utilities for GhostTrack."""

import re
import socket
from typing import Optional, Tuple


# Regex patterns for IPv4 and IPv6 validation
IPV4_PATTERN = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)

IPV6_PATTERN = re.compile(
    r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    r'|^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$'
    r'|^(?:[0-9a-fA-F]{1,4}:){1,7}:$'
    r'|^(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}$'
    r'|^::1$|^::$'
)

# Reserved/private IP ranges that cannot be geo-located
PRIVATE_RANGES = [
    ("10.0.0.0",      "10.255.255.255"),
    ("172.16.0.0",    "172.31.255.255"),
    ("192.168.0.0",   "192.168.255.255"),
    ("127.0.0.0",     "127.255.255.255"),
    ("169.254.0.0",   "169.254.255.255"),
    ("0.0.0.0",       "0.255.255.255"),
]


def _ip_to_int(ip: str) -> int:
    """Convert a dotted IPv4 string to an integer for range comparison."""
    parts = ip.split(".")
    result = 0
    for part in parts:
        result = (result << 8) | int(part)
    return result


def is_valid_ipv4(ip: str) -> bool:
    """Return True if the given string is a valid IPv4 address."""
    return bool(IPV4_PATTERN.match(ip.strip()))


def is_valid_ipv6(ip: str) -> bool:
    """Return True if the given string is a valid IPv6 address."""
    try:
        socket.inet_pton(socket.AF_INET6, ip.strip())
        return True
    except (socket.error, OSError):
        return False


def is_private_ip(ip: str) -> bool:
    """Check whether an IPv4 address falls within a private/reserved range."""
    if not is_valid_ipv4(ip):
        return False
    ip_int = _ip_to_int(ip.strip())
    for start, end in PRIVATE_RANGES:
        if _ip_to_int(start) <= ip_int <= _ip_to_int(end):
            return True
    return False


def resolve_hostname(hostname: str) -> Optional[str]:
    """Attempt to resolve a hostname to its IPv4 address.

    Returns the resolved IP string, or None if resolution fails.
    """
    try:
        resolved = socket.gethostbyname(hostname.strip())
        return resolved
    except socket.gaierror:
        return None


def validate_and_parse(target: str) -> Tuple[bool, str, str]:
    """Validate and parse a user-supplied target (IP or hostname).

    Args:
        target: Raw string input from the user — may be an IP or a hostname.

    Returns:
        A tuple of (is_valid, ip_address, message) where:
          - is_valid   : bool indicating whether the target is usable
          - ip_address : resolved/cleaned IP string (empty string if invalid)
          - message    : human-readable status description
    """
    target = target.strip()

    if not target:
        return False, "", "No target provided."

    # Direct IPv6 check
    if is_valid_ipv6(target):
        return True, target, "Valid IPv6 address."

    # Direct IPv4 check
    if is_valid_ipv4(target):
        if is_private_ip(target):
            return False, target, f"'{target}' is a private/reserved IP and cannot be tracked."
        return True, target, "Valid public IPv4 address."

    # Attempt hostname resolution
    resolved = resolve_hostname(target)
    if resolved is None:
        return False, "", f"Could not resolve hostname '{target}'."

    if is_private_ip(resolved):
        return False, resolved, f"Hostname '{target}' resolves to private IP '{resolved}'."

    return True, resolved, f"Hostname '{target}' resolved to '{resolved}'."
