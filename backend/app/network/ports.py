import asyncio
import time
import socket
import ipaddress
from typing import List, Dict, Optional, Tuple, Any
from app.core.config import settings
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

_active_port_scans = 0
_port_scan_lock = asyncio.Lock()
MAX_CONCURRENT_ACTIVE_SCANS = 2

def is_target_authorized_scope(target: str) -> Tuple[bool, str, str]:
    """
    Validates that the target falls strictly within authorized local scopes:
    loopback, local adapter IP, active interface subnet, or explicitly configured targets.
    Resolves all A and AAAA DNS records and verifies EVERY resolved address to prevent
    DNS rebinding and TOCTOU attacks. Pins the validated numeric IP for connection.
    Rejects public external WAN addresses and unrelated foreign private subnets.
    Returns: (is_authorized, pinned_numeric_ip, reason)
    """
    clean_target = target.strip()
    if not clean_target:
        return False, "", "Target address is empty."

    # 1. Resolve all A and AAAA records (supports both IPv4 and IPv6)
    try:
        addrinfo = socket.getaddrinfo(clean_target, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
        if not addrinfo:
            return False, "", f"Could not resolve host '{clean_target}'."
        # Extract unique resolved IP addresses in order
        resolved_ips = list(dict.fromkeys(item[4][0] for item in addrinfo))
    except Exception as e:
        return False, "", f"DNS resolution failed for host '{clean_target}': {str(e)}"

    if not resolved_ips:
        return False, "", f"No IP addresses resolved for host '{clean_target}'."

    # 2. Check explicitly authorized targets configuration
    is_explicit_host = clean_target.lower() in [t.lower() for t in settings.AUTHORIZED_TARGETS]

    # Pre-fetch active interfaces and authorized networks once
    try:
        interfaces = get_network_interfaces()
    except Exception:
        interfaces = []

    auth_subnets: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for net_str in settings.AUTHORIZED_NETWORKS:
        try:
            auth_subnets.append(ipaddress.ip_network(net_str.strip(), strict=False))
        except Exception:
            continue

    # Helper function to check a single IP address
    def check_single_ip(resolved_ip: str) -> Tuple[bool, str]:
        try:
            ip_obj = ipaddress.ip_address(resolved_ip)
        except ValueError as err:
            return False, f"Invalid IP address '{resolved_ip}': {str(err)}"

        # Allow loopback (127.0.0.1, ::1)
        if ip_obj.is_loopback:
            return True, "Loopback target is authorized."

        # If explicitly authorized in settings and is private/loopback, permit
        if is_explicit_host and (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local):
            return True, f"Target '{clean_target}' is explicitly authorized in system settings."

        # Reject public external WAN addresses immediately
        if not (ip_obj.is_private or ip_obj.is_link_local):
            return False, (
                f"Target '{clean_target}' resolves to public WAN address '{resolved_ip}'. "
                "External scanning is prohibited by security policy. Only local and private targets are permitted."
            )

        # Check if target matches any active local interface IP
        for iface in interfaces:
            if iface.ip_address and iface.ip_address == resolved_ip:
                return True, "Local adapter IP is authorized."

            # Check if target falls within active interface subnet
            if iface.ip_address and iface.netmask and iface.is_up and ip_obj.version == 4:
                try:
                    iface_net = ipaddress.IPv4Network(f"{iface.ip_address}/{iface.netmask}", strict=False)
                    if ipaddress.IPv4Address(resolved_ip) in iface_net:
                        return True, "Target is within active local network interface subnet."
                except Exception:
                    continue

        # Check explicitly configured authorized networks
        for auth_net in auth_subnets:
            if ip_obj in auth_net:
                return True, "Target is within configured authorized network range."

        return False, (
            f"Target '{clean_target}' ({resolved_ip}) is not within any active local interface subnet "
            "or explicitly authorized scopes."
        )

    # 3. Validate EVERY resolved address to prevent DNS rebinding
    for ip in resolved_ips:
        ip_auth, ip_reason = check_single_ip(ip)
        if not ip_auth:
            return False, ip, f"DNS Rebinding / Scope Protection: {ip_reason}"

    # 4. Pin the first validated numeric IP for connection
    pinned_ip = resolved_ips[0]
    return True, pinned_ip, f"Target is authorized (pinned to validated IP: {pinned_ip})."

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
    Distinguishes open, closed, filtered, and error states.
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
    except Exception as e:
        err_msg = str(e).lower()
        state = "closed" if "refused" in err_msg else ("filtered" if "timed out" in err_msg or "timeout" in err_msg else "error")
        return PortResult(
            port=port,
            state=state,
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
    Coordinates multi-threaded TCP port scan across specified ports with concurrency limiting,
    active scan throttles, strict server-side target authorization enforcement, and preservation
    of partial results upon overall scan timeout or cancellation.
    """
    global _active_port_scans, _port_scan_lock

    if not authorized:
        raise PermissionError("Port scan authorization was not confirmed by operator.")

    # Concurrency guard: limit active scans
    async with _port_scan_lock:
        if _active_port_scans >= MAX_CONCURRENT_ACTIVE_SCANS:
            raise RuntimeError(f"Maximum concurrent active port scans in progress ({MAX_CONCURRENT_ACTIVE_SCANS}). Please wait.")
        _active_port_scans += 1

    try:
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

        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_PORT_SCANS)
        completed_results: Dict[int, PortResult] = {}
        overall_timed_out = False

        async def sem_scan(p: int):
            async with semaphore:
                res = await scan_single_port(resolved_ip, p, timeout_sec)
                completed_results[p] = res
                return res

        task_dict = {p: asyncio.create_task(sem_scan(p)) for p in target_ports}
        start_time = time.perf_counter()

        try:
            # Overall scan deadline: maximum 15.0 seconds
            done, pending = await asyncio.wait(
                task_dict.values(),
                timeout=15.0,
                return_when=asyncio.ALL_COMPLETED
            )
            if pending:
                overall_timed_out = True
                for t in pending:
                    t.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
        except asyncio.CancelledError:
            for t in task_dict.values():
                t.cancel()
            raise

        elapsed_sec = round(time.perf_counter() - start_time, 2)

        # Assemble results preserving all completed scans and marking unfinished ports distinctly
        final_results: List[PortResult] = []
        for p in target_ports:
            if p in completed_results:
                final_results.append(completed_results[p])
            elif overall_timed_out:
                final_results.append(
                    PortResult(
                        port=p,
                        state="timed_out",
                        service=COMMON_SERVICES.get(p, f"Port {p}"),
                        banner=None,
                        rtt_ms=None
                    )
                )
            else:
                final_results.append(
                    PortResult(
                        port=p,
                        state="not_scanned",
                        service=COMMON_SERVICES.get(p, f"Port {p}"),
                        banner=None,
                        rtt_ms=None
                    )
                )

        open_count = sum(1 for r in final_results if r.state == "open")
        total_completed = len(completed_results)
        remaining = len(target_ports) - total_completed

        status_str = "completed"
        if overall_timed_out:
            status_str = "timed_out" if total_completed == 0 else "partial"

        return PortScanResponse(
            target=target,
            total_scanned=len(final_results),
            open_count=open_count,
            results=final_results,
            status=status_str,
            requested_ports=len(target_ports),
            completed_ports=total_completed,
            remaining_ports=remaining,
            elapsed_seconds=elapsed_sec,
            timed_out=overall_timed_out
        )
    finally:
        async with _port_scan_lock:
            _active_port_scans = max(0, _active_port_scans - 1)
