import asyncio
import ipaddress
import platform
import re
import socket
import subprocess
import time
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone

from app.core.config import settings
from app.network.interfaces import get_active_interface_ip, calculate_cidr, get_network_interfaces
from app.network.gateway import get_default_gateway, get_gateway_mac
from app.network.vendor import lookup_vendor
from app.schemas.network import DeviceSchema, DeviceDiscoverResponse

class DiscoverySession:
    def __init__(self, scan_id: str, total_hosts: int):
        self.scan_id = scan_id
        self.cancel_event = asyncio.Event()
        self.total_hosts = total_hosts
        self.scanned_hosts = 0
        self.status = "scanning"
        self.start_time = time.perf_counter()

    def get_progress(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "scanned": self.scanned_hosts,
            "total": self.total_hosts,
            "status": self.status
        }

_active_session: Optional[DiscoverySession] = None
_session_lock = asyncio.Lock()

def get_discovery_progress(scan_id: Optional[str] = None) -> Dict[str, Any]:
    """Returns the progress of the active discovery scan, or idle state."""
    global _active_session
    if _active_session:
        if scan_id is None or _active_session.scan_id == scan_id:
            return _active_session.get_progress()
    return {"scan_id": None, "scanned": 0, "total": 0, "status": "idle"}

def stop_discovery(scan_id: Optional[str] = None):
    """Signals the running discovery sweep to cancel immediately."""
    global _active_session
    if _active_session:
        if scan_id is None or _active_session.scan_id == scan_id:
            _active_session.cancel_event.set()
            _active_session.status = "stopped"

def get_authorized_networks() -> List[ipaddress.IPv4Network]:
    """
    Computes authorized IPv4 subnets based on active local network interfaces
    plus any explicitly configured authorized networks in Settings.
    """
    authorized: List[ipaddress.IPv4Network] = []

    # 1. Loopback subnet
    try:
        authorized.append(ipaddress.IPv4Network("127.0.0.0/8", strict=False))
    except Exception:
        pass

    # 2. Subnets of active local network interfaces
    try:
        interfaces = get_network_interfaces()
        for iface in interfaces:
            if iface.ip_address and iface.netmask and iface.is_up:
                try:
                    iface_net = ipaddress.IPv4Network(f"{iface.ip_address}/{iface.netmask}", strict=False)
                    authorized.append(iface_net)
                except Exception:
                    continue
    except Exception:
        pass

    # 3. Explicitly configured authorized networks from settings
    for net_str in settings.AUTHORIZED_NETWORKS:
        try:
            authorized.append(ipaddress.IPv4Network(net_str.strip(), strict=False))
        except Exception:
            continue

    return authorized

def is_network_authorized(net: ipaddress.IPv4Network) -> Tuple[bool, str]:
    """
    Validates that the target network belongs strictly to an active local network interface
    or an explicitly configured authorized scope.
    Rejects unrelated private networks and public external WAN subnets.
    """
    # Reject public networks immediately
    if not (net.is_private or net.is_loopback or net.is_link_local):
        return False, (
            f"Target CIDR '{net}' is a public external WAN network. "
            "Public WAN subnet scanning is strictly prohibited."
        )

    authorized_nets = get_authorized_networks()
    for auth_net in authorized_nets:
        # Check if target network is a subnet of an authorized network or identical
        if net.subnet_of(auth_net) or net == auth_net:
            return True, "Target network is within active local interface scope."

    active_subnets = [
        str(n) for n in authorized_nets
        if n.network_address != ipaddress.IPv4Address("127.0.0.0")
    ]
    return False, (
        f"Target network '{net}' is not within any active local network interface subnet "
        f"({', '.join(active_subnets) if active_subnets else 'none detected'}) "
        "or explicitly configured authorized scopes."
    )

def get_arp_table(target_network: Optional[ipaddress.IPv4Network] = None) -> Dict[str, str]:
    """
    Parses the operating system's ARP cache.
    Restricts results strictly to the authorized target network when provided.
    Returns mapping of {ip_address: mac_address}.
    """
    arp_entries: Dict[str, str] = {}
    try:
        res = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=3)
        for line in res.stdout.splitlines():
            line = line.strip()
            match = re.search(
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})",
                line
            )
            if match:
                ip = match.group(1)
                mac = match.group(2).replace("-", ":").upper()
                if not mac.startswith("FF:FF") and not ip.startswith("224.") and not ip.startswith("239.") and not ip.endswith(".255"):
                    if target_network is not None:
                        try:
                            if ipaddress.IPv4Address(ip) not in target_network:
                                continue
                        except Exception:
                            continue
                    arp_entries[ip] = mac
    except Exception:
        pass
    return arp_entries

def ping_host_fast(ip: str, timeout_ms: int = 150) -> Optional[float]:
    """
    Executes a fast ping probe to wake up the host and populate the OS ARP table.
    """
    is_win = platform.system().lower() == "windows"
    cmd = (
        ["ping", "-n", "1", "-w", str(timeout_ms), ip]
        if is_win
        else ["ping", "-c", "1", "-W", "1", ip]
    )
    start = time.perf_counter()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.3)
        if proc.returncode == 0:
            return round((time.perf_counter() - start) * 1000, 2)
    except Exception:
        pass
    return None

async def async_probe_host(ip: str, cancel_event: asyncio.Event) -> Optional[float]:
    """
    Tries async TCP connect to common service ports (takes ~1-5ms if alive or rejected),
    falling back to threaded ping if needed.
    """
    start = time.perf_counter()
    for port in (80, 443, 135):
        if cancel_event.is_set():
            return None
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=0.10
            )
            writer.close()
            await writer.wait_closed()
            return round((time.perf_counter() - start) * 1000, 2)
        except ConnectionRefusedError:
            return round((time.perf_counter() - start) * 1000, 2)
        except Exception:
            continue

    if cancel_event.is_set():
        return None

    return await asyncio.to_thread(ping_host_fast, ip, 150)

async def resolve_hostname_safe(ip: str) -> Optional[str]:
    """
    Asynchronously resolves hostname with a tight 200ms timeout to prevent blocking.
    """
    try:
        def _lookup():
            return socket.gethostbyaddr(ip)[0]
        return await asyncio.wait_for(asyncio.to_thread(_lookup), timeout=0.20)
    except Exception:
        return None

async def discover_devices(
    target_cidr: Optional[str] = None,
    timeout_seconds: int = 15
) -> DeviceDiscoverResponse:
    """
    Discovers active devices on the local subnet using safe, authorized, non-privileged probes.
    Validates CIDR, enforces active interface scope boundaries, and supports cancellation.
    """
    global _active_session, _session_lock

    # Validate target network or resolve active default interface
    if not target_cidr:
        interfaces = get_network_interfaces()
        def_iface = next((i for i in interfaces if i.is_default and i.ip_address and i.is_up), None)
        if def_iface and def_iface.ip_address:
            target_cidr, _ = calculate_cidr(def_iface.ip_address, def_iface.netmask)
        else:
            # Fallback to first up interface with IP
            up_iface = next((i for i in interfaces if i.ip_address and i.is_up and not i.ip_address.startswith("127.")), None)
            if up_iface and up_iface.ip_address:
                target_cidr, _ = calculate_cidr(up_iface.ip_address, up_iface.netmask)
            else:
                target_cidr = "192.168.1.0/24"

    try:
        network = ipaddress.IPv4Network(target_cidr.strip(), strict=False)
    except Exception as e:
        raise ValueError(f"Invalid CIDR notation '{target_cidr}': {str(e)}")

    # Security check: Target must belong strictly to active local interface or explicitly authorized scope
    is_auth, auth_reason = is_network_authorized(network)
    if not is_auth:
        raise PermissionError(auth_reason)

    # Security check: Prevent oversized sweeps (maximum /24 = 256 addresses)
    if network.num_addresses > 256:
        raise ValueError(
            f"Oversized network range (/{network.prefixlen} contains {network.num_addresses} addresses). "
            "Maximum allowed subnet size is /24 (256 addresses) to prevent local network degradation."
        )

    all_hosts = list(network.hosts())

    # Prevent concurrent conflicting scans
    async with _session_lock:
        if _active_session and _active_session.status == "scanning":
            raise RuntimeError("A device discovery scan is already actively running. Stop it before initiating another.")

        scan_id = str(uuid.uuid4())[:8]
        session = DiscoverySession(scan_id=scan_id, total_hosts=len(all_hosts))
        _active_session = session

    start_time = time.perf_counter()
    active_ip = get_active_interface_ip()
    gateway_ip = get_default_gateway()
    gateway_mac = get_gateway_mac(gateway_ip)

    # Restrict ARP lookup strictly to target network
    initial_arp = get_arp_table(target_network=network)
    semaphore = asyncio.Semaphore(50)

    async def sem_probe(host_ip: str):
        if session.cancel_event.is_set():
            return host_ip, None
        async with semaphore:
            rtt = await async_probe_host(host_ip, session.cancel_event)
            session.scanned_hosts += 1
            return host_ip, rtt

    probe_tasks = [sem_probe(str(h)) for h in all_hosts]
    probe_results = []

    try:
        probe_results = await asyncio.wait_for(
            asyncio.gather(*probe_tasks, return_exceptions=True),
            timeout=float(timeout_seconds)
        )
        if session.cancel_event.is_set():
            session.status = "stopped"
        else:
            session.status = "completed"
    except asyncio.TimeoutError:
        session.status = "timed_out"
    finally:
        pass

    alive_ips: Dict[str, Optional[float]] = {}
    for res in probe_results:
        if isinstance(res, tuple):
            ip_str, rtt = res
            if rtt is not None:
                alive_ips[ip_str] = rtt

    # Refresh ARP cache restricted to target network
    refreshed_arp = {**initial_arp, **get_arp_table(target_network=network)}

    # Ensure default gateway and local host are included if within this network
    if gateway_ip:
        try:
            if ipaddress.IPv4Address(gateway_ip) in network:
                alive_ips.setdefault(gateway_ip, 1.2)
                if gateway_mac:
                    refreshed_arp[gateway_ip] = gateway_mac
        except Exception:
            pass

    if active_ip and not active_ip.startswith("127."):
        try:
            if ipaddress.IPv4Address(active_ip) in network:
                alive_ips.setdefault(active_ip, 0.1)
        except Exception:
            pass

    candidate_ips = sorted(
        set(alive_ips.keys()).union(set(refreshed_arp.keys())),
        key=lambda x: [int(p) for p in x.split('.') if p.isdigit()]
    )

    hostname_tasks = [resolve_hostname_safe(ip) for ip in candidate_ips]
    hostnames = await asyncio.gather(*hostname_tasks, return_exceptions=True)
    hostname_map = {
        candidate_ips[i]: (hostnames[i] if isinstance(hostnames[i], str) else None)
        for i in range(len(candidate_ips))
    }

    devices: List[DeviceSchema] = []
    now = datetime.now(timezone.utc)

    for ip_str in candidate_ips:
        if ip_str.startswith("127.") or ip_str.endswith(".255"):
            continue

        mac = refreshed_arp.get(ip_str)
        is_gw = (ip_str == gateway_ip)
        is_local = (ip_str == active_ip)

        vendor_name = lookup_vendor(mac) if mac else ("Local Host Adapter" if is_local else "Unknown")
        hostname = hostname_map.get(ip_str)
        rtt = alive_ips.get(ip_str)

        devices.append(
            DeviceSchema(
                ip=ip_str,
                mac=mac,
                vendor=vendor_name,
                hostname=hostname,
                is_gateway=is_gw,
                is_local_host=is_local,
                status="online",
                response_time_ms=rtt,
                first_seen=now,
                last_seen=now,
            )
        )

    duration = round(time.perf_counter() - start_time, 2)
    return DeviceDiscoverResponse(
        scan_id=scan_id,
        total_discovered=len(devices),
        duration_seconds=duration,
        devices=devices
    )
