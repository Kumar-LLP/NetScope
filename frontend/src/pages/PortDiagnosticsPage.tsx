import React, { useState } from 'react';
import { api } from '../services/api';
import { PortScanResponse } from '../types/network';
import { Badge } from '../components/common/Badge';
import {
  Radio,
  Play,
  ShieldCheck,
  AlertTriangle,
  Download,
  Server,
  Lock,
  Unlock,
  CheckCircle2
} from 'lucide-react';

const PORT_PROFILES = {
  top20: {
    label: 'Top 20 Common',
    ports: [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 3306, 3389, 5432, 8000, 8080]
  },
  web: {
    label: 'Web & API',
    ports: [80, 443, 8000, 8080, 8443, 9000]
  },
  database: {
    label: 'Databases',
    ports: [1433, 1521, 3306, 5432, 6379, 27017]
  },
  remote: {
    label: 'Remote Access',
    ports: [21, 22, 23, 3389, 5900]
  }
};

interface PortDiagnosticsPageProps {
  initialTarget?: string;
}

export const PortDiagnosticsPage: React.FC<PortDiagnosticsPageProps> = ({
  initialTarget
}) => {
  const [target, setTarget] = useState<string>(initialTarget || '127.0.0.1');
  const [selectedProfile, setSelectedProfile] = useState<keyof typeof PORT_PROFILES>('top20');
  const [customPorts, setCustomPorts] = useState<string>('21, 22, 80, 443, 8000');
  const [useCustom, setUseCustom] = useState<boolean>(false);
  const [authorized, setAuthorized] = useState<boolean>(true);
  const [scanning, setScanning] = useState<boolean>(false);
  const [scanResult, setScanResult] = useState<PortScanResponse | null>(null);

  const getPortsToScan = (): number[] => {
    if (useCustom) {
      return customPorts
        .split(',')
        .map((p) => parseInt(p.trim(), 10))
        .filter((p) => !isNaN(p) && p > 0 && p <= 65535);
    }
    return PORT_PROFILES[selectedProfile].ports;
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authorized) {
      alert('You must confirm target authorization before initiating a port scan.');
      return;
    }

    const ports = getPortsToScan();
    if (!ports.length) {
      alert('Please specify at least one valid port number.');
      return;
    }

    try {
      setScanning(true);
      const res = await api.runPortScan(target, ports, 500, true);
      setScanResult(res);
    } catch (err: any) {
      alert(`Port scan error: ${err.message}`);
    } finally {
      setScanning(false);
    }
  };

  const exportResults = () => {
    if (!scanResult) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(scanResult, null, 2));
    const link = document.createElement('a');
    link.setAttribute('href', dataStr);
    link.setAttribute('download', `port-scan-${scanResult.target}-${Date.now()}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Target Port Diagnostics
            <Badge variant="purple">Controlled TCP Connect</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Non-intrusive service identification and banner detection with authorization guardrails
          </p>
        </div>

        {scanResult && (
          <button
            onClick={exportResults}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-muted text-xs font-medium text-cyber-text transition-colors self-start sm:self-auto"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Results</span>
          </button>
        )}
      </div>

      {/* Port Scanner Configuration Card */}
      <form onSubmit={handleScan} className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
              Authorized Target IP or Hostname
            </label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="e.g. 127.0.0.1 or 192.168.1.1"
              required
              className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
            />
          </div>

          <div>
            <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
              Port Selection Mode
            </label>
            <div className="flex flex-wrap items-center gap-2">
              {(Object.keys(PORT_PROFILES) as Array<keyof typeof PORT_PROFILES>).map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => {
                    setSelectedProfile(key);
                    setUseCustom(false);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    !useCustom && selectedProfile === key
                      ? 'bg-cyber-surface text-cyber-cyan border border-cyber-cyan/40'
                      : 'bg-slate-900 text-cyber-subtext border border-cyber-border hover:text-cyber-text'
                  }`}
                >
                  {PORT_PROFILES[key].label}
                </button>
              ))}

              <button
                type="button"
                onClick={() => setUseCustom(true)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  useCustom
                    ? 'bg-cyber-surface text-cyber-cyan border border-cyber-cyan/40'
                    : 'bg-slate-900 text-cyber-subtext border border-cyber-border hover:text-cyber-text'
                }`}
              >
                Custom Ports
              </button>
            </div>
          </div>
        </div>

        {useCustom && (
          <div>
            <label className="text-[10px] font-mono uppercase text-cyber-subtext mb-1 block">
              Comma-Separated Port List
            </label>
            <input
              type="text"
              value={customPorts}
              onChange={(e) => setCustomPorts(e.target.value)}
              placeholder="e.g. 21, 22, 80, 443, 3306, 8000"
              className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
            />
          </div>
        )}

        {/* Authorization Checkbox Guardrail */}
        <div className="pt-2 border-t border-cyber-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <label className="flex items-center gap-2.5 text-xs text-cyber-subtext cursor-pointer select-none">
            <input
              type="checkbox"
              checked={authorized}
              onChange={(e) => setAuthorized(e.target.checked)}
              className="rounded bg-slate-900 border-cyber-border text-cyber-cyan focus:ring-0 w-4 h-4"
            />
            <span>I confirm that I have explicit authorization to audit and scan this target machine.</span>
          </label>

          <button
            type="submit"
            disabled={scanning || !authorized}
            className="flex items-center justify-center gap-2 px-6 py-2 rounded-lg bg-cyber-cyan hover:bg-cyan-400 text-black text-xs font-bold transition-all disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            <span>{scanning ? 'Scanning Ports...' : 'Execute TCP Scan'}</span>
          </button>
        </div>
      </form>

      {/* Results Section */}
      {scanResult && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
              <span className="text-[10px] font-mono text-cyber-subtext uppercase">Target Scanned</span>
              <div className="text-lg font-mono font-bold text-cyber-text mt-1">{scanResult.target}</div>
            </div>

            <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
              <span className="text-[10px] font-mono text-cyber-subtext uppercase">Total Ports Audited</span>
              <div className="text-lg font-mono font-bold text-cyber-cyan mt-1">
                {scanResult.total_scanned} Ports
              </div>
            </div>

            <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
              <span className="text-[10px] font-mono text-cyber-subtext uppercase">Open Services Found</span>
              <div className="text-lg font-mono font-bold text-emerald-400 mt-1">
                {scanResult.open_count} Open
              </div>
            </div>
          </div>

          <div className="bg-cyber-card border border-cyber-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/60 text-cyber-subtext font-mono uppercase text-[10px] border-b border-cyber-border">
                  <tr>
                    <th className="py-2.5 px-4">Port Number</th>
                    <th className="py-2.5 px-4">State</th>
                    <th className="py-2.5 px-4">Standard Service Name</th>
                    <th className="py-2.5 px-4">Banner / Response Greeting</th>
                    <th className="py-2.5 px-4 text-right">RTT Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cyber-border/60 font-mono">
                  {scanResult.results.map((r, idx) => (
                    <tr key={idx} className="hover:bg-cyber-surface/60 transition-colors">
                      <td className="py-2.5 px-4 font-bold text-cyber-text">
                        {r.port}
                      </td>

                      <td className="py-2.5 px-4">
                        {r.state === 'open' ? (
                          <Badge variant="emerald" pulse>OPEN</Badge>
                        ) : r.state === 'filtered' ? (
                          <Badge variant="amber">FILTERED</Badge>
                        ) : (
                          <Badge variant="gray">CLOSED</Badge>
                        )}
                      </td>

                      <td className="py-2.5 px-4 font-sans text-cyber-text">
                        {r.service || 'Unknown'}
                      </td>

                      <td className="py-2.5 px-4 text-cyber-cyan truncate max-w-xs">
                        {r.banner || <span className="text-slate-600">—</span>}
                      </td>

                      <td className="py-2.5 px-4 text-right text-cyber-subtext">
                        {r.rtt_ms ? `${r.rtt_ms} ms` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
