export interface HealthInfo {
  status: string;
  version: string;
  platform: string;
  db_connected: boolean;
  timestamp: string;
}

export interface NetworkInterface {
  name: string;
  ip_address: string | null;
  netmask: string | null;
  broadcast: string | null;
  mac_address: string | null;
  is_up: boolean;
  speed_mbps: number | null;
  is_default: boolean;
}

export interface NetworkOverview {
  active_interface: string;
  local_ip: string;
  public_ip: string | null;
  subnet_mask: string;
  cidr: string;
  default_gateway: string | null;
  gateway_mac: string | null;
  dns_servers: string[];
  internet_connected: boolean;
  current_latency_ms: number | null;
  packet_loss_pct: number;
  download_kbps: number;
  upload_kbps: number;
  health_score: number;
  connected_devices_count: number;
}

export interface DiscoveredDevice {
  id?: number;
  ip: string;
  mac: string | null;
  vendor: string;
  hostname: string | null;
  custom_name?: string | null;
  notes?: string | null;
  category?: string | null;
  is_trusted?: boolean;
  is_gateway: boolean;
  is_local_host: boolean;
  status: string;
  response_time_ms: number | null;
  first_seen?: string;
  last_seen?: string;
}

export interface DeviceUpdateRequest {
  custom_name?: string | null;
  notes?: string | null;
  category?: string | null;
  is_trusted?: boolean;
}

export interface GatewayBaselineResponse {
  gateway_ip: string | null;
  detected_mac: string | null;
  baseline_mac: string | null;
  status: 'confirmed' | 'unconfirmed' | 'mismatch' | 'no_gateway';
  confirmed_at: string | null;
  history_count: number;
}

export interface DeviceDiscoverResponse {
  scan_id: string;
  total_discovered: number;
  duration_seconds: number;
  devices: DiscoveredDevice[];
}

export interface TopologyNodeData {
  label: string;
  subLabel?: string;
  ip?: string;
  mac?: string;
  vendor?: string;
  status: string;
  nodeType: 'internet' | 'gateway' | 'host' | 'device' | 'dns';
}

export interface TopologyNode {
  id: string;
  type: string;
  data: TopologyNodeData;
  position: { x: number; y: number };
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  animated: boolean;
  style?: Record<string, any>;
}

export interface TopologyResponse {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export interface PingResponse {
  target: string;
  packets_transmitted: number;
  packets_received: number;
  packet_loss_pct: number;
  min_rtt_ms: number | null;
  avg_rtt_ms: number | null;
  max_rtt_ms: number | null;
  history: number[];
  raw_output: string | null;
}

export interface DNSResponse {
  domain: string;
  resolved_by: string;
  records: Record<string, string[]>;
  query_time_ms: number;
}

export interface TracerouteHop {
  hop: number;
  ip: string | null;
  hostname: string | null;
  rtt_ms: number | null;
  timed_out: boolean;
}

export interface TracerouteResponse {
  target: string;
  total_hops: number;
  hops: TracerouteHop[];
}

export interface IPInfoResponse {
  input: string;
  ip_version: number;
  network_address: string;
  netmask: string;
  broadcast_address: string | null;
  usable_host_range: string[];
  total_hosts: number;
  usable_hosts: number;
  is_private: boolean;
  is_loopback: boolean;
  binary_representation: string;
}

export interface PortResult {
  port: number;
  state: 'open' | 'closed' | 'filtered';
  service: string | null;
  banner: string | null;
  rtt_ms: number | null;
}

export interface PortScanResponse {
  target: string;
  total_scanned: number;
  open_count: number;
  results: PortResult[];
}

export interface SecurityFinding {
  id?: number;
  rule_id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  category: string;
  description: string;
  evidence: string;
  impact: string;
  remediation: string;
  status: 'active' | 'acknowledged' | 'resolved' | string;
  target?: string | null;
  created_at?: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  updated_at?: string | null;
}

export interface TelemetryPayload {
  type: string;
  timestamp: string;
  bandwidth: {
    download_bytes_per_sec: number;
    upload_bytes_per_sec: number;
    download_formatted: string;
    upload_formatted: string;
  };
  ping_ms: number | null;
  tcp_latency_ms?: number | null;
  packet_loss_pct: number;
  interface: string;
  is_connected: boolean;
}

export interface AnomalyEvent {
  id?: number;
  anomaly_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  evidence: string;
  target?: string | null;
  confidence?: string;
  threshold_trigger?: string | null;
  detected_at: string;
  status?: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  notes?: string | null;
}

export interface AnomalyThresholds {
  traffic_spike_kbps?: number;
  packet_loss_pct?: number;
  latency_surge_ms?: number;
}

export interface IntelligenceEvent {
  id?: number;
  event_id: string;
  category: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  confidence: string;
  timestamp: string;
  affected_device_ip?: string | null;
  affected_device_mac?: string | null;
  evidence_references: string;
  explanation: string;
  recommended_action: string;
  investigation_status: string;
  title?: string;
  resolved_at?: string | null;
}

export interface PacketCaptureSession {
  id: string;
  interface_name: string;
  status: string;
  total_packets: number;
  tcp_packets: number;
  udp_packets: number;
  icmp_packets: number;
  dns_packets: number;
  other_packets: number;
  total_bytes: number;
  duration_seconds: number;
  error_message?: string | null;
  started_at: string;
  stopped_at?: string | null;
}

export interface PacketStats {
  total_packets: number;
  tcp_packets: number;
  udp_packets: number;
  icmp_packets: number;
  dns_packets: number;
  other_packets: number;
  total_bytes: number;
  duration_seconds: number;
}

export interface PacketCaptureStatus {
  is_capturing?: boolean;
  is_running?: boolean;
  supported?: boolean;
  session_id?: string | null;
  interface_name?: string | null;
  stats?: PacketStats;
  note?: string | null;
  error_message?: string | null;
  total_captured?: number;
  protocol_distribution?: Record<string, number>;
  top_conversations?: { src: string; dst: string; protocol: string; packets: number; bytes: number }[];
  recent_packets?: {
    timestamp: string;
    protocol: string;
    src_ip: string;
    dst_ip: string;
    src_port: number | null;
    dst_port: number | null;
    length: number;
    summary: string;
  }[];
  start_time?: string | null;
  error?: string | null;
}

export interface LearningTopic {
  id: string;
  title: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  summary: string;
  explanation: string;
  key_takeaways: string[];
  live_metric_key?: string | null;
}

export interface PaginatedDevicesResponse {
  devices: DiscoveredDevice[];
  total_count: number;
  items?: DiscoveredDevice[];
  total?: number;
  page: number;
  page_size: number;
  total_pages: number;
}

