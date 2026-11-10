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
    Enumerates all system network interfaces, resolving IPv4, IPv6, Netmask, Broadcast,
    MAC address, operational status, interface type, and line speed.
    """
    active_ip = get_active_interface_ip()
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    interfaces: List[InterfaceSchema] = []
    idx = 1

    for name, addr_list in addrs.items():
        ipv4_info = None
        ipv6_str = None
        mac_addr = None

        for addr in addr_list:
            if addr.family == socket.AF_INET:
                ipv4_info = addr
            elif hasattr(socket, "AF_INET6") and addr.family == socket.AF_INET6:
                # Capture global or link-local IPv6 address (strip scope id if present)
                raw_v6 = addr.address.split("%")[0]
                if not ipv6_str or not raw_v6.startswith("fe80"):
                    ipv6_str = raw_v6
            elif getattr(addr, "family", None) == getattr(psutil, "AF_LINK", None):
                mac_addr = addr.address

        # Only list if it has an address or is active
        if not ipv4_info and not mac_addr and not ipv6_str:
            continue

        stat = stats.get(name)
        is_up = stat.isup if stat else True
        speed = stat.speed if stat and stat.speed > 0 else None

        ip_str = ipv4_info.address if ipv4_info else None
        mask_str = ipv4_info.netmask if ipv4_info else None
        bcast_str = ipv4_info.broadcast if ipv4_info else None

        is_default = (ip_str == active_ip) if ip_str and active_ip else False

        # Determine interface type categorization
        lower_name = name.lower()
        if "loopback" in lower_name or (ip_str and ip_str.startswith("127.")):
            iface_type = "loopback"
        elif any(k in lower_name for k in ["wi-fi", "wifi", "wlan", "wireless", "802.11"]):
            iface_type = "wifi"
        elif any(k in lower_name for k in ["vethernet", "hyper-v", "vmware", "virtual", "wsl", "virbr"]):
            iface_type = "virtual"
        elif any(k in lower_name for k in ["tap", "tun", "vpn", "wireguard", "tailscale"]):
            iface_type = "vpn"
        else:
            iface_type = "ethernet"

        # Normalize MAC format
        if mac_addr:
            mac_addr = mac_addr.replace("-", ":").upper()

        interfaces.append(
            InterfaceSchema(
                name=name,
                ip_address=ip_str,
                ipv6_address=ipv6_str,
                netmask=mask_str,
                broadcast=bcast_str,
                mac_address=mac_addr,
                is_up=is_up,
                speed_mbps=speed,
                is_default=is_default,
                interface_type=iface_type,
                index=idx
            )
        )
        idx += 1

    # Sort so active/default interface is at the top, then active physical NICs, then virtual
    interfaces.sort(key=lambda x: (not x.is_default, not x.is_up, x.interface_type == "virtual", x.name))
    return interfaces
