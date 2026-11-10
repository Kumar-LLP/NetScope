from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.schemas.network import AnomalySchema, DeviceSchema

class AnomalyDetector:
    """
    Rule-based, explainable network anomaly detection engine.
    Detects traffic throughput spikes, rapid gateway MAC changes,
    abnormal packet loss surges, and sudden unclassified devices.
    """
    def __init__(self):
        # Tunable thresholds
        self.traffic_spike_threshold_kbps = 50_000.0 # 50 MB/s burst
        self.packet_loss_surge_pct = 40.0 # 40% loss
        self.latency_surge_ms = 300.0 # 300 ms RTT
        self._historical_traffic: List[float] = []

    def tune_thresholds(
        self,
        traffic_spike_kbps: Optional[float] = None,
        packet_loss_pct: Optional[float] = None,
        latency_surge_ms: Optional[float] = None
    ):
        """Allows operator to calibrate anomaly detection thresholds."""
        if traffic_spike_kbps is not None and traffic_spike_kbps > 0:
            self.traffic_spike_threshold_kbps = traffic_spike_kbps
        if packet_loss_pct is not None and 0 <= packet_loss_pct <= 100:
            self.packet_loss_surge_pct = packet_loss_pct
        if latency_surge_ms is not None and latency_surge_ms > 0:
            self.latency_surge_ms = latency_surge_ms

    def detect_anomalies(
        self,
        current_download_kbps: float,
        current_upload_kbps: float,
        current_latency_ms: Optional[float],
        packet_loss_pct: float,
        devices: List[DeviceSchema],
        gateway_mac_changed: bool = False,
        gateway_ip: Optional[str] = None,
        current_gw_mac: Optional[str] = None
    ) -> List[AnomalySchema]:
        """
        Evaluates active network telemetry and inventory against deterministic anomaly rules.
        """
        anomalies: List[AnomalySchema] = []
        now = datetime.now(timezone.utc)

        # 1. Traffic Spike Anomaly
        total_kbps = current_download_kbps + current_upload_kbps
        self._historical_traffic.append(total_kbps)
        if len(self._historical_traffic) > 50:
            self._historical_traffic.pop(0)

        # Compute moving baseline
        if len(self._historical_traffic) >= 5:
            avg_traffic = sum(self._historical_traffic[:-1]) / (len(self._historical_traffic) - 1)
            if total_kbps > self.traffic_spike_threshold_kbps or (avg_traffic > 500 and total_kbps > (avg_traffic * 3.5)):
                anomalies.append(
                    AnomalySchema(
                        anomaly_type="traffic_spike",
                        severity="medium",
                        title="Unusual Throughput Spike Detected",
                        description="Observed network throughput abruptly exceeded the normal baseline threshold.",
                        evidence=(
                            f"Current Throughput: {round(total_kbps / 1024.0, 2)} MB/s "
                            f"(Download: {round(current_download_kbps / 1024.0, 2)} MB/s, "
                            f"Upload: {round(current_upload_kbps / 1024.0, 2)} MB/s). "
                            f"Historical Average: {round(avg_traffic / 1024.0, 2)} MB/s."
                        ),
                        target="Active Network Adapter",
                        confidence="confirmed",
                        threshold_trigger=f"Throughput > {self.traffic_spike_threshold_kbps} KB/s or > 3.5x average",
                        detected_at=now,
                        status="active"
                    )
                )

        # 2. Unexpected Gateway Change
        if gateway_mac_changed:
            anomalies.append(
                AnomalySchema(
                    anomaly_type="gateway_mac_change",
                    severity="critical",
                    title="Unexpected Default Gateway MAC Divergence",
                    description="The hardware MAC address of the default router has changed from the confirmed baseline.",
                    evidence=f"Gateway IP: {gateway_ip or 'unknown'}, Detected MAC: {current_gw_mac or 'unknown'}",
                    target=str(gateway_ip or "Default Gateway"),
                    confidence="confirmed",
                    threshold_trigger="Gateway ARP baseline mismatch",
                    detected_at=now,
                    status="active"
                )
            )

        # 3. Network Degradation / Packet Loss Surge
        if packet_loss_pct >= self.packet_loss_surge_pct:
            anomalies.append(
                AnomalySchema(
                    anomaly_type="packet_loss_surge",
                    severity="high",
                    title="Severe Packet Loss Surge",
                    description="High packet loss indicates transport instability, upstream carrier congestion, or interface dropping.",
                    evidence=f"Measured Packet Loss: {packet_loss_pct:.1f}% (Threshold: {self.packet_loss_surge_pct:.1f}%)",
                    target="Local Uplink",
                    confidence="confirmed",
                    threshold_trigger=f"Packet Loss >= {self.packet_loss_surge_pct}%",
                    detected_at=now,
                    status="active"
                )
            )

        # 4. Latency Jitter Anomaly
        if current_latency_ms is not None and current_latency_ms >= self.latency_surge_ms:
            anomalies.append(
                AnomalySchema(
                    anomaly_type="excessive_latency",
                    severity="medium",
                    title="Abnormal Latency Spike",
                    description="Round-trip latency to the external uplink exceeded acceptable performance limits.",
                    evidence=f"Measured Latency: {current_latency_ms:.1f} ms (Threshold: {self.latency_surge_ms:.1f} ms)",
                    target="Internet Uplink",
                    confidence="confirmed",
                    threshold_trigger=f"Latency >= {self.latency_surge_ms} ms",
                    detected_at=now,
                    status="active"
                )
            )

        # 5. Sudden Appearance of Unknown / Untrusted Devices
        unknown_devices = [d for d in devices if d.vendor == "Unknown" and not d.is_trusted and d.status == "online"]
        if len(unknown_devices) >= 3:
            anomalies.append(
                AnomalySchema(
                    anomaly_type="unknown_device_cluster",
                    severity="low",
                    title="Cluster of Unidentified Devices on Subnet",
                    description="Multiple online devices have unidentifiable MAC OUI hardware vendors.",
                    evidence=f"Found {len(unknown_devices)} unidentified active hosts: {', '.join(d.ip for d in unknown_devices[:5])}",
                    target=f"{len(unknown_devices)} Unidentified Hosts",
                    confidence="potential",
                    threshold_trigger=">= 3 unknown devices detected",
                    detected_at=now,
                    status="active"
                )
            )

        return anomalies

anomaly_detector = AnomalyDetector()
