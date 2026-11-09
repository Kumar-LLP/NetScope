import socket
import ipaddress
import psutil
from typing import List, Optional, Tuple
from app.schemas.network import InterfaceSchema

def get_active_interface_ip() -> Optional[str]:
    """
    Determines the active host IP address used for outbound Internet routing.
    Uses a non-transmitting UDP connect that does not require admin privileges.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Connect to public DNS address without sending packets
        s.connect(("8.8.8.8", 80))
        active_ip = s.getsockname()[0]
        s.close()
        return active_ip
    except Exception:
        # Fallback to localhost if network disconnected
        return "127.0.0.1"

def calculate_cidr(ip: str, netmask: Optional[str]) -> Tuple[str, str]:
    """
    Given an IP and netmask (e.g., '192.168.1.70', '255.255.255.0'),
    returns (network_cidr, mask_str), e.g. ('192.168.1.0/24', '255.255.255.0').
    """
    if not netmask:
        netmask = "255.255.255.0"
    try:
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network), netmask
    except Exception:
        return f"{ip}/24", "255.255.255.0"

def get_network_interfaces() -> List[InterfaceSchema]:
    """
    Enumerates all system network interfaces, resolving IP, Netmask, Broadcast,
    MAC address, operational status, and line speed.
    """
    active_ip = get_active_interface_ip()
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    interfaces: List[InterfaceSchema] = []

    for name, addr_list in addrs.items():
        ipv4_info = None
        mac_addr = None

        for addr in addr_list:
            if addr.family == socket.AF_INET:
                ipv4_info = addr
            elif getattr(addr, "family", None) == getattr(psutil, "AF_LINK", None):
                mac_addr = addr.address

        # Only list if it has an address or is active
        if not ipv4_info and not mac_addr:
            continue

        stat = stats.get(name)
        is_up = stat.isup if stat else True
        speed = stat.speed if stat and stat.speed > 0 else None

        ip_str = ipv4_info.address if ipv4_info else None
        mask_str = ipv4_info.netmask if ipv4_info else None
        bcast_str = ipv4_info.broadcast if ipv4_info else None

        is_default = (ip_str == active_ip) if ip_str and active_ip else False

        # Normalize MAC format
        if mac_addr:
            mac_addr = mac_addr.replace("-", ":").upper()

        interfaces.append(
            InterfaceSchema(
                name=name,
                ip_address=ip_str,
                netmask=mask_str,
                broadcast=bcast_str,
                mac_address=mac_addr,
                is_up=is_up,
                speed_mbps=speed,
                is_default=is_default,
            )
        )

    # Sort so active/default interface is at the top
    interfaces.sort(key=lambda x: (not x.is_default, not x.is_up, x.name))
    return interfaces
