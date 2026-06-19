"""IP allowlist check — per-tenant list stored in DB, enforced at auth layer."""
from __future__ import annotations

import ipaddress

from aai_core.errors import AAIError, ErrorCode


def check_ip_allowlist(client_ip: str, allowlist: list[str]) -> None:
    """Raise AAIError if client_ip is not in allowlist.

    Empty allowlist means allow all (default for tenants without restrictions).
    Supports both individual IPs and CIDR notation (e.g. "10.0.0.0/8").
    """
    if not allowlist:
        return

    try:
        client_addr = ipaddress.ip_address(client_ip)
    except ValueError:
        raise AAIError(
            ErrorCode.AUTH_IP_BLOCKED,
            f"Invalid client IP: {client_ip}",
            http_status=403,
        )

    for entry in allowlist:
        try:
            if "/" in entry:
                network = ipaddress.ip_network(entry, strict=False)
                if client_addr in network:
                    return
            else:
                if client_addr == ipaddress.ip_address(entry):
                    return
        except ValueError:
            continue  # skip malformed entries rather than crashing

    raise AAIError(
        ErrorCode.AUTH_IP_BLOCKED,
        f"IP {client_ip} not in tenant allowlist",
        http_status=403,
        detail={"client_ip": client_ip},
    )
