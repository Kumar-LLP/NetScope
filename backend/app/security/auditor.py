from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import re

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
        self.observed_gateway_mac: Optional[str] = None
        self.ip_mac_history: Dict[str, set[str]] = {}

    def record_ip_mac_observation(self, ip: str, mac: str):
        """Records an observed IP-to-MAC association to detect conflicting reassignments."""
        if ip and mac:
            self.ip_mac_history.setdefault(ip, set()).add(mac.upper())

    def audit_environment(
        self,
        devices: List[DeviceSchema],
        open_ports: Optional[List[Dict[str, Any]]] = None,
        baseline_gateway_mac: Optional[str] = None,
        raw_arp_observations: Optional[Dict[str, str]] = None
    ) -> List[SecurityFindingSchema]:
        """
        Runs comprehensive, heuristic-based security auditing against active topology,
        inventory, observed ARP mappings, and exposed ports.
        """
        findings: List[SecurityFindingSchema] = []
        now = datetime.now(timezone.utc)

        gw_ip = get_default_gateway()
        gw_mac = get_gateway_mac(gw_ip)

        # Baseline MAC resolution (prioritize persistent baseline from DB if passed)
        if baseline_gateway_mac:
            effective_baseline = baseline_gateway_mac
        elif self.observed_gateway_mac:
            effective_baseline = self.observed_gateway_mac
        else:
            effective_baseline = gw_mac
            self.observed_gateway_mac = gw_mac

        # Rule SEC-001: Gateway MAC Baseline & ARP Poisoning Audit
        if gw_mac and effective_baseline:
            if effective_baseline != gw_mac:
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-001",
                        severity="critical",
                        title="Default Gateway MAC Address Changed (Potential ARP Poisoning)",
                        category="mitm_detection",
                        description="The hardware address of the default gateway router has unexpectedly changed compared to the verified baseline.",
                        evidence=f"Baseline Gateway MAC: {effective_baseline} -> Observed Active MAC: {gw_mac} on Gateway IP {gw_ip}",
                        impact="A rogue device on the local network segment may be executing an ARP spoofing / poisoning attack to intercept or modify network packets.",
                        remediation="Inspect your local router/switch ARP tables. Verify router MAC address against physical hardware sticker. Investigate suspicious connected devices.",
                        created_at=now
                    )
                )

        # Record observations for Rule SEC-002: Duplicate IP Conflict Detection
        for dev in devices:
            if dev.ip and dev.mac:
                self.record_ip_mac_observation(dev.ip, dev.mac)

        if raw_arp_observations:
            for ip, mac in raw_arp_observations.items():
                self.record_ip_mac_observation(ip, mac)

        # Check for multiple MACs associated with single IP
        for ip, macs in self.ip_mac_history.items():
            if len(macs) > 1:
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-002",
                        severity="high",
                        title=f"IP Address Conflict Detected on {ip}",
                        category="ip_conflict",
                        description=f"Multiple distinct MAC addresses ({len(macs)}) have been observed claiming the same IP address ({ip}).",
                        evidence=f"Conflicting hardware MAC addresses: {', '.join(sorted(macs))} for IP {ip}",
                        impact="Packets directed to this IP will experience flapping routes, dropped packets, or possible session interception.",
                        remediation="Check DHCP scope settings and static IP assignments on local network adapters to eliminate overlapping IP configurations.",
                        created_at=now
                    )
                )

        # Rule SEC-003: DNS Resolver Hygiene & Encryption Audit
        dns_servers = get_dns_servers()
        for dns_ip in dns_servers:
            is_secure_known = dns_ip in ("1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4", "9.9.9.9", "149.112.112.112")
            is_local_gw = (dns_ip == gw_ip)
            is_loopback = dns_ip.startswith("127.") or dns_ip == "::1"
            is_private = dns_ip.startswith("192.168.") or dns_ip.startswith("10.") or dns_ip.startswith("172.16.")

            # Only flag as non-standard if external third-party unencrypted IP
            if not is_secure_known and not is_local_gw and not is_loopback and not is_private:
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-003",
                        severity="low",
                        title=f"Non-Standard External DNS Resolver in Use ({dns_ip})",
                        category="dns_hygiene",
                        description="System queries are resolving through an unverified external DNS server without standard DoH/DoT privacy protections.",
                        evidence=f"Active DNS Nameserver: {dns_ip}",
                        impact="Unencrypted DNS queries can be logged, profiled, or redirected by upstream ISPs and intermediate carriers.",
                        remediation="Configure DNS-over-HTTPS (DoH) or switch to verified privacy-centric DNS providers (Cloudflare 1.1.1.1 or Quad9 9.9.9.9).",
                        created_at=now
                    )
                )

        # Port-Based Heuristics (Exposed Services)
        if open_ports:
            for p in open_ports:
                port_num = p.get("port")
                target = p.get("target")
                banner = (p.get("banner") or "").strip()

                # Rule SEC-004: Telnet (Port 23)
                if port_num == 23:
                    is_confirmed = bool(banner and any(kw in banner.lower() for kw in ["login", "telnet", "welcome", "user"]))
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-004",
                            severity="critical" if is_confirmed else "high",
                            title="Unencrypted Cleartext Telnet Service Exposed (Port 23)",
                            category="insecure_protocol",
                            description=f"A legacy unencrypted Telnet terminal service was detected active on {target}:23.",
                            evidence=f"Port 23 open on {target}. Banner: '{banner or 'No banner grabbed'}'",
                            impact="Telnet transmits authentication credentials and commands across the network in plaintext, allowing immediate eavesdropping.",
                            remediation="Immediately disable Telnet daemon and migrate management sessions to SSH (Port 22) with key-based authentication.",
                            created_at=now
                        )
                    )

                # Rule SEC-005: Plaintext FTP (Port 21)
                elif port_num == 21:
                    has_tls = bool(banner and any(kw in banner.lower() for kw in ["tls", "ssl", "ftps"]))
                    if not has_tls:
                        findings.append(
                            SecurityFindingSchema(
                                rule_id="SEC-005",
                                severity="medium",
                                title="Unencrypted Plain FTP Service Exposed (Port 21)",
                                category="insecure_protocol",
                                description=f"Standard FTP service is active on {target}:21 without verified TLS enforcement.",
                                evidence=f"Port 21 open on {target}. Banner: '{banner or 'No banner grabbed'}'",
                                impact="FTP transmits usernames and passwords in cleartext. Transferred data can be intercepted on unencrypted networks.",
                                remediation="Switch to SFTP (over SSH) or enforce FTPS (Explicit TLS) with mandatory encryption.",
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
                            title=f"Database Service Exposed on Network ({db_name})",
                            category="database_exposure",
                            description=f"{db_name} listener (Port {port_num}) is exposed directly on {target}.",
                            evidence=f"Port {port_num} ({db_name}) active. Banner: '{banner or 'Standard DB Protocol'}'",
                            impact="Direct database network exposure increases risk of brute-force attacks, unauthenticated probing, and data exfiltration.",
                            remediation="Bind database daemon exclusively to localhost (127.0.0.1) or restrict network access using local firewall rules and VPN tunnels.",
                            created_at=now
                        )
                    )

                # Rule SEC-007: Gateway Admin HTTP
                elif port_num == 80 and target == gw_ip:
                    # Check if port 80 redirects to HTTPS
                    redirects_to_https = bool(banner and "https://" in banner.lower())
                    if not redirects_to_https:
                        findings.append(
                            SecurityFindingSchema(
                                rule_id="SEC-007",
                                severity="medium",
                                title="Gateway Management Portal Accessible via Cleartext HTTP",
                                category="service_exposure",
                                description=f"Default gateway router {gw_ip} has HTTP port 80 open without verified forced redirection to HTTPS.",
                                evidence=f"Port 80 open on {gw_ip}. Response Banner: '{banner or 'HTTP listener active'}'",
                                impact="Router administrative sessions conducted over plain HTTP can expose admin passwords to local eavesdroppers.",
                                remediation="Log into router administration settings, enable HTTPS web management, and disable cleartext HTTP access.",
                                created_at=now
                            )
                        )

                # Rule SEC-008: SMB / Windows File Sharing (Port 445 / 139)
                elif port_num in (445, 139):
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-008",
                            severity="medium",
                            title=f"SMB / Windows File Sharing Exposed (Port {port_num})",
                            category="file_sharing_exposure",
                            description=f"Server Message Block (SMB) network service is active on {target}:{port_num}.",
                            evidence=f"Port {port_num} active on {target}",
                            impact="Unprotected or misconfigured SMB shares can expose internal files and provide opportunities for lateral movement attacks.",
                            remediation="Ensure SMB signing is required, audit anonymous access, and restrict SMB to private subnets using Windows Defender Firewall.",
                            created_at=now
                        )
                    )

                # Rule SEC-009: Remote Desktop Protocol (Port 3389)
                elif port_num == 3389:
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-009",
                            severity="medium",
                            title="Remote Desktop Protocol (RDP) Exposed (Port 3389)",
                            category="remote_access_exposure",
                            description=f"Microsoft Remote Desktop listener is active on {target}:3389.",
                            evidence=f"Port 3389 open on {target}",
                            impact="RDP ports exposed across local or routed subnets are frequent targets for automated dictionary and brute-force attacks.",
                            remediation="Enforce Network Level Authentication (NLA), implement account lockout policies, and access RDP solely through secure VPN.",
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
                    description="No rogue gateways, IP conflicts, or insecure unencrypted legacy management ports were detected.",
                    evidence=f"Gateway {gw_ip} baseline verified ({effective_baseline or 'Verified'}), {len(devices)} active devices analyzed.",
                    impact="Local network segment operates within healthy configuration parameters.",
                    remediation="Maintain regular device discovery sweeps and keep router firmware updated.",
                    created_at=now
                )
            )

        return findings

security_auditor = SecurityAuditor()
