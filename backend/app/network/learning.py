from typing import List, Dict, Any, Optional
from app.schemas.network import LearningTopic

LEARNING_TOPICS: List[Dict[str, Any]] = [
    {
        "id": "ip_address",
        "title": "IP Address (Internet Protocol Address)",
        "category": "Fundamentals",
        "summary": "The unique numerical identifier assigned to every device on a network.",
        "explanation": (
            "An IP address works like a mailing address for digital communication. IPv4 uses 32-bit addresses "
            "written as four numbers separated by dots (e.g. 192.168.1.50). Private IP ranges (RFC 1918) are used inside "
            "homes and offices, while public IP addresses identify your network on the global Internet."
        ),
        "how_netscope_measures": "NetScope inspects your active host adapters, discovers local devices via ARP, and queries public IP services.",
        "recommended_reading": "RFC 791 (IPv4), RFC 1918 (Private Address Allocation)"
    },
    {
        "id": "mac_address",
        "title": "MAC Address (Media Access Control)",
        "category": "Fundamentals",
        "summary": "The permanent hardware identifier embedded into your physical network interface card.",
        "explanation": (
            "While IP addresses can change dynamically via DHCP, a MAC address is a 48-bit (6-byte) physical identifier "
            "(e.g. AA:BB:CC:DD:EE:FF) assigned by the device manufacturer. The first 3 bytes represent the Organizationally "
            "Unique Identifier (OUI), which tells you who manufactured the device (Apple, Intel, Cisco, etc.)."
        ),
        "how_netscope_measures": "NetScope queries local ARP tables and matches MAC OUIs against an offline IEEE hardware database.",
        "recommended_reading": "IEEE 802 Standards for Local and Metropolitan Area Networks"
    },
    {
        "id": "subnet_cidr",
        "title": "Subnet Mask & CIDR Notation",
        "category": "Architecture",
        "summary": "The boundary that defines how large your local network is and which IPs are local versus remote.",
        "explanation": (
            "A subnet mask divides an IP address into two parts: the Network portion and the Host portion. In CIDR notation "
            "(Classless Inter-Domain Routing), /24 means the first 24 bits belong to the network (255.255.255.0), leaving 8 bits "
            "for 254 usable local devices. Devices on the same subnet communicate directly without routing."
        ),
        "how_netscope_measures": "NetScope's IP Calculator mathematically computes network addresses, broadcast addresses, and usable host counts.",
        "recommended_reading": "RFC 4632 (Classless Inter-domain Routing)"
    },
    {
        "id": "default_gateway",
        "title": "Default Gateway",
        "category": "Architecture",
        "summary": "The router or node that forwards packets outside your local subnet to the Internet.",
        "explanation": (
            "When your computer needs to send data to an IP address that is not on your local subnet, it sends the packets "
            "to the default gateway (usually your home Wi-Fi router, such as 192.168.1.1). The gateway translates addresses (NAT) "
            "and routes traffic across WAN carriers."
        ),
        "how_netscope_measures": "NetScope reads the operating system routing table to discover the gateway IP and monitors its MAC address baseline.",
        "recommended_reading": "RFC 1812 (Requirements for IP Version 4 Routers)"
    },
    {
        "id": "dns",
        "title": "DNS (Domain Name System)",
        "category": "Core Services",
        "summary": "The internet's phonebook that translates human domain names into numerical IP addresses.",
        "explanation": (
            "Computers communicate using IP addresses, but humans remember domain names like google.com. DNS queries resolve "
            "domains into A records (IPv4), AAAA records (IPv6), MX records (mail servers), and TXT records."
        ),
        "how_netscope_measures": "NetScope provides multi-record DNS resolution diagnostics and benchmarks DNS resolution latency.",
        "recommended_reading": "RFC 1034 & 1035 (Domain Names - Concepts and Facilities)"
    },
    {
        "id": "ports",
        "title": "Network Ports (TCP & UDP)",
        "category": "Transport",
        "summary": "Numbered endpoints on a device allowing multiple applications to share network connections.",
        "explanation": (
            "An IP address specifies the destination computer, while a port number (0-65535) specifies which application receives "
            "the data. For example, web servers typically listen on port 80 (HTTP) and port 443 (HTTPS), while SSH uses port 22."
        ),
        "how_netscope_measures": "NetScope executes controlled TCP connect port scans with anti-rebinding protections to identify exposed services.",
        "recommended_reading": "IANA Service Name and Port Number Registry"
    },
    {
        "id": "tcp_udp",
        "title": "TCP vs UDP",
        "category": "Transport",
        "summary": "The two primary transport layer protocols that deliver network traffic.",
        "explanation": (
            "TCP (Transmission Control Protocol) is connection-oriented and guarantees reliable, ordered packet delivery via a "
            "three-way handshake (SYN, SYN-ACK, ACK). UDP (User Datagram Protocol) is connectionless, prioritizing low latency "
            "over reliability (ideal for streaming, gaming, and DNS)."
        ),
        "how_netscope_measures": "NetScope measures TCP connect handshake latency directly on port 53/443 without raw packet privileges.",
        "recommended_reading": "RFC 793 (TCP) & RFC 768 (UDP)"
    },
    {
        "id": "ping_icmp",
        "title": "Ping & ICMP Latency",
        "category": "Diagnostics",
        "summary": "The fundamental tool for measuring round-trip time and connectivity to remote hosts.",
        "explanation": (
            "Ping uses ICMP (Internet Control Message Protocol) Echo Request and Echo Reply messages. The time between sending "
            "a request and receiving a reply is the Round-Trip Time (RTT), measured in milliseconds (ms)."
        ),
        "how_netscope_measures": "NetScope invokes tokenized system ping binaries to collect genuine min, average, and max round-trip latency.",
        "recommended_reading": "RFC 792 (Internet Control Message Protocol)"
    },
    {
        "id": "packet_loss",
        "title": "Packet Loss & Network Health",
        "category": "Diagnostics",
        "summary": "The percentage of data packets sent across a network that fail to reach their destination.",
        "explanation": (
            "Packet loss occurs due to signal interference, network congestion, faulty cabling, or overloaded router buffers. "
            "Loss above 2-3% significantly degrades video calls, voice streaming, and web responsiveness."
        ),
        "how_netscope_measures": "NetScope measures packet loss during ping tests and factors packet loss heavily into its deterministic health score.",
        "recommended_reading": "RFC 2681 (A Round-trip Delay Metric for IPPM)"
    },
    {
        "id": "arp_spoofing",
        "title": "ARP & ARP Poisoning Security",
        "category": "Cybersecurity",
        "summary": "How devices map IPs to MAC addresses, and how attackers exploit this via ARP spoofing.",
        "explanation": (
            "ARP (Address Resolution Protocol) has no authentication. An attacker on the local network can broadcast forged ARP replies "
            "claiming the router's IP has the attacker's MAC address, intercepting all outbound Internet traffic (Man-in-the-Middle)."
        ),
        "how_netscope_measures": "NetScope features Operator-Confirmed Gateway Baseline monitoring that flags any ARP divergence immediately (SEC-001).",
        "recommended_reading": "RFC 826 (An Ethernet Address Resolution Protocol)"
    }
]

def get_learning_topics_with_context(
    current_ip: Optional[str] = None,
    current_gateway: Optional[str] = None,
    current_latency: Optional[float] = None
) -> List[LearningTopic]:
    """
    Returns learning topics annotated with live contextual data from the user's active network.
    """
    topics: List[LearningTopic] = []
    for t in LEARNING_TOPICS:
        curr_val = None
        if t["id"] == "ip_address" and current_ip:
            curr_val = f"Your active IP: {current_ip}"
        elif t["id"] == "default_gateway" and current_gateway:
            curr_val = f"Your default gateway: {current_gateway}"
        elif t["id"] == "ping_icmp" and current_latency is not None:
            curr_val = f"Your current latency: {current_latency:.1f} ms"

        topics.append(
            LearningTopic(
                id=t["id"],
                title=t["title"],
                category=t["category"],
                summary=t["summary"],
                explanation=t["explanation"],
                how_netscope_measures=t["how_netscope_measures"],
                current_value=curr_val,
                recommended_reading=t["recommended_reading"]
            )
        )
    return topics
