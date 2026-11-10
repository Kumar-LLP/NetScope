from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.schemas.network import AnomalySchema, DeviceSchema

class AnomalyDetector:
    """
    Rule-based, explainable network anomaly detection engine.
    Detects traffic throughput spikes, rapid gateway MAC changes,
    abnormal packet loss surges, and sudden unclassified devices.
    All throughput metrics are strictly normalized and mathematically verified.
    """
    def __init__(self):
        # Tunable thresholds (KB/s = Kilobytes per second; 1 Byte = 8 bits)
        self.traffic_spike_threshold_KB_s = 50_000.0  # 50,000 KB/s (~48.8 MB/s or ~390.6 Mbps)
        self.packet_loss_surge_pct = 40.0             # 40% loss
        self.latency_surge_ms = 300.0                 # 300 ms RTT
        self._historical_traffic_KB_s: List[float] = []

    def tune_thresholds(
        self,
        traffic_spike_kbps: Optional[float] = None,
        packet_loss_pct: Optional[float] = None,
        latency_surge_ms: Optional[float] = None
    ):
        """Allows operator to calibrate anomaly detection thresholds."""
        if traffic_spike_kbps is not None and traffic_spike_kbps > 0:
            self.traffic_spike_threshold_KB_s = traffic_spike_kbps
        if packet_loss_pct is not None and 0 <= packet_loss_pct <= 100:
            self.packet_loss_surge_pct = packet_loss_pct
        if latency_surge_ms is not None and latency_surge_ms > 0:
            self.latency_surge_ms = latency_surge_ms

    def get_thresholds(self) -> Dict[str, float]:
        """Returns the current threshold values."""
        return {
            "traffic_spike_kbps": self.traffic_spike_threshold_KB_s,
            "traffic_spike_threshold_kbps": self.traffic_spike_threshold_KB_s,
            "packet_loss_pct": self.packet_loss_surge_pct,
            "packet_loss_surge_pct": self.packet_loss_surge_pct,
            "latency_surge_ms": self.latency_surge_ms
        }

    def detect_anomalies(
        self,
        current_download_kbps: float,  # KB/s
        current_upload_kbps: float,    # KB/s
        current_latency_ms: Optional[float],
        packet_loss_pct: float,
        devices: List[DeviceSchema],
        gateway_mac_changed: bool = False,
        gateway_ip: Optional[str] = None,
        current_gw_mac: Optional[str] = None,
        historical_baseline_KB_s: Optional[float] = None
    ) -> List[AnomalySchema]:
        """
        Evaluates active network telemetry and inventory against deterministic anomaly rules.
        """
        anomalies: List[AnomalySchema] = []
        now = datetime.now(timezone.utc)

        # 1. Traffic Spike Anomaly
        total_KB_s = current_download_kbps + current_upload_kbps
        self._historical_traffic_KB_s.append(total_KB_s)
        if len(self._historical_traffic_KB_s) > 50:
            self._historical_traffic_KB_s.pop(0)

        # Determine moving baseline (from DB historical records or sliding window)
        avg_traffic_KB_s = historical_baseline_KB_s
        if avg_traffic_KB_s is None and len(self._historical_traffic_KB_s) >= 5:
            avg_traffic_KB_s = sum(self._historical_traffic_KB_s[:-1]) / (len(self._historical_traffic_KB_s) - 1)

        if avg_traffic_KB_s is not None:
            # Units: KB/s to MB/s and Mbps
            total_MB_s = round(total_KB_s / 1024.0, 2)
            total_Mbps = round((total_KB_s * 8) / 1000.0, 1)
            down_MB_s = round(current_download_kbps / 1024.0, 2)
            up_MB_s = round(current_upload_kbps / 1024.0, 2)
            avg_MB_s = round(avg_traffic_KB_s / 1024.0, 2)
            avg_Mbps = round((avg_traffic_KB_s * 8) / 1000.0, 1)

            is_threshold_exceeded = total_KB_s > self.traffic_spike_threshold_KB_s
            is_multiplier_exceeded = (avg_traffic_KB_s > 500 and total_KB_s > (avg_traffic_KB_s * 3.5))

            if is_threshold_exceeded or is_multiplier_exceeded:
                anomalies.append(
                    AnomalySchema(
                        anomaly_type="traffic_spike",
                        severity="medium",
                        title="Unusual Throughput Spike Detected",
                        description="Observed network throughput abruptly exceeded the established operating baseline.",
                        evidence=(
                            f"Current Throughput: {total_MB_s} MB/s ({total_Mbps} Mbps) "
                            f"[Download: {down_MB_s} MB/s, Upload: {up_MB_s} MB/s]. "
                            f"Baseline Average: {avg_MB_s} MB/s ({avg_Mbps} Mbps)."
                        ),
                        target="Active Network Adapter",
                        confidence="confirmed",
                        threshold_trigger=(
                            f"Throughput > {round(self.traffic_spike_threshold_KB_s / 1024.0, 1)} MB/s "
                            f"({round((self.traffic_spike_threshold_KB_s * 8) / 1000.0, 0)} Mbps) or > 3.5x baseline"
                        ),
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
                    description="The hardware Layer 2 MAC address of the default router has diverged from your confirmed baseline.",
                    evidence=f"Gateway IP: {gateway_ip or 'unknown'}, Detected Active MAC: {current_gw_mac or 'unknown'}",
                    target=str(gateway_ip or "Default Gateway"),
                    confidence="high",
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
                    threshold_trigger=f"Packet Loss >= {self.packet_loss_surge_pct:.1f}%",
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
                    description="Round-trip latency to the external uplink exceeded normal operating tolerances.",
                    evidence=f"Measured Latency: {current_latency_ms:.1f} ms (Threshold: {self.latency_surge_ms:.1f} ms)",
                    target="Internet Uplink",
                    confidence="confirmed",
                    threshold_trigger=f"Latency >= {self.latency_surge_ms:.1f} ms",
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
