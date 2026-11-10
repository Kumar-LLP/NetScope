import React, { useState, useEffect } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { api } from '../services/api';
import { NetworkInterface } from '../types/network';
import { StatCard } from '../components/common/StatCard';
import { Badge } from '../components/common/Badge';
import {
  BarChart3,
  ArrowDown,
  ArrowUp,
  Activity,
  Layers,
  Radio,
  RefreshCw,
  Download,
  Wifi,
  Server,
  Zap,
  Percent
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

export const TrafficAnalyticsPage: React.FC = () => {
  const { history, telemetry } = useTelemetry();
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [selectedInterface, setSelectedInterface] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [switching, setSwitching] = useState<boolean>(false);

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const fetchInterfaces = async () => {
    try {
      setLoading(true);
      const data = await api.getInterfaces();
      setInterfaces(data);
      if (!selectedInterface && data.length > 0) {
        const def = data.find((i) => i.is_default) || data[0];
        setSelectedInterface(def.name);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterfaces();
  }, []);

  useEffect(() => {
    if (telemetry?.interface && !selectedInterface) {
      setSelectedInterface(telemetry.interface);
    }
  }, [telemetry?.interface]);

  const handleInterfaceChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const ifaceName = e.target.value;
    setSelectedInterface(ifaceName);
    try {
      setSwitching(true);
      await api.selectInterface(ifaceName);
    } catch (err: any) {
      alert(`Failed to switch interface: ${err.message || err}`);
    } finally {
      setSwitching(false);
    }
  };

  const handleExportHistory = async (format: 'json' | 'csv') => {
    try {
      const blob = await api.exportHistory(format);
      downloadBlob(blob, `netscope_metrics_history_${Date.now()}.${format}`);
    } catch (err: any) {
      alert(`Export failed: ${err.message || err}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Network Traffic & Throughput Analytics
            <Badge variant="cyan">Real psutil Metrics</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Interface-level byte counters, measured throughput deltas, and packet transmission statistics
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          {/* Interface Selector Dropdown */}
          <div className="flex items-center gap-2 bg-cyber-card border border-cyber-border rounded-lg px-3 py-1.5 text-xs">
            <Wifi className="w-3.5 h-3.5 text-cyber-cyan" />
            <span className="text-cyber-subtext font-mono">Adapter:</span>
            <select
              value={selectedInterface || telemetry?.interface || ''}
              onChange={handleInterfaceChange}
              disabled={switching || loading}
              className="bg-transparent text-cyber-text font-mono focus:outline-none cursor-pointer max-w-[200px] truncate"
            >
              {interfaces.map((iface) => (
                <option key={iface.name} value={iface.name} className="bg-cyber-bg text-cyber-text">
                  {iface.name} {iface.ip_address ? `(${iface.ip_address})` : '(No IP)'} {iface.is_default ? '★' : ''}
                </option>
              ))}
            </select>
            {switching && <RefreshCw className="w-3 h-3 animate-spin text-cyber-cyan" />}
          </div>

          {/* Export Controls */}
          <div className="flex items-center gap-1 bg-cyber-card border border-cyber-border rounded-lg p-0.5">
            <button
              onClick={() => handleExportHistory('csv')}
              className="px-2.5 py-1 text-xs font-medium text-cyber-subtext hover:text-cyber-cyan transition-colors flex items-center gap-1"
              title="Export historical metrics as CSV"
            >
              <Download className="w-3 h-3" /> CSV
            </button>
            <span className="text-cyber-border">|</span>
            <button
              onClick={() => handleExportHistory('json')}
              className="px-2.5 py-1 text-xs font-medium text-cyber-subtext hover:text-cyber-cyan transition-colors flex items-center gap-1"
              title="Export historical metrics as JSON"
            >
              <Download className="w-3 h-3" /> JSON
            </button>
          </div>

          <button
            onClick={fetchInterfaces}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs font-medium text-cyber-text transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Download Throughput"
          value={telemetry?.bandwidth.download_formatted || '0 KB/s'}
          subtitle={`Adapter: ${telemetry?.interface || 'Default'}`}
          icon={ArrowDown}
          variant="cyan"
        />

        <StatCard
          title="Upload Throughput"
          value={telemetry?.bandwidth.upload_formatted || '0 KB/s'}
          subtitle="Instantaneous TX Rate"
          icon={ArrowUp}
          variant="emerald"
        />

        <StatCard
          title="ICMP Ping Latency"
          value={telemetry?.ping_ms != null ? `${Math.round(telemetry.ping_ms)} ms` : 'N/A'}
          subtitle={telemetry?.tcp_latency_ms != null ? `TCP: ${Math.round(telemetry.tcp_latency_ms)} ms` : 'Multi-probe ICMP'}
          icon={Zap}
          variant="purple"
        />

        <StatCard
          title="Packet Loss"
          value={telemetry?.packet_loss_pct != null ? `${telemetry.packet_loss_pct.toFixed(1)}%` : '0%'}
          subtitle={telemetry?.is_connected ? 'Gateway Reachable' : 'Gateway Unreachable'}
          icon={Percent}
          variant={telemetry?.packet_loss_pct && telemetry.packet_loss_pct > 5 ? 'rose' : 'cyan'}
        />
      </div>

      {/* Primary Traffic Throughput Graph */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-cyber-text">Historical Telemetry Stream</h3>
            <p className="text-xs text-cyber-subtext">Recent sliding window throughput measurements (KB/s)</p>
          </div>
          <span className="text-[11px] font-mono text-cyber-subtext">
            Monitored: <strong className="text-cyber-cyan">{telemetry?.interface || 'All'}</strong>
          </span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="downGradient2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="upGradient2" x1="0" y1="0" x2="0" y2="1">
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
                fill="url(#downGradient2)"
              />
              <Area
                type="monotone"
                dataKey="upKbps"
                name="Upload (KB/s)"
                stroke="#10B981"
                fillOpacity={1}
                fill="url(#upGradient2)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Latency Jitter Graph */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-cyber-text mb-4">Round-Trip Latency History (ms)</h3>
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
              <Bar dataKey="ping" name="Latency (ms)" fill="#38BDF8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
