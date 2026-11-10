import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.entities import (
    IntelligenceEventModel,
    DeviceObservationModel,
    NetworkDeviceModel,
    NetworkMetricModel,
    PortDiagnosticModel,
    ApplicationSettingsModel
)
from app.network.gateway import get_default_gateway, get_gateway_mac, get_dns_servers

def utcnow():
    return datetime.now(timezone.utc)

class NetworkIntelligenceEngine:
    """
    Central Network Intelligence Service.
    Consumes normalized evidence from device discovery, traffic monitoring,
    packet analysis, port diagnostics, DNS diagnostics, gateway monitoring,
    and historical device observations.
    Executes explainable correlation rules with strictly evidence-backed classifications.
    """

    async def evaluate_network_evidence(self, db: AsyncSession) -> List[IntelligenceEventModel]:
        """
        Evaluates active multi-domain evidence against deterministic correlation rules.
        Persists newly correlated intelligence events avoiding duplicates.
        """
        now = utcnow()
        events_to_record: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # EVIDENCE DOMAIN 1: Device Observations & DHCP / IP Conflicts
        # -------------------------------------------------------------
        recent_window = now - timedelta(hours=2)
        obs_res = await db.execute(
            select(DeviceObservationModel)
            .where(DeviceObservationModel.timestamp >= recent_window)
            .order_by(desc(DeviceObservationModel.timestamp))
        )
        recent_observations = obs_res.scalars().all()

        # Group observations by IP and MAC
        mac_to_ips: Dict[str, set] = {}
        ip_to_macs: Dict[str, set] = {}
        for obs in recent_observations:
            if obs.mac_address and obs.ip_address:
                mac_clean = obs.mac_address.upper()
                mac_to_ips.setdefault(mac_clean, set()).add(obs.ip_address)
                ip_to_macs.setdefault(obs.ip_address, set()).add(mac_clean)

        # Rule NETINT-CONF-01: Simultaneous IP Address Conflict
        for ip, macs in ip_to_macs.items():
            if len(macs) > 1:
                event_key = f"NETINT-IPCONF-{ip}"
                events_to_record.append({
                    "event_id": event_key,
                    "category": "device",
                    "severity": "high",
                    "confidence": "confirmed",
                    "timestamp": now,
                    "affected_device_ip": ip,
                    "affected_device_mac": ", ".join(sorted(macs)),
                    "evidence_references": json.dumps({
                        "conflicting_ip": ip,
                        "observed_mac_addresses": sorted(list(macs)),
                        "observation_count": len(macs),
                        "time_window": "past 2 hours"
                    }),
                    "explanation": (
                        f"Multiple physical MAC addresses ({', '.join(sorted(macs))}) were observed responding "
                        f"to the same IP address ({ip}) within the current observation window. This indicates an active "
                        "IP collision or rapid overlapping DHCP leases."
                    ),
                    "recommended_action": (
                        "Inspect DHCP server scope leases and verify static IP allocations on connected network hosts "
                        "to resolve conflicting address assignments."
                    )
                })

        # Rule NETINT-DHCP-02: DHCP Lease Transition
        for mac, ips in mac_to_ips.items():
            if len(ips) > 1:
                event_key = f"NETINT-DHCP-{mac}"
                events_to_record.append({
                    "event_id": event_key,
                    "category": "device",
                    "severity": "info",
                    "confidence": "confirmed",
                    "timestamp": now,
                    "affected_device_ip": sorted(list(ips))[-1],
                    "affected_device_mac": mac,
                    "evidence_references": json.dumps({
                        "mac_address": mac,
                        "associated_ips": sorted(list(ips)),
                        "transition_count": len(ips)
                    }),
                    "explanation": (
                        f"Hardware device with MAC {mac} has transitioned between multiple IP addresses "
                        f"({', '.join(sorted(ips))}). Consistent with standard DHCP lease renewal or interface roaming."
                    ),
                    "recommended_action": (
                        "If this device requires a fixed network location (e.g., printer, server), configure a permanent "
                        "DHCP reservation in your local router."
                    )
                })

        # -------------------------------------------------------------
        # EVIDENCE DOMAIN 2: Gateway Layer-2 Verification
        # -------------------------------------------------------------
        gw_ip = get_default_gateway()
        gw_mac = get_gateway_mac(gw_ip) if gw_ip else None
        if gw_ip and gw_mac:
            res_status = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_status"))
            res_mac = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_mac"))
            s_row = res_status.scalars().first()
            m_row = res_mac.scalars().first()

            if s_row and s_row.value == "confirmed" and m_row and m_row.value:
                baseline_mac_clean = m_row.value.upper()
                active_mac_clean = gw_mac.upper()
                if baseline_mac_clean != active_mac_clean:
                    event_key = f"NETINT-GW-{gw_ip}"
                    events_to_record.append({
                        "event_id": event_key,
                        "category": "gateway",
                        "severity": "high",
                        "confidence": "high",
                        "timestamp": now,
                        "affected_device_ip": gw_ip,
                        "affected_device_mac": active_mac_clean,
                        "evidence_references": json.dumps({
                            "gateway_ip": gw_ip,
                            "confirmed_baseline_mac": baseline_mac_clean,
                            "detected_active_mac": active_mac_clean
                        }),
                        "explanation": (
                            f"The Layer-2 hardware address of default gateway {gw_ip} changed from confirmed baseline "
                            f"({baseline_mac_clean}) to ({active_mac_clean}). This observation is consistent with physical "
                            "router replacement, Wi-Fi mesh access point handover, or an active ARP cache poisoning condition."
                        ),
                        "recommended_action": (
                            "Verify router physical label and switch ARP tables. If the router or AP was legitimately upgraded, "
                            "re-baseline the gateway in the Security panel."
                        )
                    })

        # -------------------------------------------------------------
        # EVIDENCE DOMAIN 3: Port Diagnostics Exposure
        # -------------------------------------------------------------
        ports_res = await db.execute(
            select(PortDiagnosticModel)
            .where(PortDiagnosticModel.state == "open")
            .order_by(desc(PortDiagnosticModel.created_at))
            .limit(20)
        )
        open_ports = ports_res.scalars().all()
        for p in open_ports:
            if p.port in (21, 23):
                service_name = "Telnet" if p.port == 23 else "FTP"
                event_key = f"NETINT-PORT-{p.target_ip}-{p.port}"
                events_to_record.append({
                    "event_id": event_key,
                    "category": "port",
                    "severity": "medium",
                    "confidence": "confirmed",
                    "timestamp": now,
                    "affected_device_ip": p.target_ip,
                    "affected_device_mac": None,
                    "evidence_references": json.dumps({
                        "target_ip": p.target_ip,
                        "open_port": p.port,
                        "service": service_name,
                        "banner": p.banner or "No banner grabbed"
                    }),
                    "explanation": (
                        f"Service {service_name} on port {p.port} is accepting connections in cleartext on {p.target_ip}. "
                        "Passwords and session traffic sent to this service are unencrypted."
                    ),
                    "recommended_action": (
                        f"Disable {service_name} and replace with an encrypted management protocol (SSH on port 22 or SFTP)."
                    )
                })

        # -------------------------------------------------------------
        # EVIDENCE DOMAIN 4: Traffic & Latency Operating Tolerances
        # -------------------------------------------------------------
        metrics_res = await db.execute(
            select(NetworkMetricModel)
            .order_by(desc(NetworkMetricModel.timestamp))
            .limit(10)
        )
        recent_metrics = metrics_res.scalars().all()
        if recent_metrics:
            latest = recent_metrics[0]
            if latest.packet_loss_pct >= 25.0:
                event_key = f"NETINT-LOSS-{latest.interface_name or 'uplink'}"
                events_to_record.append({
                    "event_id": event_key,
                    "category": "traffic",
                    "severity": "medium",
                    "confidence": "confirmed",
                    "timestamp": now,
                    "affected_device_ip": None,
                    "affected_device_mac": None,
                    "evidence_references": json.dumps({
                        "measured_packet_loss_pct": latest.packet_loss_pct,
                        "interface": latest.interface_name,
                        "latency_ms": latest.latency_ms
                    }),
                    "explanation": (
                        f"Observed network transport packet loss reached {latest.packet_loss_pct:.1f}%, exceeding the "
                        "25% operational stability tolerance threshold."
                    ),
                    "recommended_action": (
                        "Inspect local Ethernet cabling, check Wi-Fi signal-to-noise ratio, or test upstream modem connection."
                    )
                })

        # -------------------------------------------------------------
        # PERSIST EVENTS TO DATABASE (Deduplicated on event_id)
        # -------------------------------------------------------------
        saved_events: List[IntelligenceEventModel] = []
        try:
            for item in events_to_record:
                q = select(IntelligenceEventModel).where(IntelligenceEventModel.event_id == item["event_id"])
                res = await db.execute(q)
                existing = res.scalars().first()

                if existing:
                    # Update evidence references and timestamp
                    existing.timestamp = item["timestamp"]
                    existing.evidence_references = item["evidence_references"]
                    existing.explanation = item["explanation"]
                    saved_events.append(existing)
                else:
                    new_event = IntelligenceEventModel(
                        event_id=item["event_id"],
                        category=item["category"],
                        severity=item["severity"],
                        confidence=item["confidence"],
                        timestamp=item["timestamp"],
                        affected_device_ip=item["affected_device_ip"],
                        affected_device_mac=item["affected_device_mac"],
                        evidence_references=item["evidence_references"],
                        explanation=item["explanation"],
                        recommended_action=item["recommended_action"],
                        investigation_status="unreviewed"
                    )
                    db.add(new_event)
                    saved_events.append(new_event)

            await db.commit()
            return saved_events
        except Exception as e:
            await db.rollback()
            raise RuntimeError(f"Database error during intelligence event persistence: {str(e)}") from e

    async def list_events(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[IntelligenceEventModel]:
        """Queries persisted intelligence events with optional filtering."""
        stmt = select(IntelligenceEventModel).order_by(desc(IntelligenceEventModel.timestamp))

        if category:
            stmt = stmt.where(IntelligenceEventModel.category == category)
        if severity:
            stmt = stmt.where(IntelligenceEventModel.severity == severity)
        if status:
            stmt = stmt.where(IntelligenceEventModel.investigation_status == status)

        stmt = stmt.limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def update_event_status(
        self,
        db: AsyncSession,
        event_id: str,
        new_status: str
    ) -> Optional[IntelligenceEventModel]:
        """Updates the investigation status of a specific intelligence event."""
        stmt = select(IntelligenceEventModel).where(IntelligenceEventModel.event_id == event_id)
        res = await db.execute(stmt)
        event = res.scalars().first()
        if not event:
            return None

        event.investigation_status = new_status
        if new_status in ("resolved", "dismissed"):
            event.resolved_at = utcnow()
        await db.commit()
        return event

network_intelligence_engine = NetworkIntelligenceEngine()
