import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { DiscoveredDevice } from '../types/network';
import { Badge } from '../components/common/Badge';
import { DeviceDetailDrawer } from '../components/common/DeviceDetailDrawer';
import { useToast } from '../components/common/Toast';
import {
  Search,
  RefreshCw,
  Download,
  Shield,
  Router,
  Laptop,
  CheckCircle2,
  Copy,
  StopCircle,
  Eye,
  SlidersHorizontal,
  Check,
  Tag
} from 'lucide-react';

interface DeviceDiscoveryPageProps {
  onNavigateToPing?: (ip: string) => void;
  onNavigateToPortScan?: (ip: string) => void;
}

export const DeviceDiscoveryPage: React.FC<DeviceDiscoveryPageProps> = ({
  onNavigateToPing,
  onNavigateToPortScan
}) => {
  const [devices, setDevices] = useState<DiscoveredDevice[]>([]);
  const [cidr, setCidr] = useState<string>('');
  const [scanning, setScanning] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [copiedIp, setCopiedIp] = useState<string | null>(null);
  const [scanDuration, setScanDuration] = useState<number | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<DiscoveredDevice | null>(null);
  const [progress, setProgress] = useState<{ scanned: number; total: number }>({ scanned: 0, total: 254 });

  const { addToast } = useToast();

  const loadInitialDevices = async () => {
    try {
      const data = await api.getDevices();
      setDevices(data);
      const ov = await api.getOverview();
      if (ov.cidr) setCidr(ov.cidr);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadInitialDevices();
  }, []);

  // Poll scan progress while scanning
  useEffect(() => {
    let interval: any;
    if (scanning) {
      interval = setInterval(async () => {
        try {
          const prog = await api.getScanProgress();
          if (prog && prog.total > 0) {
            setProgress({ scanned: prog.scanned, total: prog.total });
          }
        } catch (e) {
          // ignore
        }
      }, 500);
    }
    return () => clearInterval(interval);
  }, [scanning]);

  const handleScan = async () => {
    try {
      setScanning(true);
      addToast('info', 'Discovery Sweep Initiated', `Sweeping subnet ${cidr || 'auto'}...`);
      const res = await api.discoverDevices(cidr || undefined, 10);
      setDevices(res.devices);
      setScanDuration(res.duration_seconds);
      addToast('success', 'Discovery Complete', `Identified ${res.total_discovered} active hosts on subnet.`);
    } catch (err: any) {
      addToast('error', 'Discovery Sweep Failed', err.message);
    } finally {
      setScanning(false);
    }
  };

  const handleStop = async () => {
    try {
      await api.stopDiscovery();
      setScanning(false);
      addToast('info', 'Sweep Aborted', 'Cancellation signal sent to discovery engine.');
    } catch (e: any) {
      console.error(e);
    }
  };

  const copyToClipboard = (e: React.MouseEvent, text: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedIp(text);
    addToast('success', 'IP Copied', `Copied ${text} to clipboard.`);
    setTimeout(() => setCopiedIp(null), 2000);
  };

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

  const exportCSV = async () => {
    try {
      const blob = await api.exportDevices('csv');
      downloadBlob(blob, `netscope-devices-${Date.now()}.csv`);
      addToast('success', 'CSV Exported', `Saved ${devices.length} hosts to CSV file.`);
    } catch (err) {
      // Fallback
      if (!devices.length) return;
      const headers = ['IP Address', 'MAC Address', 'Vendor', 'Hostname', 'Custom Name', 'Category', 'Trusted', 'Role', 'Status', 'Response Time (ms)'];
      const rows = devices.map((d) => [
        d.ip,
        d.mac || 'N/A',
        `"${d.vendor}"`,
        d.hostname || 'N/A',
        `"${d.custom_name || ''}"`,
        `"${d.category || 'General'}"`,
        d.is_trusted ? 'Yes' : 'No',
        d.is_gateway ? 'Gateway' : d.is_local_host ? 'Localhost' : 'Host',
        d.status,
        d.response_time_ms ?? 'N/A'
      ]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', `netscope-devices-${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      addToast('success', 'CSV Exported', `Saved ${devices.length} hosts to CSV file.`);
    }
  };

  const exportJSON = async () => {
    try {
      const blob = await api.exportDevices('json');
      downloadBlob(blob, `netscope-devices-${Date.now()}.json`);
      addToast('success', 'JSON Exported', `Saved ${devices.length} hosts to JSON file.`);
    } catch (err) {
      if (!devices.length) return;
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(devices, null, 2));
      const link = document.createElement('a');
      link.setAttribute('href', dataStr);
      link.setAttribute('download', `netscope-devices-${Date.now()}.json`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      addToast('success', 'JSON Exported', `Saved ${devices.length} hosts to JSON file.`);
    }
  };

  const handleDeviceUpdated = (updated: DiscoveredDevice) => {
    setDevices((prev) => prev.map((d) => (d.id === updated.id || d.ip === updated.ip ? updated : d)));
    setSelectedDevice(updated);
    addToast('success', 'Device Saved', `Updated classification for ${updated.ip}.`);
  };

  const filtered = devices.filter((d) => {
    const q = searchQuery.toLowerCase();
    return (
      d.ip.toLowerCase().includes(q) ||
      (d.mac && d.mac.toLowerCase().includes(q)) ||
      d.vendor.toLowerCase().includes(q) ||
      (d.hostname && d.hostname.toLowerCase().includes(q)) ||
      (d.custom_name && d.custom_name.toLowerCase().includes(q)) ||
      (d.category && d.category.toLowerCase().includes(q))
    );
  });

  const progressPercent =
    progress.total > 0 ? Math.min(100, Math.round((progress.scanned / progress.total) * 100)) : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Network Device Discovery & Inventory
            <Badge variant="cyan">{devices.length} Discovered</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Active ARP scanning and TCP socket sweep across the local network interface
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-1 bg-cyber-card border border-cyber-border rounded-lg p-0.5">
            <button
              onClick={exportCSV}
              disabled={!devices.length}
              className="px-2.5 py-1 text-xs font-medium text-cyber-subtext hover:text-cyber-cyan transition-colors flex items-center gap-1 disabled:opacity-40"
              title="Export as CSV"
            >
              <Download className="w-3 h-3" /> CSV
            </button>
            <span className="text-cyber-border">|</span>
            <button
              onClick={exportJSON}
              disabled={!devices.length}
              className="px-2.5 py-1 text-xs font-medium text-cyber-subtext hover:text-cyber-cyan transition-colors flex items-center gap-1 disabled:opacity-40"
              title="Export as JSON"
            >
              <Download className="w-3 h-3" /> JSON
            </button>
          </div>
        </div>
      </div>

      {/* Discovery Control Bar */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
          <div className="w-full sm:w-64">
            <label className="text-[10px] font-mono text-cyber-subtext uppercase block mb-1">
              Target Subnet CIDR (Scoped to Host)
            </label>
            <input
              type="text"
              value={cidr}
              onChange={(e) => setCidr(e.target.value)}
              placeholder="e.g. 192.168.1.0/24"
              className="w-full bg-slate-900 border border-cyber-border rounded-lg px-3 py-2 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto mt-auto">
            {!scanning ? (
              <button
                onClick={handleScan}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-black text-xs font-bold transition-all shadow-md"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Run Discovery Sweep</span>
              </button>
            ) : (
              <button
                onClick={handleStop}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-md"
              >
                <StopCircle className="w-3.5 h-3.5" />
                <span>Stop Sweep</span>
              </button>
            )}
          </div>
        </div>

        {scanDuration && (
          <div className="text-xs font-mono text-cyber-subtext flex items-center gap-2">
            <span>Last Duration:</span>
            <span className="text-cyber-cyan font-medium">{scanDuration}s</span>
          </div>
        )}
      </div>

      {/* Live Scan Progress Bar */}
      {scanning && (
        <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/40 space-y-2 animate-in fade-in">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="text-cyber-cyan font-bold flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Sweeping ARP & TCP Sockets...
            </span>
            <span className="text-cyber-subtext">
              {progress.scanned} / {progress.total} Hosts ({progressPercent}%)
            </span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-cyber-border">
            <div
              className="bg-gradient-to-r from-cyan-400 to-sky-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Search Filter Strip */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-cyber-subtext absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by IP, MAC, hostname, custom name, or category..."
            className="w-full bg-cyber-card border border-cyber-border rounded-lg pl-9 pr-3 py-2 text-xs text-cyber-text placeholder:text-slate-500 focus:outline-none focus:border-cyber-cyan"
          />
        </div>
        <span className="text-xs font-mono text-cyber-subtext">
          Showing {filtered.length} of {devices.length} hosts
        </span>
      </div>

      {/* Discovered Devices Table */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-cyber-subtext font-mono uppercase text-[10px] border-b border-cyber-border">
              <tr>
                <th className="py-3 px-4">IPv4 Address</th>
                <th className="py-3 px-4">Physical Address (MAC)</th>
                <th className="py-3 px-4">Vendor / Manufacturer</th>
                <th className="py-3 px-4">Device Identity</th>
                <th className="py-3 px-4">Network Role</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Response Time</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border/60 font-mono">
              {filtered.map((dev, idx) => (
                <tr
                  key={dev.id || dev.ip || idx}
                  onClick={() => setSelectedDevice(dev)}
                  className="hover:bg-cyber-surface/80 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-4 text-cyber-cyan font-medium">
                    <div className="flex items-center gap-2">
                      {dev.is_gateway ? (
                        <Router className="w-4 h-4 text-sky-400 flex-shrink-0" />
                      ) : dev.is_local_host ? (
                        <Laptop className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      ) : (
                        <Shield className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      )}
                      <span>{dev.ip}</span>
                      {dev.is_trusted && (
                        <span title="Trusted Device" className="text-emerald-400">
                          <Check className="w-3 h-3" />
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="py-3 px-4 text-slate-300">
                    {dev.mac || <span className="text-slate-600">Local NIC</span>}
                  </td>

                  <td className="py-3 px-4 font-sans">
                    <span className="text-cyber-text font-medium">{dev.vendor}</span>
                  </td>

                  <td className="py-3 px-4">
                    {dev.custom_name ? (
                      <div>
                        <span className="text-cyber-cyan font-medium block">{dev.custom_name}</span>
                        <span className="text-cyber-subtext text-[10px]">{dev.hostname || '—'}</span>
                      </div>
                    ) : (
                      <span className="text-cyber-subtext">{dev.hostname || <span className="text-slate-600">—</span>}</span>
                    )}
                  </td>

                  <td className="py-3 px-4">
                    {dev.is_gateway ? (
                      <Badge variant="blue">Gateway Router</Badge>
                    ) : dev.is_local_host ? (
                      <Badge variant="emerald">Local Machine</Badge>
                    ) : (
                      <Badge variant="gray">Station</Badge>
                    )}
                  </td>

                  <td className="py-3 px-4 font-sans">
                    <span className="text-[11px] text-cyber-subtext px-2 py-0.5 rounded bg-black/40 border border-cyber-border">
                      {dev.category || 'General'}
                    </span>
                  </td>

                  <td className="py-3 px-4 text-cyber-subtext">
                    {dev.response_time_ms ? `${dev.response_time_ms} ms` : 'Active ARP'}
                  </td>

                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={(e) => copyToClipboard(e, dev.ip)}
                        title="Copy IP to clipboard"
                        className="p-1.5 rounded hover:bg-slate-800 text-cyber-subtext hover:text-cyber-text transition-colors"
                      >
                        {copiedIp === dev.ip ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                      <button
                        onClick={() => setSelectedDevice(dev)}
                        title="View Device Details & Inventory"
                        className="p-1.5 rounded hover:bg-slate-800 text-cyber-subtext hover:text-cyber-cyan transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-cyber-subtext">
                    No active devices matched your filter. Click "Run Discovery Sweep" to refresh.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Device Detail Slide-out Drawer */}
      <DeviceDetailDrawer
        device={selectedDevice}
        onClose={() => setSelectedDevice(null)}
        onNavigateToPing={onNavigateToPing}
        onNavigateToPortScan={onNavigateToPortScan}
        onDeviceUpdated={handleDeviceUpdated}
      />
    </div>
  );
};
