from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.schemas.network import SecurityFindingSchema, DeviceSchema
from app.network.gateway import get_default_gateway, get_gateway_mac, get_dns_servers
from app.network.interfaces import get_network_interfaces

class SecurityAuditor:
    def __init__(self):
        self.observed_gateway_mac: Optional[str] = None

    def audit_environment(
        self,
        devices: List[DeviceSchema],
        open_ports: Optional[List[Dict]] = None
    ) -> List[SecurityFindingSchema]:
        """
        Runs comprehensive security rules against active network topology,
        discovered inventory, and exposed port results.
        """
        findings: List[SecurityFindingSchema] = []
        now = datetime.now(timezone.utc)

        gw_ip = get_default_gateway()
        gw_mac = get_gateway_mac(gw_ip)

        # Rule 1: Gateway MAC Baseline & ARP Poisoning Audit
        if gw_mac:
            if self.observed_gateway_mac is None:
                self.observed_gateway_mac = gw_mac
            elif self.observed_gateway_mac != gw_mac:
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-001",
                        severity="critical",
                        title="Default Gateway MAC Address Changed (Potential ARP Poisoning)",
                        category="mitm_detection",
                        description="The hardware address of the default gateway has abruptly changed since monitoring started.",
                        evidence=f"Previous MAC: {self.observed_gateway_mac} -> New MAC: {gw_mac} on Gateway IP {gw_ip}",
                        impact="A rogue device on the local network may be executing an ARP spoofing attack to intercept your unencrypted internet traffic.",
                        remediation="Inspect the local switch/router and check ARP tables using 'arp -a'. Verify router hardware authenticity.",
                        created_at=now
                    )
                )

        # Rule 2: Duplicate IP Conflict Audit
        ip_counts: Dict[str, List[str]] = {}
        for dev in devices:
            if dev.mac:
                ip_counts.setdefault(dev.ip, []).append(dev.mac)

        for ip, macs in ip_counts.items():
            if len(set(macs)) > 1:
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-002",
                        severity="high",
                        title=f"IP Address Conflict Detected on {ip}",
                        category="ip_conflict",
                        description=f"Multiple distinct MAC addresses are claiming the same IP address ({ip}).",
                        evidence=f"MACs observed: {', '.join(macs)}",
                        impact="Packets intended for this IP will experience intermittent routing failures or session hijacking.",
                        remediation="Verify static IP assignments and configure DHCP reservations to avoid IP overlap.",
                        created_at=now
                    )
                )

        # Rule 3: DNS Resolver Configuration Audit
        dns_servers = get_dns_servers()
        for dns_ip in dns_servers:
            # Check for known secure resolvers or local router
            is_secure_known = dns_ip in ("1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4", "9.9.9.9")
            is_local_gw = (dns_ip == gw_ip)
            if not is_secure_known and not is_local_gw and not dns_ip.startswith("127."):
                findings.append(
                    SecurityFindingSchema(
                        rule_id="SEC-003",
                        severity="low",
                        title=f"Non-Standard DNS Resolver in Use ({dns_ip})",
                        category="dns_hygiene",
                        description="System queries are resolving through a third-party or ISP DNS resolver that may not support DNS-over-HTTPS (DoH).",
                        evidence=f"Active DNS Nameserver: {dns_ip}",
                        impact="DNS queries can be monitored or redirected by intermediate network providers.",
                        remediation="Consider configuring encrypted DNS (DoH/DoT) or utilizing trusted privacy-first resolvers (Cloudflare 1.1.1.1 or Quad9 9.9.9.9).",
                        created_at=now
                    )
                )

        # Rule 4: Exposed Insecure Services Audit (from port diagnostics)
        if open_ports:
            for p in open_ports:
                port_num = p.get("port")
                target = p.get("target")
                if port_num == 23:
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-004",
                            severity="high",
                            title="Unencrypted Telnet Service Exposed (Port 23)",
                            category="insecure_protocol",
                            description=f"A Telnet management interface was detected listening on {target}:23.",
                            evidence=f"Port 23 state: Open on {target}",
                            impact="Telnet transmits usernames, passwords, and commands in cleartext over the wire, allowing easy packet sniffing.",
                            remediation="Immediately disable Telnet service and migrate to SSH (Port 22) with key-based authentication.",
                            created_at=now
                        )
                    )
                elif port_num == 21:
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-005",
                            severity="medium",
                            title="Unencrypted Plain FTP Service Exposed (Port 21)",
                            category="insecure_protocol",
                            description=f"Standard FTP service was detected on {target}:21 without mandatory TLS/SSL.",
                            evidence=f"Port 21 state: Open on {target}",
                            impact="FTP credentials and transferred files can be captured by local eavesdroppers.",
                            remediation="Switch to SFTP (over SSH) or configure FTPS with forced TLS encryption.",
                            created_at=now
                        )
                    )
                elif port_num in (3306, 5432, 27017):
                    findings.append(
                        SecurityFindingSchema(
                            rule_id="SEC-006",
                            severity="medium",
                            title=f"Database Port Open on LAN ({port_num})",
                            category="database_exposure",
                            description=f"A production database listener (port {port_num}) is exposed directly on {target}.",
                            evidence=f"Port {port_num} ({p.get('service')}) open",
                            impact="Exposing databases directly to local network segments increases vulnerability to brute-force attacks and credential stuffing.",
                            remediation="Bind database listener to localhost (127.0.0.1) or restrict access using local firewall rules and VPN tunnels.",
                            created_at=now
                        )
                    )

        # Baseline Informational finding if everything is clean
        if not findings:
            findings.append(
                SecurityFindingSchema(
                    rule_id="SEC-000",
                    severity="info",
                    title="Network Security Baseline Satisfied",
                    category="audit_baseline",
                    description="No rogue gateways, IP conflicts, or insecure unencrypted legacy management ports were detected.",
                    evidence=f"Gateway {gw_ip} verified, {len(devices)} active devices analyzed.",
                    impact="Local network segment operates within healthy configuration parameters.",
                    remediation="Maintain regular device discovery sweeps and keep router firmware updated.",
                    created_at=now
                )
            )

        return findings

security_auditor = SecurityAuditor()
