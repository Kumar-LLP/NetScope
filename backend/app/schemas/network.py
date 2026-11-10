from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    platform: str
    db_connected: bool
    timestamp: datetime

class InterfaceSchema(BaseModel):
    name: str
    ip_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    netmask: Optional[str] = None
    broadcast: Optional[str] = None
    mac_address: Optional[str] = None
    is_default: bool = False
    is_up: bool = True
    speed_mbps: Optional[int] = None
    interface_type: Optional[str] = "ethernet" # 'ethernet', 'wifi', 'loopback', 'virtual', 'vpn'
    index: Optional[int] = None

class OverviewResponse(BaseModel):
    active_interface: Optional[str] = None
    local_ip: Optional[str] = None
    public_ip: Optional[str] = None
    subnet_mask: Optional[str] = None
    cidr: Optional[str] = None
    default_gateway: Optional[str] = None
    gateway_mac: Optional[str] = None
    dns_servers: List[str] = []
    internet_connected: bool = True
    gateway_connected: bool = True
    current_latency_ms: Optional[float] = None
    tcp_latency_ms: Optional[float] = None
    packet_loss_pct: float = 0.0
    download_kbps: float = 0.0
    upload_kbps: float = 0.0
    health_score: int = 100
    connected_devices_count: int = 0

class DeviceDiscoverRequest(BaseModel):
    cidr: Optional[str] = None
    timeout_seconds: Optional[int] = Field(default=10, ge=1, le=60)

class DeviceSchema(BaseModel):
    id: Optional[int] = None
    ip: str
    mac: Optional[str] = None
    vendor: str = "Unknown"
    hostname: Optional[str] = None
    custom_name: Optional[str] = None
    notes: Optional[str] = None
    category: str = "workstation"
    is_trusted: bool = False
    is_gateway: bool = False
    is_local_host: bool = False
    status: str = "online"
    response_time_ms: Optional[float] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

class DeviceUpdateRequest(BaseModel):
    custom_name: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = None
    is_trusted: Optional[bool] = None

class DeviceDiscoverResponse(BaseModel):
    scan_id: str
    total_targets: int = 0
    total_scanned: int = 0
    total_discovered: int
    duration_seconds: float
    status: str = "completed"
    devices: List[DeviceSchema]

class TopologyNodeData(BaseModel):
    label: str
    subLabel: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    vendor: Optional[str] = None
    status: str = "online"
    nodeType: str # 'internet', 'gateway', 'host', 'device', 'dns'

class TopologyNode(BaseModel):
    id: str
    type: str = "customNode"
    data: TopologyNodeData
    position: Dict[str, float]

class TopologyEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False
    style: Optional[Dict[str, Any]] = None

class TopologyResponse(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]

class PingRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    count: int = Field(default=4, ge=1, le=20)
    timeout_ms: int = Field(default=1000, ge=100, le=5000)

class PingResponse(BaseModel):
    target: str
    packets_transmitted: int
    packets_received: int
    packet_loss_pct: float
    min_rtt_ms: Optional[float] = None
    avg_rtt_ms: Optional[float] = None
    max_rtt_ms: Optional[float] = None
    stddev_rtt_ms: Optional[float] = None
    raw_output: str

class DNSRequest(BaseModel):
    domain: str = Field(..., min_length=1, max_length=255)
    record_type: str = Field(default="A", max_length=10)
    custom_server: Optional[str] = None

class DNSRecord(BaseModel):
    record_type: str
    value: str
    ttl: Optional[int] = None

class DNSResponse(BaseModel):
    domain: str
    record_type: Optional[str] = "ALL"
    resolved_by: str
    query_time_ms: float
    records: Dict[str, List[str]] = {}
    status: str = "success" # 'success', 'no_answer', 'nxdomain', 'timeout', 'resolver_error'
    statuses_by_type: Dict[str, str] = {}

class TracerouteRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    max_hops: int = Field(default=30, ge=1, le=50)
    timeout_ms: int = Field(default=2000, ge=500, le=5000)

class TracerouteHop(BaseModel):
    hop: int
    ip: Optional[str] = None
    hostname: Optional[str] = None
    rtt_ms: Optional[float] = None
    timed_out: bool = False

class TracerouteResponse(BaseModel):
    target: str
    total_hops: int
    hops: List[TracerouteHop]
    status: str = "completed" # 'completed', 'timed_out', 'error'
    error_message: Optional[str] = None

class IPInfoRequest(BaseModel):
    ip_or_cidr: str = Field(..., min_length=3, max_length=45)

class IPInfoResponse(BaseModel):
    input: str
    ip_version: int
    network_address: str
    netmask: str
    wildcard_mask: Optional[str] = None
    prefix_length: Optional[int] = None
    broadcast_address: Optional[str] = None
    usable_host_range: List[str]
    total_hosts: int
    usable_hosts: int
    is_private: bool
    is_loopback: bool
    binary_representation: str

class PortScanRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    ports: List[int] = Field(..., min_length=1, max_length=100)
    timeout_ms: int = Field(default=500, ge=100, le=3000)
    authorized: bool = Field(default=False)

    @field_validator("ports")
    @classmethod
    def validate_port_range(cls, v: List[int]) -> List[int]:
        for p in v:
            if not isinstance(p, int) or p < 1 or p > 65535:
                raise ValueError(f"Port number {p} is out of valid range (1-65535).")
        return v

    @field_validator("target")
    @classmethod
    def sanitize_target(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Target host cannot be empty.")
        if any(c in clean for c in [";", "&", "|", "`", "$", " ", "\n", "\r", "<", ">"]):
            raise ValueError("Target contains illegal shell or control characters.")
        return clean

class PortResult(BaseModel):
    port: int
    state: str # 'open', 'closed', 'filtered', 'error', 'not_scanned', 'timed_out'
    service: Optional[str] = None
    banner: Optional[str] = None
    rtt_ms: Optional[float] = None

class PortScanResponse(BaseModel):
    target: str
    total_scanned: int
    open_count: int
    results: List[PortResult]
    status: str = "completed" # 'completed', 'partial', 'timed_out', 'cancelled'
    requested_ports: Optional[int] = None
    completed_ports: Optional[int] = None
    remaining_ports: Optional[int] = 0
    elapsed_seconds: Optional[float] = None
    timed_out: bool = False

class PaginatedDevicesResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    devices: List[DeviceSchema]

class PacketStats(BaseModel):
    total_packets: int = 0
    tcp_packets: int = 0
    udp_packets: int = 0
    icmp_packets: int = 0
    dns_packets: int = 0
    other_packets: int = 0
    total_bytes: int = 0
    protocols: Dict[str, int] = {}
    duration_seconds: float = 0.0

class PacketCaptureStatusResponse(BaseModel):
    is_capturing: bool = False
    supported: bool = True
    session_id: Optional[str] = None
    interface_name: Optional[str] = None
    stats: PacketStats
    note: Optional[str] = None
    error_message: Optional[str] = None

class AnomalySchema(BaseModel):
    id: Optional[int] = None
    anomaly_type: str # 'traffic_spike', 'gateway_mac_change', 'unknown_device', 'excessive_latency'
    severity: str # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    evidence: str
    target: Optional[str] = None
    confidence: str = "confirmed" # 'confirmed', 'potential'
    threshold_trigger: Optional[str] = None
    detected_at: Optional[datetime] = None
    status: str = "active" # 'active', 'acknowledged', 'resolved', 'false_positive'
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None

class IntelligenceEventSchema(BaseModel):
    id: Optional[int] = None
    event_id: str
    category: str
    severity: str
    confidence: str
    timestamp: datetime
    affected_device_ip: Optional[str] = None
    affected_device_mac: Optional[str] = None
    evidence_references: str
    explanation: str
    recommended_action: str
    investigation_status: str = "unreviewed"
    resolved_at: Optional[datetime] = None

class DeviceObservationSchema(BaseModel):
    id: Optional[int] = None
    device_id: Optional[int] = None
    ip_address: str
    mac_address: Optional[str] = None
    interface_name: Optional[str] = None
    timestamp: datetime
    scan_id: Optional[str] = None
    source: str = "arp"
    response_status: str = "responding"
    confidence: str = "confirmed"

class LearningTopic(BaseModel):
    id: str
    title: str
    category: str
    summary: str
    explanation: str
    how_netscope_measures: str
    current_value: Optional[str] = None
    recommended_reading: Optional[str] = None

class SecurityFindingSchema(BaseModel):
    id: Optional[int] = None
    rule_id: str
    severity: str # 'critical', 'high', 'medium', 'low', 'info'
    title: str
    category: str
    description: str
    evidence: str
    impact: str
    remediation: str
    target: Optional[str] = None
    confidence: str = "potential" # 'confirmed', 'potential', 'informational'
    status: str = "active" # 'active', 'acknowledged', 'resolved'
    created_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class GatewayBaselineResponse(BaseModel):
    gateway_ip: Optional[str] = None
    detected_mac: Optional[str] = None
    confirmed_mac: Optional[str] = None
    baseline_mac: Optional[str] = None
    status: str # 'confirmed', 'unconfirmed', 'mismatch'
    confirmed_at: Optional[str] = None

class SelectInterfaceRequest(BaseModel):
    interface_name: str

class TelemetryBandwidth(BaseModel):
    download_bytes_per_sec: float
    upload_bytes_per_sec: float
    download_formatted: str
    upload_formatted: str

class TelemetryMessage(BaseModel):
    type: str = "telemetry_update"
    timestamp: str
    bandwidth: TelemetryBandwidth
    ping_ms: Optional[float] = None
    tcp_latency_ms: Optional[float] = None
    packet_loss_pct: float = 0.0
    interface: str
    is_connected: bool
    gateway_connected: Optional[bool] = None
