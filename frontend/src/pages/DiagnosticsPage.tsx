import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  PingResponse,
  DNSResponse,
  TracerouteResponse,
  IPInfoResponse
} from '../types/network';
import { Badge } from '../components/common/Badge';
import { useToast } from '../components/common/Toast';
import {
  Activity,
  Terminal,
  Globe,
  Share2,
  Calculator,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Server,
  Router,
  Wifi
} from 'lucide-react';

interface DiagnosticsPageProps {
  initialTarget?: string;
  initialTab?: 'ping' | 'dns' | 'traceroute' | 'ipinfo' | 'connectivity';
}

export const DiagnosticsPage: React.FC<DiagnosticsPageProps> = ({
  initialTarget,
  initialTab = 'ping'
}) => {
  const [activeTab, setActiveTab] = useState<'ping' | 'dns' | 'traceroute' | 'ipinfo' | 'connectivity'>(initialTab);

  // Ping State
  const [pingTarget, setPingTarget] = useState<string>(initialTarget || '1.1.1.1');
  const [pingCount, setPingCount] = useState<number>(4);
  const [pingLoading, setPingLoading] = useState<boolean>(false);
  const [pingResult, setPingResult] = useState<PingResponse | null>(null);

  // DNS State
  const [dnsDomain, setDnsDomain] = useState<string>('google.com');
  const [dnsType, setDnsType] = useState<string>('ALL');
  const [dnsLoading, setDnsLoading] = useState<boolean>(false);
  const [dnsResult, setDnsResult] = useState<DNSResponse | null>(null);

  // Traceroute State
  const [traceTarget, setTraceTarget] = useState<string>(initialTarget || '8.8.8.8');
  const [traceHops, setTraceHops] = useState<number>(15);
  const [traceLoading, setTraceLoading] = useState<boolean>(false);
  const [traceResult, setTraceResult] = useState<TracerouteResponse | null>(null);

  // IP Info State
  const [ipInput, setIpInput] = useState<string>('192.168.1.50/24');
  const [ipLoading, setIpLoading] = useState<boolean>(false);
  const [ipResult, setIpResult] = useState<IPInfoResponse | null>(null);

  // Connectivity Benchmark State
  const [connLoading, setConnLoading] = useState<boolean>(false);
  const [connResult, setConnResult] = useState<any>(null);

  const { addToast } = useToast();

  useEffect(() => {
    if (initialTarget) {
      setPingTarget(initialTarget);
      setTraceTarget(initialTarget);
    }
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTarget, initialTab]);

  const handlePing = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setPingLoading(true);
      const res = await api.runPing(pingTarget, pingCount);
      setPingResult(res);
      addToast('success', 'Ping Operation Complete', `Avg RTT: ${res.avg_rtt_ms ?? 'N/A'} ms`);
    } catch (err: any) {
      addToast('error', 'Ping Operation Failed', err.message);
    } finally {
      setPingLoading(false);
    }
  };

  const handleDNS = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setDnsLoading(true);
      const res = await api.runDNS(dnsDomain, dnsType);
      setDnsResult(res);
      addToast('success', 'DNS Resolution Complete', `Resolved in ${res.query_time_ms} ms`);
    } catch (err: any) {
      addToast('error', 'DNS Resolution Failed', err.message);
    } finally {
      setDnsLoading(false);
    }
  };

  const handleTraceroute = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setTraceLoading(true);
      addToast('info', 'Traceroute Started', `Tracing hop path to ${traceTarget}...`);
      const res = await api.runTraceroute(traceTarget, traceHops);
      setTraceResult(res);
      addToast('success', 'Traceroute Complete', `Discovered ${res.total_hops} network hops.`);
    } catch (err: any) {
      addToast('error', 'Traceroute Failed', err.message);
    } finally {
      setTraceLoading(false);
    }
  };

  const handleIPInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIpLoading(true);
      const res = await api.getIPInfo(ipInput);
      setIpResult(res);
    } catch (err: any) {
      addToast('error', 'Subnet Calculation Error', err.message);
    } finally {
      setIpLoading(false);
    }
  };

  const handleConnectivityTest = async () => {
    try {
      setConnLoading(true);
      addToast('info', 'Benchmarking Connectivity', 'Testing DNS, Gateway, and Internet WAN...');
      const res = await api.runConnectivityTest();
      setConnResult(res);
      addToast(
        res.verdict === 'HEALTHY' ? 'success' : 'error',
        `Connectivity Benchmark: ${res.verdict}`,
        res.summary
      );
    } catch (err: any) {
      addToast('error', 'Benchmark Failed', err.message);
    } finally {
      setConnLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Network Diagnostic Toolkit
            <Badge variant="cyan">Multi-Protocol</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Genuine ICMP ping, recursive DNS record inspection, traceroute hop routing, and CIDR subnet calculation
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-cyber-card border border-cyber-border self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('ping')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'ping'
                ? 'bg-cyber-surface text-cyber-cyan border border-cyber-cyan/30'
                : 'text-cyber-subtext hover:text-cyber-text'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Ping</span>
          </button>

          <button
            onClick={() => setActiveTab('dns')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'dns'
                ? 'bg-cyber-surface text-cyber-cyan border border-cyber-cyan/30'
                : 'text-cyber-subtext hover:text-cyber-text'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>DNS</span>
          </button>

          <button
            onClick={() => setActiveTab('traceroute')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'traceroute'
                ? 'bg-cyber-surface text-cyber-cyan border border-cyber-cyan/30'
                : 'text-cyber-subtext hover:text-cyber-text'
            }`}
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Traceroute</span>
          </button>

          <button
            onClick={() => setActiveTab('ipinfo')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'ipinfo'
                ? 'bg-cyber-surface text-cyber-cyan border border-cyber-cyan/30'
                : 'text-cyber-subtext hover:text-cyber-text'
            }`}
          >
            <Calculator className="w-3.5 h-3.5" />
            <span>Subnet Calc</span>
          </button>

          <button
            onClick={() => setActiveTab('connectivity')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'connectivity'
                ? 'bg-cyber-surface text-emerald-400 border border-emerald-500/40'
                : 'text-cyber-subtext hover:text-cyber-text'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Connectivity Test</span>
          </button>
        </div>
      </div>

      {/* 1. PING TEST TAB */}
      {activeTab === 'ping' && (
        <div className="space-y-6">
          <form onSubmit={handlePing} className="bg-cyber-card border border-cyber-border rounded-xl p-5 flex flex-col sm:flex-row items-end gap-4">
            <div className="flex-1 w-full">
              <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
                Target IP or Hostname
              </label>
              <input
                type="text"
                value={pingTarget}
                onChange={(e) => setPingTarget(e.target.value)}
                placeholder="e.g. 1.1.1.1 or google.com"
                required
                className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
              />
            </div>

            <div className="w-full sm:w-32">
              <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
                Packet Count
              </label>
              <select
                value={pingCount}
                onChange={(e) => setPingCount(Number(e.target.value))}
                className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
              >
                <option value={4}>4 Packets</option>
                <option value={8}>8 Packets</option>
                <option value={10}>10 Packets</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={pingLoading}
              className="flex items-center justify-center gap-2 px-6 py-2 rounded-lg bg-cyber-cyan hover:bg-cyan-400 text-black text-xs font-bold transition-all disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${pingLoading ? 'animate-spin' : ''}`} />
              <span>{pingLoading ? 'Pinging...' : 'Send ICMP Ping'}</span>
            </button>
          </form>

          {pingResult && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
                  <span className="text-[10px] font-mono text-cyber-subtext uppercase">Packets</span>
                  <div className="text-xl font-mono font-bold text-cyber-text mt-1">
                    {pingResult.packets_received} / {pingResult.packets_transmitted}
                  </div>
                  <span className="text-xs text-cyber-subtext">Loss: {pingResult.packet_loss_pct}%</span>
                </div>

                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
                  <span className="text-[10px] font-mono text-cyber-subtext uppercase">Min Latency</span>
                  <div className="text-xl font-mono font-bold text-emerald-400 mt-1">
                    {pingResult.min_rtt_ms ?? 'N/A'} {pingResult.min_rtt_ms ? 'ms' : ''}
                  </div>
                </div>

                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
                  <span className="text-[10px] font-mono text-cyber-subtext uppercase">Average Latency</span>
                  <div className="text-xl font-mono font-bold text-cyber-cyan mt-1">
                    {pingResult.avg_rtt_ms ?? 'N/A'} {pingResult.avg_rtt_ms ? 'ms' : ''}
                  </div>
                </div>

                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
                  <span className="text-[10px] font-mono text-cyber-subtext uppercase">Max Latency</span>
                  <div className="text-xl font-mono font-bold text-sky-400 mt-1">
                    {pingResult.max_rtt_ms ?? 'N/A'} {pingResult.max_rtt_ms ? 'ms' : ''}
                  </div>
                </div>
              </div>

              {pingResult.raw_output && (
                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
                  <h4 className="text-xs font-semibold text-cyber-text mb-2 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-cyber-cyan" />
                    System Ping Output
                  </h4>
                  <pre className="p-3 bg-black/70 border border-cyber-border/60 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                    {pingResult.raw_output}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 2. DNS LOOKUP TAB */}
      {activeTab === 'dns' && (
        <div className="space-y-6">
          <form onSubmit={handleDNS} className="bg-cyber-card border border-cyber-border rounded-xl p-5 flex flex-col sm:flex-row items-end gap-4">
            <div className="flex-1 w-full">
              <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
                Target Domain Name
              </label>
              <input
                type="text"
                value={dnsDomain}
                onChange={(e) => setDnsDomain(e.target.value)}
                placeholder="e.g. google.com or cloudflare.com"
                required
                className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
              />
            </div>

            <div className="w-full sm:w-40">
              <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
                Record Type
              </label>
              <select
                value={dnsType}
                onChange={(e) => setDnsType(e.target.value)}
                className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
              >
                <option value="ALL">ALL Records</option>
                <option value="A">A (IPv4)</option>
                <option value="AAAA">AAAA (IPv6)</option>
                <option value="MX">MX (Mail)</option>
                <option value="NS">NS (Name Server)</option>
                <option value="TXT">TXT (Verification)</option>
                <option value="CNAME">CNAME (Alias)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={dnsLoading}
              className="flex items-center justify-center gap-2 px-6 py-2 rounded-lg bg-cyber-cyan hover:bg-cyan-400 text-black text-xs font-bold transition-all disabled:opacity-50"
            >
              <Globe className={`w-3.5 h-3.5 ${dnsLoading ? 'animate-spin' : ''}`} />
              <span>{dnsLoading ? 'Resolving...' : 'Lookup Records'}</span>
            </button>
          </form>

          {dnsResult && (
            <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-cyber-border pb-3">
                <div className="text-xs font-mono">
                  <span className="text-cyber-subtext">Resolved domain: </span>
                  <span className="text-cyber-cyan font-bold">{dnsResult.domain}</span>
                </div>
                <div className="text-xs font-mono text-cyber-subtext">
                  Query execution time: <span className="text-emerald-400 font-bold">{dnsResult.query_time_ms} ms</span>
                </div>
              </div>

              <div className="space-y-4">
                {Object.entries(dnsResult.records).map(([type, records]) => (
                  <div key={type} className="border border-cyber-border/80 rounded-lg p-3 bg-cyber-surface/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono font-bold text-cyber-text bg-slate-800 px-2 py-0.5 rounded">
                        {type} Records ({records.length})
                      </span>
                    </div>
                    {records.length > 0 ? (
                      <ul className="space-y-1 text-xs font-mono text-cyber-cyan">
                        {records.map((r, i) => (
                          <li key={i} className="py-1 px-2 rounded bg-slate-900/60 break-all">
                            {r}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-cyber-subtext italic">No records returned for this type.</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3. TRACEROUTE TAB */}
      {activeTab === 'traceroute' && (
        <div className="space-y-6">
          <form onSubmit={handleTraceroute} className="bg-cyber-card border border-cyber-border rounded-xl p-5 flex flex-col sm:flex-row items-end gap-4">
            <div className="flex-1 w-full">
              <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
                Destination Target
              </label>
              <input
                type="text"
                value={traceTarget}
                onChange={(e) => setTraceTarget(e.target.value)}
                placeholder="e.g. 8.8.8.8"
                required
                className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
              />
            </div>

            <div className="w-full sm:w-32">
              <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
                Max Hops
              </label>
              <select
                value={traceHops}
                onChange={(e) => setTraceHops(Number(e.target.value))}
                className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
              >
                <option value={10}>10 Hops</option>
                <option value={15}>15 Hops</option>
                <option value={30}>30 Hops</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={traceLoading}
              className="flex items-center justify-center gap-2 px-6 py-2 rounded-lg bg-cyber-cyan hover:bg-cyan-400 text-black text-xs font-bold transition-all disabled:opacity-50"
            >
              <Share2 className={`w-3.5 h-3.5 ${traceLoading ? 'animate-spin' : ''}`} />
              <span>{traceLoading ? 'Tracing Path...' : 'Trace Route'}</span>
            </button>
          </form>

          {traceResult && (
            <div className="bg-cyber-card border border-cyber-border rounded-xl p-5">
              <h4 className="text-xs font-semibold text-cyber-text mb-4">
                Routing Path Hops ({traceResult.hops.length})
              </h4>
              <div className="space-y-2">
                {traceResult.hops.map((hop) => (
                  <div
                    key={hop.hop}
                    className="flex items-center justify-between p-3 rounded-lg bg-cyber-surface/60 border border-cyber-border text-xs font-mono"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-slate-800 text-cyber-subtext flex items-center justify-center text-[10px] font-bold">
                        {hop.hop}
                      </span>
                      <span className="text-cyber-text font-medium">
                        {hop.timed_out ? <span className="text-rose-400">* * * (Request timed out)</span> : hop.ip}
                      </span>
                    </div>

                    {!hop.timed_out && (
                      <span className="text-emerald-400 font-bold">
                        {hop.rtt_ms ? `${hop.rtt_ms} ms` : '<1 ms'}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 4. IP CALCULATOR TAB */}
      {activeTab === 'ipinfo' && (
        <div className="space-y-6">
          <form onSubmit={handleIPInfo} className="bg-cyber-card border border-cyber-border rounded-xl p-5 flex flex-col sm:flex-row items-end gap-4">
            <div className="flex-1 w-full">
              <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
                IPv4 or CIDR Notation
              </label>
              <input
                type="text"
                value={ipInput}
                onChange={(e) => setIpInput(e.target.value)}
                placeholder="e.g. 192.168.1.50/24 or 10.0.0.1/16"
                required
                className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
              />
            </div>

            <button
              type="submit"
              disabled={ipLoading}
              className="flex items-center justify-center gap-2 px-6 py-2 rounded-lg bg-cyber-cyan hover:bg-cyan-400 text-black text-xs font-bold transition-all disabled:opacity-50"
            >
              <Calculator className={`w-3.5 h-3.5 ${ipLoading ? 'animate-spin' : ''}`} />
              <span>{ipLoading ? 'Calculating...' : 'Calculate Subnet'}</span>
            </button>
          </form>

          {ipResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-3 text-xs font-mono">
                <h4 className="font-sans font-semibold text-cyber-text text-sm border-b border-cyber-border pb-2">
                  Network Architecture
                </h4>

                <div className="flex justify-between py-1 border-b border-cyber-border/50">
                  <span className="text-cyber-subtext">Network Address:</span>
                  <span className="text-cyber-cyan font-bold">{ipResult.network_address}</span>
                </div>

                <div className="flex justify-between py-1 border-b border-cyber-border/50">
                  <span className="text-cyber-subtext">Subnet Mask:</span>
                  <span className="text-cyber-text">{ipResult.netmask}</span>
                </div>

                <div className="flex justify-between py-1 border-b border-cyber-border/50">
                  <span className="text-cyber-subtext">Broadcast Address:</span>
                  <span className="text-cyber-text">{ipResult.broadcast_address || 'N/A'}</span>
                </div>

                <div className="flex justify-between py-1">
                  <span className="text-cyber-subtext">IP Version:</span>
                  <span className="text-cyber-text">IPv{ipResult.ip_version}</span>
                </div>
              </div>

              <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-3 text-xs font-mono">
                <h4 className="font-sans font-semibold text-cyber-text text-sm border-b border-cyber-border pb-2">
                  Host Capacity & Scope
                </h4>

                <div className="flex justify-between py-1 border-b border-cyber-border/50">
                  <span className="text-cyber-subtext">Usable Host Range:</span>
                  <span className="text-emerald-400 font-bold">
                    {ipResult.usable_host_range[0]} - {ipResult.usable_host_range[1]}
                  </span>
                </div>

                <div className="flex justify-between py-1 border-b border-cyber-border/50">
                  <span className="text-cyber-subtext">Usable Hosts:</span>
                  <span className="text-cyber-cyan font-bold">{ipResult.usable_hosts.toLocaleString()}</span>
                </div>

                <div className="flex justify-between py-1 border-b border-cyber-border/50">
                  <span className="text-cyber-subtext">Scope:</span>
                  <span className="text-cyber-text">
                    {ipResult.is_private ? 'Private LAN (RFC 1918)' : 'Public Internet'}
                  </span>
                </div>

                <div className="flex justify-between py-1">
                  <span className="text-cyber-subtext">Binary Octets:</span>
                  <span className="text-[10px] text-slate-400 truncate max-w-[200px]">
                    {ipResult.binary_representation}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 5. CONNECTIVITY BENCHMARK TAB */}
      {activeTab === 'connectivity' && (
        <div className="space-y-6">
          <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-cyber-text">One-Click Network Health Benchmark</h3>
              <p className="text-xs text-cyber-subtext mt-1">
                Sequentially tests DNS lookup, default gateway ICMP ping, and public WAN uplink.
              </p>
            </div>
            <button
              onClick={handleConnectivityTest}
              disabled={connLoading}
              className="flex items-center gap-2 px-6 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black text-xs font-bold transition-all shadow-md disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${connLoading ? 'animate-spin' : ''}`} />
              <span>{connLoading ? 'Benchmarking...' : 'Run Connectivity Benchmark'}</span>
            </button>
          </div>

          {connResult && (
            <div className="space-y-4 animate-in fade-in">
              {/* Verdict Card */}
              <div
                className={`p-5 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                  connResult.verdict === 'HEALTHY'
                    ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-400'
                    : 'bg-amber-950/30 border-amber-800/60 text-amber-400'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5" />
                    <h3 className="text-sm font-bold text-cyber-text">
                      Network Verdict: {connResult.verdict}
                    </h3>
                  </div>
                  <p className="text-xs text-cyber-subtext mt-1">{connResult.summary}</p>
                </div>
                <Badge variant={connResult.verdict === 'HEALTHY' ? 'emerald' : 'amber'}>
                  {connResult.benchmark_duration_ms} ms benchmark
                </Badge>
              </div>

              {/* 3 Tier Benchmark Breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-cyber-subtext font-sans">Tier 1: Domain Name (DNS)</span>
                    <Server className="w-4 h-4 text-purple-400" />
                  </div>
                  <div className="text-base font-bold font-mono text-cyber-text">
                    {connResult.dns.ok ? 'Resolving OK' : 'DNS Failed'}
                  </div>
                  <div className="text-xs font-mono text-cyber-cyan">
                    {connResult.dns.latency_ms ? `${connResult.dns.latency_ms} ms` : '—'}
                  </div>
                </div>

                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-cyber-subtext font-sans">Tier 2: Router Gateway</span>
                    <Router className="w-4 h-4 text-sky-400" />
                  </div>
                  <div className="text-base font-bold font-mono text-cyber-text">
                    {connResult.gateway.ok ? 'Gateway Reachable' : 'Gateway Dropped'}
                  </div>
                  <div className="text-xs font-mono text-sky-400">
                    {connResult.gateway.latency_ms ? `${connResult.gateway.latency_ms} ms` : 'No ICMP Reply'}
                  </div>
                </div>

                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-cyber-subtext font-sans">Tier 3: Public Internet WAN</span>
                    <Wifi className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="text-base font-bold font-mono text-cyber-text">
                    {connResult.internet.ok ? 'Internet Online' : 'Internet Offline'}
                  </div>
                  <div className="text-xs font-mono text-emerald-400">
                    {connResult.internet.latency_ms ? `${connResult.internet.latency_ms} ms` : 'Offline'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
