import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Badge } from '../components/common/Badge';
import { History, RefreshCw, Clock, CheckCircle, Database } from 'lucide-react';

export const ScanHistoryPage: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getHistory();
      setHistory(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Scan History & Audit Trail
            <Badge variant="cyan">{history.length} Runs</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Historical subnet discovery and port audit runs stored in SQLite WAL database
          </p>
        </div>

        <button
          onClick={fetchHistory}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs font-medium text-cyber-text transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh History</span>
        </button>
      </div>

      {/* History Table */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-cyber-subtext font-mono uppercase text-[10px] border-b border-cyber-border">
              <tr>
                <th className="py-3 px-4">Scan ID</th>
                <th className="py-3 px-4">Operation Type</th>
                <th className="py-3 px-4">Target Scope</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Targets Identified</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border/60 font-mono">
              {history.map((item, idx) => (
                <tr key={idx} className="hover:bg-cyber-surface/60 transition-colors">
                  <td className="py-3 px-4 text-cyber-cyan font-bold">{item.id}</td>
                  <td className="py-3 px-4 font-sans text-cyber-text">
                    {item.scan_type === 'device_discovery' ? 'Subnet Device Sweep' : item.scan_type}
                  </td>
                  <td className="py-3 px-4 text-slate-300">{item.target_range}</td>
                  <td className="py-3 px-4">
                    <Badge variant="emerald">COMPLETED</Badge>
                  </td>
                  <td className="py-3 px-4 text-cyber-text font-bold">{item.found_targets}</td>
                  <td className="py-3 px-4 text-cyber-subtext">{item.duration_seconds}s</td>
                  <td className="py-3 px-4 text-right text-cyber-subtext">
                    {item.created_at ? new Date(item.created_at).toLocaleString() : 'Recent'}
                  </td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-cyber-subtext">
                    No scan history recorded yet. Run a device discovery sweep to generate audit logs.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
