import asyncio
import time
import socket
import ipaddress
from typing import List, Dict, Optional, Tuple
from app.schemas.network import PortResult, PortScanResponse
from app.network.interfaces import get_network_interfaces

COMMON_SERVICES: Dict[int, str] = {
    21: "FTP (File Transfer)",
    22: "SSH (Secure Shell)",
    23: "Telnet (Unencrypted CLI)",
    25: "SMTP (Mail Transfer)",
    53: "DNS (Domain Name System)",
    80: "HTTP (World Wide Web)",
    110: "POP3 (Mail Access)",
    135: "MSRPC (Microsoft RPC)",
    139: "NetBIOS (File Sharing)",
    143: "IMAP (Mail Access)",
    443: "HTTPS (Encrypted Web)",
    445: "SMB (Direct Host Sharing)",
    993: "IMAPS (Secure IMAP)",
    995: "POP3S (Secure POP3)",
    1433: "MSSQL (Microsoft SQL Server)",
    1521: "Oracle Database",
    3306: "MySQL Database",
    3389: "RDP (Remote Desktop)",
    5432: "PostgreSQL Database",
    6379: "Redis Cache Store",
    8000: "HTTP-Alt / FastAPI Dev",
    8080: "HTTP-Proxy / Alternate",
    8443: "HTTPS-Alt / Management",
    9000: "SonarQube / Portainer",
    27017: "MongoDB Database"
}

def is_target_authorized_scope(target: str) -> Tuple[bool, str, str]:
    """
    Validates that the target falls strictly within authorized local scopes:
    loopback, local adapter IP, or private RFC 1918 / link-local addresses.
    Rejects public external WAN addresses.
    Returns: (is_authorized, resolved_ip, reason)
    """
    clean_target = target.strip()
    if not clean_target:
        return False, "", "Target address is empty."

    try:
        resolved_ip = socket.gethostbyname(clean_target)
    except Exception as e:
        return False, "", f"Could not resolve host '{clean_target}': {str(e)}"

    try:
        ip_obj = ipaddress.ip_address(resolved_ip)
    except ValueError as e:
        return False, resolved_ip, f"Invalid IP address '{resolved_ip}': {str(e)}"

    # Allow loopback (127.0.0.1, etc.)
    if ip_obj.is_loopback:
        return True, resolved_ip, "Loopback address is authorized."

    # Allow private (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and link-local
    if ip_obj.is_private or ip_obj.is_link_local:
        return True, resolved_ip, "Private network target is authorized."

    # Allow active local interface IP
    try:
        interfaces = get_network_interfaces()
        for iface in interfaces:
            if iface.ip_address and iface.ip_address == resolved_ip:
                return True, resolved_ip, "Local adapter IP is authorized."
    except Exception:
        pass

    return False, resolved_ip, (
        f"Target '{clean_target}' resolves to public WAN address '{resolved_ip}'. "
        "External scanning is prohibited by security policy. Only local and private targets are permitted."
    )

async def grab_banner(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, port: int) -> Optional[str]:
    """
    Attempts to read initial banner or send a polite HTTP HEAD request to identify the service.
    """
    try:
        if port in (80, 8000, 8080, 8443):
            writer.write(b"HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n")
            await writer.drain()
        
        banner_bytes = await asyncio.wait_for(reader.read(256), timeout=0.35)
        if banner_bytes:
            first_line = banner_bytes.decode("utf-8", errors="ignore").splitlines()[0].strip()
            return first_line[:80]
    except Exception:
        pass
    return None

async def scan_single_port(
    target: str,
    port: int,
    timeout_sec: float = 0.5
) -> PortResult:
    """
    Scans a single TCP port using standard non-elevated socket connect.
    """
    service_name = COMMON_SERVICES.get(port, f"Custom Service ({port})")
    start = time.perf_counter()

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(target, port),
            timeout=timeout_sec
        )
        rtt_ms = round((time.perf_counter() - start) * 1000, 2)
        
        banner = await grab_banner(reader, writer, port)
        
        writer.close()
        await writer.wait_closed()

        return PortResult(
            port=port,
            state="open",
            service=service_name,
            banner=banner,
            rtt_ms=rtt_ms
        )
    except ConnectionRefusedError:
        rtt_ms = round((time.perf_counter() - start) * 1000, 2)
        return PortResult(
            port=port,
            state="closed",
            service=service_name,
            banner=None,
            rtt_ms=rtt_ms
        )
    except asyncio.TimeoutError:
        return PortResult(
            port=port,
            state="filtered",
            service=service_name,
            banner=None,
            rtt_ms=None
        )
    except Exception:
        return PortResult(
            port=port,
            state="closed",
            service=service_name,
            banner=None,
            rtt_ms=None
        )

async def run_port_scan(
    target: str,
    ports: List[int],
    timeout_ms: int = 500,
    authorized: bool = False
) -> PortScanResponse:
    """
    Coordinates multi-threaded TCP port scan across specified ports with concurrency limiting
    and strict server-side target authorization enforcement.
    """
    if not authorized:
        raise PermissionError("Port scan authorization was not confirmed by operator.")

    # Enforce server-side target scope validation
    is_auth, resolved_ip, reason = is_target_authorized_scope(target)
    if not is_auth:
        if not resolved_ip:
            raise ValueError(reason)
        raise PermissionError(reason)

    # Validate port ranges (1 - 65535)
    for p in ports:
        if not isinstance(p, int) or p < 1 or p > 65535:
            raise ValueError(f"Port number {p} is out of valid range (1-65535).")

    # Deduplicate and sort ports
    target_ports = sorted(list(set(ports)))
    timeout_sec = max(0.1, min(timeout_ms / 1000.0, 3.0))

    semaphore = asyncio.Semaphore(50)

    async def sem_scan(p: int):
        async with semaphore:
            return await scan_single_port(resolved_ip, p, timeout_sec)

    tasks = [sem_scan(p) for p in target_ports]
    try:
        # Bounded scan execution with overall timeout (maximum 15 seconds)
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=15.0)
    except asyncio.TimeoutError:
        # If overall scan timed out, gather available results
        results = [
            PortResult(port=p, state="filtered", service=COMMON_SERVICES.get(p, f"Port {p}"), banner=None, rtt_ms=None)
            for p in target_ports
        ]

    open_count = sum(1 for r in results if r.state == "open")

    return PortScanResponse(
        target=target,
        total_scanned=len(results),
        open_count=open_count,
        results=results
    )
