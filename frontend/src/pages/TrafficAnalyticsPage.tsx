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
  RefreshCw
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
  const [loading, setLoading] = useState<boolean>(true);

  const fetchInterfaces = async () => {
    try {
      setLoading(true);
      const data = await api.getInterfaces();
      setInterfaces(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterfaces();
  }, []);

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

        <button
          onClick={fetchInterfaces}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs font-medium text-cyber-text transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Counters</span>
        </button>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Download Throughput"
          value={telemetry?.bandwidth.download_formatted || '0 KB/s'}
          subtitle="Instantaneous RX Rate"
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
          title="Active Adapters"
          value={interfaces.filter(i => i.is_up).length}
          unit={`/ ${interfaces.length} Total`}
          subtitle="Physical & Virtual Devices"
          icon={Layers}
          variant="purple"
        />
      </div>

      {/* Primary Traffic Throughput Graph */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-cyber-text">Historical Telemetry Stream</h3>
            <p className="text-xs text-cyber-subtext">Recent sliding window throughput measurements (KB/s)</p>
          </div>
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
