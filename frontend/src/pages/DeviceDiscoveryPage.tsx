import React, { useState, useEffect, useCallback } from 'react';
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
  Check,
  ChevronLeft,
  ChevronRight,
  Filter
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
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState<'all' | 'online' | 'offline'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loadingDevices, setLoadingDevices] = useState<boolean>(false);

  const [cidr, setCidr] = useState<string>('');
  const [scanning, setScanning] = useState<boolean>(false);
  const [copiedIp, setCopiedIp] = useState<string | null>(null);
  const [scanDuration, setScanDuration] = useState<number | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<DiscoveredDevice | null>(null);
  const [progress, setProgress] = useState<{ scanned: number; total: number }>({ scanned: 0, total: 254 });

  const { addToast } = useToast();

  const loadDevices = useCallback(async (
    targetPage: number = page,
    targetPageSize: number = pageSize,
    targetStatus: 'all' | 'online' | 'offline' = statusFilter,
    targetSearch: string = searchQuery
  ) => {
    try {
      setLoadingDevices(true);
      const res = await api.getPaginatedDevices({
        page: targetPage,
        pageSize: targetPageSize,
        status: targetStatus === 'all' ? undefined : targetStatus,
        search: targetSearch.trim() || undefined
      });
      setDevices(res.devices);
      setTotalCount(res.total_count);
      setTotalPages(res.total_pages);
      setPage(res.page);
    } catch (e) {
      console.error('Failed to load paginated devices:', e);
      // Fallback to legacy getDevices if paginated fails
      try {
        const fallback = await api.getDevices();
        setDevices(fallback);
        setTotalCount(fallback.length);
        setTotalPages(1);
      } catch (err) {
        console.error(err);
      }
    } finally {
      setLoadingDevices(false);
    }
  }, [page, pageSize, statusFilter, searchQuery]);

  // Initial load
  useEffect(() => {
    loadDevices(1, pageSize, statusFilter, searchQuery);
    api.getOverview().then(ov => {
      if (ov.cidr) setCidr(ov.cidr);
    }).catch(console.error);
  }, []);

  // Reload when page, pageSize, or statusFilter changes
  useEffect(() => {
    loadDevices(page, pageSize, statusFilter, searchQuery);
  }, [page, pageSize, statusFilter]);

  // Search input handler with delay
  useEffect(() => {
    const timer = setTimeout(() => {
      loadDevices(1, pageSize, statusFilter, searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

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
      setScanDuration(res.duration_seconds);
      addToast('success', 'Discovery Complete', `Identified ${res.total_discovered} active hosts on subnet.`);
      await loadDevices(1, pageSize, statusFilter, searchQuery);
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
      await loadDevices(page, pageSize, statusFilter, searchQuery);
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
      addToast('success', 'CSV Exported', `Saved inventory to CSV file.`);
    } catch (err) {
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
      addToast('success', 'CSV Exported', `Saved hosts to CSV file.`);
    }
  };

  const exportJSON = async () => {
    try {
      const blob = await api.exportDevices('json');
      downloadBlob(blob, `netscope-devices-${Date.now()}.json`);
      addToast('success', 'JSON Exported', `Saved inventory to JSON file.`);
    } catch (err) {
      if (!devices.length) return;
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(devices, null, 2));
      const link = document.createElement('a');
      link.setAttribute('href', dataStr);
      link.setAttribute('download', `netscope-devices-${Date.now()}.json`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      addToast('success', 'JSON Exported', `Saved hosts to JSON file.`);
    }
  };

  const handleDeviceUpdated = (updated: DiscoveredDevice) => {
    setDevices((prev) => prev.map((d) => (d.id === updated.id || d.ip === updated.ip ? updated : d)));
    setSelectedDevice(updated);
    addToast('success', 'Device Saved', `Updated classification for ${updated.ip}.`);
  };

  const progressPercent =
    progress.total > 0 ? Math.min(100, Math.round((progress.scanned / progress.total) * 100)) : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Network Device Discovery & Inventory
            <Badge variant="cyan">{totalCount} Registered</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Active ARP scanning and TCP socket sweep across the local network interface
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-1 bg-cyber-card border border-cyber-border rounded-lg p-0.5">
            <button
              onClick={exportCSV}
              disabled={!totalCount}
              className="px-2.5 py-1 text-xs font-medium text-cyber-subtext hover:text-cyber-cyan transition-colors flex items-center gap-1 disabled:opacity-40"
              title="Export as CSV"
            >
              <Download className="w-3 h-3" /> CSV
            </button>
            <span className="text-cyber-border">|</span>
            <button
              onClick={exportJSON}
              disabled={!totalCount}
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

      {/* Filters and Controls Strip */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 bg-cyber-card border border-cyber-border rounded-xl p-3">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1">
          <span className="text-cyber-subtext flex items-center gap-1 font-mono uppercase text-[10px] mr-2">
            <Filter className="w-3 h-3" /> Status:
          </span>
          {(['all', 'online', 'offline'] as const).map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setPage(1);
              }}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-colors ${
                statusFilter === st
                  ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40'
                  : 'text-cyber-subtext hover:text-cyber-text'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Search Input and Page Size Selector */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-72">
            <Search className="w-3.5 h-3.5 text-cyber-subtext absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search IP, MAC, vendor, hostname..."
              className="w-full bg-slate-900 border border-cyber-border rounded-lg pl-9 pr-3 py-1.5 text-xs text-cyber-text placeholder:text-slate-500 focus:outline-none focus:border-cyber-cyan"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs text-cyber-subtext font-mono">
            <span>Rows:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-slate-900 border border-cyber-border rounded px-2 py-1 text-cyber-text focus:outline-none focus:border-cyber-cyan"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
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
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Response Time</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border/60 font-mono">
              {devices.map((dev, idx) => (
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

                  <td className="py-3 px-4">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                      dev.status === 'online'
                        ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/50'
                        : 'bg-slate-900/40 text-slate-500 border border-slate-700/50'
                    }`}>
                      {dev.status ? dev.status.toUpperCase() : 'UNKNOWN'}
                    </span>
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
              {devices.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-cyber-subtext">
                    {loadingDevices
                      ? 'Loading device inventory...'
                      : 'No devices matched your query. Click "Run Discovery Sweep" to refresh.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 bg-slate-950/60 border-t border-cyber-border flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono">
          <div className="text-cyber-subtext">
            {totalCount > 0 ? (
              <span>
                Showing <strong className="text-cyber-text">{(page - 1) * pageSize + 1}</strong> to{' '}
                <strong className="text-cyber-text">{Math.min(page * pageSize, totalCount)}</strong> of{' '}
                <strong className="text-cyber-cyan">{totalCount}</strong> devices
              </span>
            ) : (
              <span>0 devices found</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loadingDevices}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-cyber-text disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Previous
            </button>
            <span className="px-2 text-cyber-subtext">
              Page <strong className="text-cyber-text">{page}</strong> of{' '}
              <strong className="text-cyber-text">{totalPages}</strong>
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loadingDevices}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-cyber-text disabled:opacity-40 transition-colors"
            >
              Next <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
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
