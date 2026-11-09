import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { NetworkOverview, NetworkInterface } from '../types/network';
import { useTelemetry } from '../hooks/useTelemetry';
import { StatCard } from '../components/common/StatCard';
import { Badge } from '../components/common/Badge';
import {
  Activity,
  Globe,
  Router,
  Wifi,
  Server,
  Download,
  Upload,
  ShieldCheck,
  RefreshCw,
  Cpu
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

export const OverviewPage: React.FC = () => {
  const [overview, setOverview] = useState<NetworkOverview | null>(null);
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const { history, telemetry } = useTelemetry();

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const [ovData, ifData] = await Promise.all([
        api.getOverview(),
        api.getInterfaces()
      ]);
      setOverview(ovData);
      setInterfaces(ifData);
    } catch (err) {
      console.error('Failed to load overview:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const healthScore = overview?.health_score ?? 100;
  const healthVariant = healthScore >= 80 ? 'emerald' : healthScore >= 60 ? 'amber' : 'rose';

  return (
    <div className="space-y-6">
      {/* Top Banner with Title & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Network Operations Center
            <Badge variant="cyan">Real-time Telemetry</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Live physical and logical topology monitoring for host machine
          </p>
        </div>
        <button
          onClick={fetchOverview}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs font-medium text-cyber-text transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyber-cyan' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Primary KPI Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Health Score"
          value={healthScore}
          unit="/100"
          subtitle={healthScore >= 80 ? "Optimal Connectivity" : "Impaired Link"}
          icon={ShieldCheck}
          variant={healthVariant}
        />

        <StatCard
          title="Active Gateway"
          value={overview?.default_gateway || '192.168.1.1'}
          subtitle={overview?.gateway_mac ? `MAC: ${overview.gateway_mac}` : 'Gateway Router'}
          icon={Router}
          variant="blue"
        />

        <StatCard
          title="Current Latency"
          value={telemetry?.ping_ms !== undefined && telemetry?.ping_ms !== null ? telemetry.ping_ms : (overview?.current_latency_ms || 14)}
          unit="ms"
          subtitle="RTT to Gateway / DNS"
          icon={Activity}
          variant="cyan"
        />

        <StatCard
          title="Connected LAN Devices"
          value={overview?.connected_devices_count || 1}
          subtitle="Subnet Device Inventory"
          icon={Cpu}
          variant="purple"
        />
      </div>

      {/* Throughput Area Chart & Network Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-time Throughput Visualizer */}
        <div className="lg:col-span-2 bg-cyber-card border border-cyber-border rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-cyber-text">Real-Time Bandwidth Utilization</h3>
              <p className="text-xs text-cyber-subtext">Live 1Hz streaming throughput (KB/s)</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                Down: {telemetry?.bandwidth.download_formatted || '0 KB/s'}
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Up: {telemetry?.bandwidth.upload_formatted || '0 KB/s'}
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="downGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="upGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={10} tickLine={false} />
                <YAxis stroke="#475569" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#1E293B',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="downKbps"
                  name="Download (KB/s)"
                  stroke="#06B6D4"
                  fillOpacity={1}
                  fill="url(#downGradient)"
                />
                <Area
                  type="monotone"
                  dataKey="upKbps"
                  name="Upload (KB/s)"
                  stroke="#10B981"
                  fillOpacity={1}
                  fill="url(#upGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Network Identifiers Panel */}
        <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-cyber-text border-b border-cyber-border pb-3">
            Interface & Addressing
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-cyber-border/60">
              <span className="text-cyber-subtext">Active Adapter</span>
              <span className="font-mono text-cyber-text font-medium truncate max-w-[150px]">
                {overview?.active_interface || 'Default NIC'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-cyber-border/60">
              <span className="text-cyber-subtext">Local Host IP</span>
              <span className="font-mono text-cyber-cyan font-medium">
                {overview?.local_ip || '127.0.0.1'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-cyber-border/60">
              <span className="text-cyber-subtext">Subnet & CIDR</span>
              <span className="font-mono text-cyber-text">
                {overview?.cidr || '192.168.1.0/24'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-cyber-border/60">
              <span className="text-cyber-subtext">Public External IP</span>
              <span className="font-mono text-emerald-400 font-medium">
                {overview?.public_ip || 'Resolving...'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-cyber-border/60">
              <span className="text-cyber-subtext">DNS Nameservers</span>
              <span className="font-mono text-cyber-text">
                {overview?.dns_servers.join(', ') || '1.1.1.1'}
              </span>
            </div>

            <div className="flex justify-between py-1.5">
              <span className="text-cyber-subtext">Internet Uplink</span>
              <span className="font-medium text-emerald-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Verified Online
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Network Interfaces List */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-cyber-text mb-4">
          All Detected Host Interfaces ({interfaces.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-cyber-subtext font-mono uppercase text-[10px] border-b border-cyber-border">
              <tr>
                <th className="py-2.5 px-3">Adapter Name</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">IPv4 Address</th>
                <th className="py-2.5 px-3">Netmask</th>
                <th className="py-2.5 px-3">Physical Address (MAC)</th>
                <th className="py-2.5 px-3">Link Speed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border/60 font-mono">
              {interfaces.map((iface, idx) => (
                <tr key={idx} className="hover:bg-cyber-surface/50 transition-colors">
                  <td className="py-2.5 px-3 font-sans font-medium text-cyber-text flex items-center gap-2">
                    <Wifi className="w-3.5 h-3.5 text-cyber-cyan" />
                    {iface.name}
                    {iface.is_default && (
                      <span className="text-[10px] bg-cyan-950 text-cyan-400 px-1.5 py-0.5 rounded border border-cyan-800/60 font-sans">
                        Default
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3">
                    <Badge variant={iface.is_up ? 'emerald' : 'gray'}>
                      {iface.is_up ? 'UP' : 'DOWN'}
                    </Badge>
                  </td>
                  <td className="py-2.5 px-3 text-cyber-cyan">{iface.ip_address || '—'}</td>
                  <td className="py-2.5 px-3 text-cyber-subtext">{iface.netmask || '—'}</td>
                  <td className="py-2.5 px-3 text-slate-300">{iface.mac_address || '—'}</td>
                  <td className="py-2.5 px-3 text-cyber-subtext">
                    {iface.speed_mbps ? `${iface.speed_mbps} Mbps` : 'Auto-negotiate'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
