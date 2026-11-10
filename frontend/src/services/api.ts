import {
  HealthInfo,
  NetworkInterface,
  NetworkOverview,
  DiscoveredDevice,
  DeviceDiscoverResponse,
  DeviceUpdateRequest,
  GatewayBaselineResponse,
  TopologyResponse,
  PingResponse,
  DNSResponse,
  TracerouteResponse,
  IPInfoResponse,
  PortScanResponse,
  SecurityFinding,
  AnomalyEvent,
  AnomalyThresholds,
  PacketCaptureStatus,
  LearningTopic,
  PaginatedDevicesResponse,
  IntelligenceEvent,
  PacketCaptureSession
} from '../types/network';

const API_BASE = (import.meta as any).env?.VITE_API_URL || '/api';

export const api = {
  async getHealth(): Promise<HealthInfo> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch health info');
    return res.json();
  },

  async getInterfaces(): Promise<NetworkInterface[]> {
    const res = await fetch(`${API_BASE}/network/interfaces`);
    if (!res.ok) throw new Error('Failed to fetch network interfaces');
    return res.json();
  },

  async getOverview(): Promise<NetworkOverview> {
    const res = await fetch(`${API_BASE}/network/overview`);
    if (!res.ok) throw new Error('Failed to fetch network overview');
    return res.json();
  },

  async getRecentMetrics(): Promise<{ metrics: any[] }> {
    const res = await fetch(`${API_BASE}/network/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  },

  async getMetricsHistory(limit: number = 50): Promise<any[]> {
    const res = await fetch(`${API_BASE}/network/metrics/history?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch database metric history');
    return res.json();
  },

  async discoverDevices(cidr?: string, timeoutSeconds: number = 10): Promise<DeviceDiscoverResponse> {
    const res = await fetch(`${API_BASE}/devices/discover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cidr, timeout_seconds: timeoutSeconds })
    });
    if (!res.ok) throw new Error('Failed to execute device discovery sweep');
    return res.json();
  },

  async stopDiscovery(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/devices/scan/stop`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to stop discovery scan');
    return res.json();
  },

  async getScanProgress(): Promise<{ scanned: number; total: number; status: string }> {
    const res = await fetch(`${API_BASE}/devices/scan/progress`);
    if (!res.ok) throw new Error('Failed to fetch scan progress');
    return res.json();
  },

  async getDevices(): Promise<DiscoveredDevice[]> {
    const res = await fetch(`${API_BASE}/devices`);
    if (!res.ok) throw new Error('Failed to fetch devices');
    return res.json();
  },

  async updateDevice(deviceId: number, data: DeviceUpdateRequest): Promise<DiscoveredDevice> {
    const res = await fetch(`${API_BASE}/devices/${deviceId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to update device' }));
      throw new Error(err.detail || 'Failed to update device');
    }
    return res.json();
  },

  async selectInterface(interfaceName: string): Promise<{ status: string; selected_interface: string; message: string }> {
    const res = await fetch(`${API_BASE}/network/interfaces/select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interface_name: interfaceName })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to select interface' }));
      throw new Error(err.detail || 'Failed to select interface');
    }
    return res.json();
  },

  async getTopology(): Promise<TopologyResponse> {
    const res = await fetch(`${API_BASE}/topology`);
    if (!res.ok) throw new Error('Failed to fetch topology');
    return res.json();
  },

  async runPing(target: string, count: number = 4, timeoutMs: number = 1000): Promise<PingResponse> {
    const res = await fetch(`${API_BASE}/diagnostics/ping`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, count, timeout_ms: timeoutMs })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Ping error' }));
      throw new Error(err.detail || 'Ping operation failed');
    }
    return res.json();
  },

  async runDNS(domain: string, recordType: string = 'ALL', customServer?: string): Promise<DNSResponse> {
    const res = await fetch(`${API_BASE}/diagnostics/dns`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain, record_type: recordType, custom_server: customServer || null })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'DNS query error' }));
      throw new Error(err.detail || 'DNS resolution failed');
    }
    return res.json();
  },

  async runTraceroute(target: string, maxHops: number = 15, timeoutMs: number = 1500): Promise<TracerouteResponse> {
    const res = await fetch(`${API_BASE}/diagnostics/traceroute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, max_hops: maxHops, timeout_ms: timeoutMs })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Traceroute error' }));
      throw new Error(err.detail || 'Traceroute failed');
    }
    return res.json();
  },

  async getIPInfo(ipOrCidr: string): Promise<IPInfoResponse> {
    const res = await fetch(`${API_BASE}/diagnostics/ip-info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_or_cidr: ipOrCidr })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'IP Info error' }));
      throw new Error(err.detail || 'IP calculation failed');
    }
    return res.json();
  },

  async runConnectivityTest(): Promise<{
    verdict: string;
    summary: string;
    dns: { ok: boolean; latency_ms?: number; tested_domain: string };
    gateway: { ok: boolean; latency_ms?: number; gateway_ip: string };
    internet: { ok: boolean; latency_ms?: number; tested_target: string };
    benchmark_duration_ms: number;
  }> {
    const res = await fetch(`${API_BASE}/diagnostics/connectivity`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to run connectivity benchmark');
    return res.json();
  },

  async runPortScan(target: string, ports: number[], timeoutMs: number = 500, authorized: boolean = true): Promise<PortScanResponse> {
    const res = await fetch(`${API_BASE}/diagnostics/ports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, ports, timeout_ms: timeoutMs, authorized })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Port scan error' }));
      throw new Error(err.detail || 'Port scan rejected');
    }
    return res.json();
  },

  async runSecurityAudit(): Promise<SecurityFinding[]> {
    const res = await fetch(`${API_BASE}/security/audit/run`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to run security audit');
    return res.json();
  },

  async getSecurityFindings(): Promise<SecurityFinding[]> {
    const res = await fetch(`${API_BASE}/security/findings`);
    if (!res.ok) throw new Error('Failed to fetch security findings');
    return res.json();
  },

  async getSecurityFindingsHistory(limit: number = 100): Promise<SecurityFinding[]> {
    const res = await fetch(`${API_BASE}/security/findings/history?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch security findings history');
    return res.json();
  },

  async acknowledgeSecurityFinding(findingId: number): Promise<{ status: string; message: string; finding_id: number }> {
    const res = await fetch(`${API_BASE}/security/findings/${findingId}/acknowledge`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to acknowledge finding' }));
      throw new Error(err.detail || 'Failed to acknowledge finding');
    }
    return res.json();
  },

  async resolveSecurityFinding(findingId: number): Promise<{ status: string; message: string; finding_id: number }> {
    const res = await fetch(`${API_BASE}/security/findings/${findingId}/resolve`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to resolve finding' }));
      throw new Error(err.detail || 'Failed to resolve finding');
    }
    return res.json();
  },

  async getGatewayBaseline(): Promise<GatewayBaselineResponse> {
    const res = await fetch(`${API_BASE}/security/gateway-baseline`);
    if (!res.ok) throw new Error('Failed to fetch gateway baseline');
    return res.json();
  },

  async confirmGatewayBaseline(baselineMac?: string): Promise<{ status: string; message: string; gateway_ip: string; baseline_mac: string }> {
    const res = await fetch(`${API_BASE}/security/gateway-baseline/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(baselineMac ? { baseline_mac: baselineMac } : {})
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to confirm baseline' }));
      throw new Error(err.detail || 'Failed to confirm baseline');
    }
    return res.json();
  },

  async resetGatewayBaseline(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/security/gateway-baseline/reset`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to reset gateway baseline');
    return res.json();
  },

  async exportDevices(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const res = await fetch(`${API_BASE}/reports/devices/export?format=${format}`);
    if (!res.ok) throw new Error('Failed to export devices');
    return res.blob();
  },

  async exportSecurityFindings(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const res = await fetch(`${API_BASE}/reports/security/export?format=${format}`);
    if (!res.ok) throw new Error('Failed to export security findings');
    return res.blob();
  },

  async exportHistory(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const res = await fetch(`${API_BASE}/reports/history/export?format=${format}`);
    if (!res.ok) throw new Error('Failed to export history');
    return res.blob();
  },

  async getHistory(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/history`);
    if (!res.ok) throw new Error('Failed to fetch history');
    return res.json();
  },

  async getSettings(): Promise<any> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async getPaginatedDevices(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    status?: string;
    vendor?: string;
    category?: string;
    sortBy?: string;
  }): Promise<PaginatedDevicesResponse> {
    const q = new URLSearchParams();
    if (params?.page) q.append('page', params.page.toString());
    if (params?.pageSize) q.append('page_size', params.pageSize.toString());
    if (params?.search) q.append('search', params.search);
    if (params?.status) q.append('status', params.status);
    if (params?.vendor) q.append('vendor', params.vendor);
    if (params?.category) q.append('category', params.category);
    if (params?.sortBy) q.append('sort_by', params.sortBy);

    const res = await fetch(`${API_BASE}/devices/paginated?${q.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch paginated devices');
    return res.json();
  },

  async evaluateAnomalies(): Promise<AnomalyEvent[]> {
    const res = await fetch(`${API_BASE}/security/anomalies/evaluate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to evaluate anomalies');
    return res.json();
  },

  async getAnomalies(limit: number = 50): Promise<AnomalyEvent[]> {
    const res = await fetch(`${API_BASE}/security/anomalies?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch active anomalies');
    return res.json();
  },

  async getAnomalyHistory(limit: number = 100): Promise<AnomalyEvent[]> {
    const res = await fetch(`${API_BASE}/security/anomalies/history?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch anomaly history');
    return res.json();
  },

  async acknowledgeAnomaly(id: number, notes?: string): Promise<{ status: string; id: number }> {
    const res = await fetch(`${API_BASE}/security/anomalies/${id}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes })
    });
    if (!res.ok) throw new Error('Failed to acknowledge anomaly');
    return res.json();
  },

  async resolveAnomaly(id: number, notes?: string): Promise<{ status: string; id: number }> {
    const res = await fetch(`${API_BASE}/security/anomalies/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes })
    });
    if (!res.ok) throw new Error('Failed to resolve anomaly');
    return res.json();
  },

  async tuneAnomalyThresholds(thresholds: AnomalyThresholds): Promise<{ status: string; thresholds: AnomalyThresholds }> {
    const q = new URLSearchParams();
    if (thresholds.traffic_spike_kbps) q.append('traffic_spike_kbps', thresholds.traffic_spike_kbps.toString());
    if (thresholds.packet_loss_pct) q.append('packet_loss_pct', thresholds.packet_loss_pct.toString());
    if (thresholds.latency_surge_ms) q.append('latency_surge_ms', thresholds.latency_surge_ms.toString());

    const res = await fetch(`${API_BASE}/security/anomalies/tune?${q.toString()}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to tune anomaly thresholds');
    return res.json();
  },

  async evaluateIntelligence(): Promise<IntelligenceEvent[]> {
    const res = await fetch(`${API_BASE}/intelligence/evaluate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to evaluate network intelligence');
    return res.json();
  },

  async getIntelligenceEvents(params?: { category?: string; severity?: string; status?: string; limit?: number }): Promise<IntelligenceEvent[]> {
    const q = new URLSearchParams();
    if (params?.category) q.append('category', params.category);
    if (params?.severity) q.append('severity', params.severity);
    if (params?.status) q.append('status', params.status);
    if (params?.limit) q.append('limit', params.limit.toString());

    const res = await fetch(`${API_BASE}/intelligence/events?${q.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch intelligence events');
    return res.json();
  },

  async updateIntelligenceEventStatus(eventId: string, status: string): Promise<{ status: string; event_id: string }> {
    const res = await fetch(`${API_BASE}/intelligence/events/${eventId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    if (!res.ok) throw new Error('Failed to update event status');
    return res.json();
  },

  async getPacketCaptureStatus(): Promise<PacketCaptureStatus> {
    const res = await fetch(`${API_BASE}/packets/status`);
    if (!res.ok) throw new Error('Failed to fetch packet capture status');
    return res.json();
  },

  async getPacketSessions(limit: number = 20): Promise<PacketCaptureSession[]> {
    const res = await fetch(`${API_BASE}/packets/sessions?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch packet capture sessions');
    return res.json();
  },

  async startPacketCapture(maxPackets: number = 500): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/packets/start?max_packets=${maxPackets}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start packet capture' }));
      throw new Error(err.detail || 'Failed to start packet capture');
    }
    return res.json();
  },

  async stopPacketCapture(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/packets/stop`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to stop packet capture');
    return res.json();
  },

  async getLearningTopics(): Promise<{ topics: LearningTopic[]; categories: string[] }> {
    const res = await fetch(`${API_BASE}/learning/topics`);
    if (!res.ok) throw new Error('Failed to fetch learning topics');
    return res.json();
  },

  async cleanupHistory(retentionDays: number = 30): Promise<{ status: string; message: string; pruned: any }> {
    const res = await fetch(`${API_BASE}/history/cleanup?retention_days=${retentionDays}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to prune database history');
    return res.json();
  }
};
