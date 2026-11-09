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
  is_gateway: boolean;
  is_local_host: boolean;
  status: string;
  response_time_ms: number | null;
  first_seen?: string;
  last_seen?: string;
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
  status: string;
  created_at?: string;
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
  packet_loss_pct: number;
  interface: string;
  is_connected: boolean;
}
