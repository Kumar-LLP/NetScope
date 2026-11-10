import React, { useState, useEffect } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { api } from '../services/api';
import { NetworkInterface, PacketCaptureStatus, PacketCaptureSession } from '../types/network';
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
  Percent,
  Play,
  Square,
  ShieldAlert,
  History,
  CheckCircle2,
  Clock
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
  const [packetStatus, setPacketStatus] = useState<PacketCaptureStatus | null>(null);
  const [sessions, setSessions] = useState<PacketCaptureSession[]>([]);
  const [captureLoading, setCaptureLoading] = useState<boolean>(false);

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

  const fetchSessions = async () => {
    try {
      const sess = await api.getPacketSessions(20);
      setSessions(sess);
    } catch (e) {
      // ignore
    }
  };

  const fetchPacketStatus = async () => {
    try {
      const status = await api.getPacketCaptureStatus();
      setPacketStatus(status);
      await fetchSessions();
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchPacketStatus();
    fetchSessions();
  }, []);

  const isCapturing = Boolean(packetStatus?.is_capturing || packetStatus?.is_running);

  useEffect(() => {
    let interval: any;
    if (isCapturing) {
      interval = setInterval(fetchPacketStatus, 1000);
    }
    return () => clearInterval(interval);
  }, [isCapturing]);

  const handleStartCapture = async () => {
    try {
      setCaptureLoading(true);
      await api.startPacketCapture(500);
      await fetchPacketStatus();
    } catch (err: any) {
      alert(`Capture failed: ${err.message || err}`);
    } finally {
      setCaptureLoading(false);
    }
  };

  const handleStopCapture = async () => {
    try {
      setCaptureLoading(true);
      await api.stopPacketCapture();
      await fetchPacketStatus();
      await fetchSessions();
    } catch (err: any) {
      alert(`Stop failed: ${err.message || err}`);
    } finally {
      setCaptureLoading(false);
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

      {/* Packet Inspection & Protocol Distribution Engine */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-cyber-border pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyber-cyan" />
              <h3 className="text-sm font-semibold text-cyber-text">Real-Time Packet & Protocol Inspection</h3>
              {isCapturing && (
                <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  CAPTURING
                </span>
              )}
            </div>
            <p className="text-xs text-cyber-subtext mt-0.5">
              Opt-in non-invasive network layer telemetry • Zero payload inspection • Scapy / Npcap Raw Socket
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!isCapturing ? (
              <button
                onClick={handleStartCapture}
                disabled={captureLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-cyan text-black font-semibold text-xs hover:bg-cyber-cyan/90 transition-colors disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Start Capture (500 Pkts)</span>
              </button>
            ) : (
              <button
                onClick={handleStopCapture}
                disabled={captureLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 text-white font-semibold text-xs hover:bg-rose-500 transition-colors disabled:opacity-50"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Stop Capture</span>
              </button>
            )}
            <button
              onClick={fetchPacketStatus}
              className="p-1.5 rounded-lg bg-cyber-surface border border-cyber-border hover:text-cyber-cyan text-cyber-subtext text-xs"
              title="Refresh capture state"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Driver Capability / System Notice */}
        {packetStatus?.note && (
          <div className={`p-3 rounded-lg border text-xs flex items-center gap-2.5 font-mono ${
            packetStatus.supported === false
              ? 'bg-amber-950/20 border-amber-800/40 text-amber-300'
              : 'bg-cyan-950/20 border-cyan-800/40 text-cyan-300'
          }`}>
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <div>
              <span className="font-bold block uppercase text-[10px]">
                {packetStatus.supported === false ? 'Packet Capture Driver Notice' : 'Capture Environment'}
              </span>
              <span>{packetStatus.note}</span>
            </div>
          </div>
        )}

        {(packetStatus?.error_message || packetStatus?.error) && (
          <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-800/40 text-xs text-rose-300 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>{packetStatus.error_message || packetStatus.error}</span>
          </div>
        )}

        {/* Protocol Distribution Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {['TCP', 'UDP', 'ICMP', 'DNS', 'OTHER'].map((proto) => {
            const count =
              (packetStatus?.stats as any)?.[`${proto.toLowerCase()}_packets`] ??
              packetStatus?.protocol_distribution?.[proto] ??
              0;
            const total = packetStatus?.stats?.total_packets ?? packetStatus?.total_captured ?? 0;
            const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
            return (
              <div key={proto} className="bg-cyber-surface border border-cyber-border/70 rounded-lg p-3 text-center">
                <span className="text-[10px] font-mono text-cyber-subtext uppercase block">{proto}</span>
                <span className="text-base font-mono font-bold text-cyber-text mt-0.5 block">{count}</span>
                <span className="text-[10px] font-mono text-cyber-cyan">{pct}%</span>
              </div>
            );
          })}
        </div>

        {/* Capture Telemetry Footer */}
        {packetStatus?.stats && (
          <div className="flex items-center justify-between text-xs font-mono text-cyber-subtext pt-2 border-t border-cyber-border/40">
            <span>Total Captured: <strong className="text-cyber-text">{packetStatus.stats.total_packets}</strong> packets</span>
            <span>Bytes: <strong className="text-cyber-text">{(packetStatus.stats.total_bytes / 1024).toFixed(1)} KB</strong></span>
            <span>Duration: <strong className="text-cyber-cyan">{packetStatus.stats.duration_seconds.toFixed(1)}s</strong></span>
          </div>
        )}

        {/* Recent Packets Stream (if available) */}
        {packetStatus?.recent_packets && packetStatus.recent_packets.length > 0 && (
          <div className="space-y-2 mt-4">
            <div className="text-[11px] font-mono text-cyber-subtext uppercase tracking-wider flex items-center justify-between">
              <span>Recent Packets (Headers Only)</span>
              <span>Total Captured: {packetStatus.total_captured}</span>
            </div>
            <div className="max-h-56 overflow-y-auto space-y-1 font-mono text-[11px] border border-cyber-border rounded-lg p-2 bg-black/40">
              {packetStatus.recent_packets.slice(0, 20).map((pkt, idx) => (
                <div key={idx} className="flex items-center justify-between py-1 px-2 rounded hover:bg-cyber-surface/60 border-b border-cyber-border/30 last:border-b-0">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-cyan-950 text-cyan-400 border border-cyan-800/40">
                      {pkt.protocol}
                    </span>
                    <span className="text-cyber-text">{pkt.src_ip}{pkt.src_port ? `:${pkt.src_port}` : ''}</span>
                    <span className="text-cyber-subtext">→</span>
                    <span className="text-cyber-cyan">{pkt.dst_ip}{pkt.dst_port ? `:${pkt.dst_port}` : ''}</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-500 text-[10px]">
                    <span>{pkt.length} B</span>
                    <span>{new Date(pkt.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Historical Capture Sessions Table */}
        <div className="mt-6 pt-4 border-t border-cyber-border space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-cyber-cyan" />
              <h4 className="text-xs font-semibold text-cyber-text uppercase font-mono tracking-wider">
                Capture Session History ({sessions.length})
              </h4>
            </div>
            <button
              onClick={fetchSessions}
              className="text-[11px] font-mono text-cyber-subtext hover:text-cyber-cyan flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" /> Refresh Sessions
            </button>
          </div>

          {sessions.length === 0 ? (
            <div className="text-center py-4 text-xs font-mono text-cyber-subtext bg-black/30 rounded border border-cyber-border/40">
              No historical packet capture sessions recorded in database.
            </div>
          ) : (
            <div className="overflow-x-auto border border-cyber-border rounded-lg">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/80 text-cyber-subtext uppercase text-[10px] border-b border-cyber-border">
                  <tr>
                    <th className="py-2.5 px-3">Session ID</th>
                    <th className="py-2.5 px-3">Interface</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Packets</th>
                    <th className="py-2.5 px-3">Protocols (TCP/UDP/ICMP/DNS)</th>
                    <th className="py-2.5 px-3">Duration</th>
                    <th className="py-2.5 px-3">Started At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cyber-border/40">
                  {sessions.map((s) => (
                    <tr key={s.id} className="hover:bg-cyber-surface/60">
                      <td className="py-2.5 px-3 text-cyber-cyan font-bold">{s.id}</td>
                      <td className="py-2.5 px-3 text-cyber-text">{s.interface_name}</td>
                      <td className="py-2.5 px-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded ${
                          s.status === 'completed'
                            ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/40'
                            : s.status === 'capturing'
                            ? 'bg-cyan-950/40 text-cyan-400 border border-cyan-800/40 animate-pulse'
                            : 'bg-rose-950/40 text-rose-400 border border-rose-800/40'
                        }`}>
                          {s.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-cyber-text font-bold">{s.total_packets}</td>
                      <td className="py-2.5 px-3 text-cyber-subtext text-[11px]">
                        {s.tcp_packets} / {s.udp_packets} / {s.icmp_packets} / {s.dns_packets}
                      </td>
                      <td className="py-2.5 px-3 text-cyber-subtext">{s.duration_seconds.toFixed(1)}s</td>
                      <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                        {new Date(s.started_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
