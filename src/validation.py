"""Validation helpers for endpoint configuration and SSRF-aware destination checks."""
import ipaddress
import socket
from urllib.parse import urlsplit

class EndpointValidationError(ValueError):
    """Raised when an endpoint configuration is invalid or unsafe."""

def validate_endpoint_url(url: str, allow_local: bool = False) -> str:
    if not isinstance(url, str) or not url.strip():
        raise EndpointValidationError("Enter a URL.")
    url = url.strip()
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise EndpointValidationError("Only valid HTTP or HTTPS URLs are allowed.")
        if parts.username or parts.password:
            raise EndpointValidationError("Credentials embedded in URLs are not allowed.")
        host = parts.hostname.rstrip(".").lower()
        local_names = {"localhost", "localhost.localdomain"}
        if not allow_local and host in local_names:
            raise EndpointValidationError("Local destinations are blocked. Enable local-testing mode only for trusted tests.")
        try:
            address = ipaddress.ip_address(host.strip("[]"))
            if not allow_local and (not address.is_global):
                raise EndpointValidationError("Private, loopback, link-local, and reserved IP destinations are blocked.")
        except ValueError:
            if not allow_local:
                try:
                    resolved = socket.getaddrinfo(host, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
                except socket.gaierror:
                    resolved = []
                for item in resolved:
                    ip = ipaddress.ip_address(item[4][0].split("%", 1)[0])
                    if not ip.is_global:
                        raise EndpointValidationError("The hostname resolves to a non-public IP address.")
        if parts.port is not None and not (1 <= parts.port <= 65535):
            raise EndpointValidationError("Port must be between 1 and 65535.")
        return url
    except ValueError as exc:
        if isinstance(exc, EndpointValidationError):
            raise
        raise EndpointValidationError("Invalid URL format.") from exc

def validate_endpoint_config(name: str, url: str, method: str = "GET", timeout_seconds: float = 5.0,
                             expected_status_min: int = 200, expected_status_max: int = 299,
                             allow_local: bool = False) -> dict:
    if not name or not name.strip():
        raise EndpointValidationError("Endpoint name cannot be empty.")
    method = method.upper().strip()
    if method not in {"GET", "HEAD"}:
        raise EndpointValidationError("Supported methods are GET and HEAD. POST is intentionally omitted to avoid unsafe side effects.")
    if not isinstance(timeout_seconds, (int, float)) or not (0.1 <= float(timeout_seconds) <= 60):
        raise EndpointValidationError("Timeout must be between 0.1 and 60 seconds.")
    if not (100 <= int(expected_status_min) <= int(expected_status_max) <= 599):
        raise EndpointValidationError("Expected status range must satisfy 100 <= minimum <= maximum <= 599.")
    return {"name": name.strip(), "url": validate_endpoint_url(url, allow_local), "method": method,
            "timeout_seconds": float(timeout_seconds), "expected_status_min": int(expected_status_min),
            "expected_status_max": int(expected_status_max)}
