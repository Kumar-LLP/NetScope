import ipaddress
import re
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timezone

from app.schemas.network import SecurityFindingSchema, DeviceSchema
from app.network.gateway import get_default_gateway, get_gateway_mac, get_dns_servers

DATABASE_PORTS: Dict[int, str] = {
    1433: "Microsoft SQL Server (MSSQL)",
    1521: "Oracle Database Listener",
    3306: "MySQL / MariaDB",
    5432: "PostgreSQL Database Server",
    6379: "Redis In-Memory Key-Value Store",
    27017: "MongoDB NoSQL Database Server"
}

class SecurityAuditor:
    def __init__(self):
        # Maps IP -> Set of (mac, observed_timestamp_iso)
        self.ip_mac_history: Dict[str, Set[str]] = {}
        self.last_observation_by_ip: Dict[str, str] = {} # ip -> last mac

    def record_ip_mac_observation(self, ip: str, mac: str):
        """Records an observed IP-to-MAC association to detect conflicting reassignments."""
        if ip and mac:
            clean_mac = mac.upper()
            self.ip_mac_history.setdefault(ip, set()).add(clean_mac)
            self.last_observation_by_ip[ip] = clean_mac

    def record_device_history(self, ip: str, mac: str):
        """Forwarding alias for record_ip_mac_observation to support device persistence hooks."""
        self.record_ip_mac_observation(ip, mac)

    def load_history_from_devices(self, devices: List[Any]):
        """Recovers historical IP-to-MAC observations from database devices upon server startup."""
        for d in devices:
            ip = getattr(d, 'ip', None) or getattr(d, 'ip_address', None)
            mac = getattr(d, 'mac', None) or getattr(d, 'mac_address', None)
            if ip and mac:
                self.record_ip_mac_observation(str(ip), str(mac))

    def audit_environment(
        self,
        devices: List[DeviceSchema],
        open_ports: Optional[List[Dict[str, Any]]] = None,
        confirmed_baseline_mac: Optional[str] = None,
        baseline_status: str = "unconfirmed",
        confirmed_at: Optional[str] = None,
        raw_arp_observations: Optional[Dict[str, str]] = None
    ) -> List[SecurityFindingSchema]:
        """
        Runs comprehensive, evidence-based security auditing against active topology,
        inventory, observed ARP mappings, and exposed ports.
        Classifies each finding with an explicit confidence level ('confirmed', 'potential', 'informational').
        """
        findings: List[SecurityFindingSchema] = []
        now = datetime.now(timezone.utc)

        gw_ip = get_default_gateway()
        gw_mac = get_gateway_mac(gw_ip) if gw_ip else None

        # Rule SEC-001: Gateway MAC Baseline & ARP Poisoning Audit
        if gw_mac:
            if baseline_status == "confirmed" and confirmed_baseline_mac:
                if confirmed_baseline_mac.upper() != gw_mac.upper():
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-001",
                            severity="critical",
                            title="Default Gateway MAC Address Changed (Potential ARP Poisoning or Gateway Replacement)",
                            category="mitm_detection",
                            confidence="confirmed",
                            description="The physical MAC address of the default gateway router has diverged from your confirmed baseline.",
                            evidence=f"Confirmed Baseline: {confirmed_baseline_mac} (confirmed at {confirmed_at or 'earlier'}) -> Detected Active MAC: {gw_mac} on Gateway IP {gw_ip}",
                            impact="A rogue device on the local network segment may be executing an ARP spoofing attack, or the gateway router was physically replaced.",
                            remediation="Inspect local router/switch ARP tables. Verify router MAC address against physical hardware sticker. Re-baseline if router was legitimately upgraded.",
                            target=gw_ip,
                            created_at=now
                        )
                    )
            elif baseline_status == "unconfirmed":
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-001-INFO",
                        severity="info",
                        title="Gateway Hardware Baseline Pending Operator Confirmation",
                        category="audit_baseline",
                        confidence="informational",
                        description="An active default gateway MAC was detected. Please review and explicitly confirm this baseline to enable automated ARP spoofing detection.",
                        evidence=f"Detected Gateway IP: {gw_ip}, Hardware MAC: {gw_mac}",
                        impact="Automated spoofing detection requires an operator-confirmed baseline to prevent false alarms.",
                        remediation="Click 'Confirm Gateway Baseline' in the Security Insights panel once verified.",
                        target=gw_ip,
                        created_at=now
                    )
                )

        # Rule SEC-002: Duplicate IP Conflict Detection (distinguish simultaneous vs historical)
        current_scan_macs_by_ip: Dict[str, Set[str]] = {}
        for dev in devices:
            if dev.ip and dev.mac:
                self.record_ip_mac_observation(dev.ip, dev.mac)
                current_scan_macs_by_ip.setdefault(dev.ip, set()).add(dev.mac.upper())

        if raw_arp_observations:
            for ip, mac in raw_arp_observations.items():
                self.record_ip_mac_observation(ip, mac)
                current_scan_macs_by_ip.setdefault(ip, set()).add(mac.upper())

        # Check for multiple MACs associated with single IP
        for ip, macs in self.ip_mac_history.items():
            if len(macs) > 1:
                # Check if multiple MACs were seen simultaneously in the CURRENT sweep/ARP table
                simultaneous = current_scan_macs_by_ip.get(ip, set())
                is_simultaneous = len(simultaneous) > 1

                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-002",
                        severity="high" if is_simultaneous else "medium",
                        title=f"{'Simultaneous IP Address Conflict' if is_simultaneous else 'Potential IP Address Reassignment / Conflict'} on {ip}",
                        category="ip_conflict",
                        confidence="confirmed" if is_simultaneous else "potential",
                        description=(
                            f"Multiple distinct MAC addresses ({len(macs)}) have been observed claiming the same IP address ({ip}). "
                            + ("Active conflicting devices observed simultaneously on the subnet." if is_simultaneous else "May reflect historical DHCP lease reassignment.")
                        ),
                        evidence=f"Observed MAC addresses: {', '.join(sorted(macs))} on IP {ip}" + (" (Active overlap detected)" if is_simultaneous else ""),
                        impact="Packets directed to this IP will experience route flapping, dropped connections, or potential session hijacking.",
                        remediation="Review DHCP server scope allocations and static IP assignments to resolve overlapping configurations.",
                        target=ip,
                        created_at=now
                    )
                )

        # Rule SEC-003: DNS Resolver Hygiene & Encryption Audit
        dns_servers = get_dns_servers()
        for dns_ip in dns_servers:
            is_secure_known = dns_ip in ("1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4", "9.9.9.9", "149.112.112.112")
            is_local_gw = (dns_ip == gw_ip)
            is_loopback = False
            is_private = False
            try:
                ip_obj = ipaddress.ip_address(dns_ip)
                is_loopback = ip_obj.is_loopback
                is_private = ip_obj.is_private or ip_obj.is_link_local
            except Exception:
                pass

            # Only flag if external unverified public IP without known DoH/DoT evidence
            if not is_secure_known and not is_local_gw and not is_loopback and not is_private:
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-003",
                        severity="low",
                        title=f"External Unverified DNS Resolver in Use ({dns_ip})",
                        category="dns_hygiene",
                        confidence="potential",
                        description=f"System queries are resolving through external DNS server {dns_ip}. Without verified DNS-over-HTTPS (DoH) or DNS-over-TLS (DoT), queries are presumed to use standard unencrypted UDP port 53.",
                        evidence=f"Active DNS Nameserver: {dns_ip} (Standard UDP/53 presumed)",
                        impact="Unencrypted DNS queries can be logged, profiled, or spoofed by intermediate network operators and upstream carriers.",
                        remediation="Configure DNS-over-HTTPS (DoH) or switch to verified privacy-centric DNS providers (Cloudflare 1.1.1.1 or Quad9 9.9.9.9).",
                        target=dns_ip,
                        created_at=now
                    )
                )

        # Port-Based Heuristics (Exposed Services)
        if open_ports:
            for p in open_ports:
                port_num = p.get("port")
                target = p.get("target") or "Unknown"
                banner = (p.get("banner") or "").strip()

                # Rule SEC-004: Telnet (Port 23)
                if port_num == 23:
                    is_confirmed = bool(banner and any(kw in banner.lower() for kw in ["login", "telnet", "welcome", "user", "password"]))
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-004",
                            severity="critical" if is_confirmed else "high",
                            title=f"{'Verified' if is_confirmed else 'Potential'} Unencrypted Telnet Service Exposed (Port 23)",
                            category="insecure_protocol",
                            confidence="confirmed" if is_confirmed else "potential",
                            description=f"{'A confirmed' if is_confirmed else 'A potential'} legacy unencrypted Telnet terminal service is listening on {target}:23.",
                            evidence=f"Port 23 open on {target}. Banner: '{banner or 'No banner grabbed'}'",
                            impact="Telnet transmits authentication credentials and commands in plaintext, permitting credential theft via passive packet capture.",
                            remediation="Immediately disable Telnet daemon and migrate management sessions to SSH (Port 22) with key-based authentication.",
                            target=f"{target}:23",
                            created_at=now
                        )
                    )

                # Rule SEC-005: Plaintext FTP (Port 21)
                elif port_num == 21:
                    has_tls = bool(banner and any(kw in banner.lower() for kw in ["tls", "ssl", "ftps"]))
                    if not has_tls:
                        is_confirmed_ftp = bool(banner and any(kw in banner.lower() for kw in ["ftp", "220", "filez", "vsftpd", "pure-ftpd"]))
                        findings.append(
                            SecurityFindingSchema(
                                rule_id="SEC-005",
                                severity="medium",
                                title=f"{'Verified' if is_confirmed_ftp else 'Potential'} Unencrypted Plain FTP Service Exposed (Port 21)",
                                category="insecure_protocol",
                                confidence="confirmed" if is_confirmed_ftp else "potential",
                                description=f"FTP listener is active on {target}:21 without verified TLS encryption in banner.",
                                evidence=f"Port 21 open on {target}. Banner: '{banner or 'No banner grabbed'}'",
                                impact="Standard FTP transmits usernames and passwords in cleartext without encryption.",
                                remediation="Switch to SFTP (over SSH) or enforce FTPS (Explicit TLS) with mandatory encryption.",
                                target=f"{target}:21",
                                created_at=now
                            )
                        )

                # Rule SEC-006: Database Exposure (MSSQL, Oracle, MySQL, Postgres, Redis, Mongo)
                elif port_num in DATABASE_PORTS:
                    db_name = DATABASE_PORTS[port_num]
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-006",
                            severity="high",
                            title=f"Potential Database Port Exposure ({db_name} on Port {port_num})",
                            category="database_exposure",
                            confidence="potential",
                            description=f"{db_name} listener (Port {port_num}) is exposed directly on network address {target}.",
                            evidence=f"Port {port_num} ({db_name}) active. Banner: '{banner or 'Standard DB Protocol'}'",
                            impact="Direct database network exposure increases risk of automated brute-force attacks, unauthenticated probing, and data exfiltration.",
                            remediation="Bind database daemon exclusively to localhost (127.0.0.1) or restrict network access using local firewall rules and VPN tunnels.",
                            target=f"{target}:{port_num}",
                            created_at=now
                        )
                    )

                # Rule SEC-007: Gateway Admin HTTP
                elif port_num == 80 and target == gw_ip:
                    # Check if response redirects to HTTPS
                    redirects_to_https = bool(
                        banner and (
                            "location: https://" in banner.lower() or
                            "301 moved" in banner.lower() or
                            "302 found" in banner.lower() or
                            "307 temporary" in banner.lower() or
                            "308 permanent" in banner.lower()
                        )
                    )
                    if not redirects_to_https:
                        findings.append(
                            SecurityFindingSchema(
                                rule_id="SEC-007",
                                severity="medium",
                                title="Gateway Management Portal Accessible via Cleartext HTTP",
                                category="service_exposure",
                                confidence="potential",
                                description=f"Default gateway router {gw_ip} has HTTP port 80 open without verified forced redirection to HTTPS in response header.",
                                evidence=f"Port 80 open on {gw_ip}. Response Banner: '{banner or 'HTTP listener active'}'",
                                impact="Router administrative sessions conducted over plain HTTP can expose admin passwords to local network eavesdroppers.",
                                remediation="Log into router administration settings, enable HTTPS web management, and disable cleartext HTTP access.",
                                target=f"{gw_ip}:80",
                                created_at=now
                            )
                        )

                # Rule SEC-008: SMB / Windows File Sharing (Port 445 / 139)
                elif port_num in (445, 139):
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-008",
                            severity="medium",
                            title=f"SMB / Windows File Sharing Port Active ({port_num})",
                            category="file_sharing_exposure",
                            confidence="potential",
                            description=f"Server Message Block (SMB) network service is active on {target}:{port_num}. SMB exposure should be audited for guest access or missing signing.",
                            evidence=f"Port {port_num} active on {target}",
                            impact="Unprotected or misconfigured SMB shares can expose internal files and permit lateral movement across the network.",
                            remediation="Ensure SMB signing is required, audit anonymous access, and restrict SMB to private subnets using Windows Defender Firewall.",
                            target=f"{target}:{port_num}",
                            created_at=now
                        )
                    )

                # Rule SEC-009: Remote Desktop Protocol (Port 3389)
                elif port_num == 3389:
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-009",
                            severity="medium",
                            title="Remote Desktop Protocol (RDP) Port Active (3389)",
                            category="remote_access_exposure",
                            confidence="potential",
                            description=f"Microsoft Remote Desktop listener is active on {target}:3389. Ensure Network Level Authentication (NLA) or VPN encapsulation is enforced.",
                            evidence=f"Port 3389 open on {target}",
                            impact="RDP ports exposed across local or routed subnets are frequent targets for automated dictionary and credential-stuffing attacks.",
                            remediation="Enforce Network Level Authentication (NLA), implement account lockout policies, and access RDP solely through secure VPN.",
                            target=f"{target}:3389",
                            created_at=now
                        )
                    )

        # Baseline Info Finding if no issues detected
        if not findings:
            findings.append(
                SecurityFindingSchema(
                    rule_id="SEC-000",
                    severity="info",
                    title="Network Security Baseline Satisfied",
                    category="audit_baseline",
                    confidence="informational",
                    description="No rogue gateways, IP conflicts, or insecure unencrypted legacy management ports were detected.",
                    evidence=f"Gateway {gw_ip} active ({confirmed_baseline_mac or 'Verified'}), {len(devices)} active devices analyzed.",
                    impact="Local network segment operates within healthy configuration parameters.",
                    remediation="Maintain regular device discovery sweeps and keep router firmware updated.",
                    target=gw_ip,
                    created_at=now
                )
            )

        return findings

security_auditor = SecurityAuditor()
