import {
  HealthInfo,
  NetworkInterface,
  NetworkOverview,
  DiscoveredDevice,
  DeviceDiscoverResponse,
  TopologyResponse,
  PingResponse,
  DNSResponse,
  TracerouteResponse,
  IPInfoResponse,
  PortScanResponse,
  SecurityFinding
} from '../types/network';

const API_BASE = '/api';

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

  async getSecurityFindings(): Promise<SecurityFinding[]> {
    const res = await fetch(`${API_BASE}/security/findings`);
    if (!res.ok) throw new Error('Failed to fetch security findings');
    return res.json();
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
  }
};
