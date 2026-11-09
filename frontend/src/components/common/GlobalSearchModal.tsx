import React, { useState, useEffect } from 'react';
import { Search, Activity, Network, Terminal, Radio, Shield, Server, ArrowRight, X } from 'lucide-react';
import { DiscoveredDevice } from '../../types/network';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  devices: DiscoveredDevice[];
  onNavigateTab: (tab: string, extraParam?: string) => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  devices,
  onNavigateTab
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        // Toggle search
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const staticModules = [
    { id: 'overview', title: 'Network Operations Center (NOC)', category: 'Module', icon: Activity },
    { id: 'discovery', title: 'Device Discovery & LAN Sweeper', category: 'Module', icon: Search },
    { id: 'topology', title: 'Interactive Network Topology Graph', category: 'Module', icon: Network },
    { id: 'diagnostics', title: 'Ping, DNS, Traceroute & Subnet Calculator', category: 'Diagnostics', icon: Terminal },
    { id: 'ports', title: 'Target Port Diagnostics & Banner Grabbing', category: 'Security', icon: Radio },
    { id: 'traffic', title: 'Real-time Traffic & Throughput Analytics', category: 'Analytics', icon: Activity },
    { id: 'security', title: 'Security Insights & Vulnerability Auditing', category: 'Security', icon: Shield },
    { id: 'history', title: 'Scan History & SQLite Audit Trail', category: 'Database', icon: Server }
  ];

  const filteredModules = staticModules.filter((m) =>
    m.title.toLowerCase().includes(query.toLowerCase()) || m.category.toLowerCase().includes(query.toLowerCase())
  );

  const filteredDevices = devices.filter(
    (d) =>
      d.ip.toLowerCase().includes(query.toLowerCase()) ||
      d.vendor.toLowerCase().includes(query.toLowerCase()) ||
      (d.hostname && d.hostname.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/75 backdrop-blur-md flex items-start justify-center pt-20 px-4 animate-in fade-in">
      <div className="w-full max-w-2xl bg-cyber-surface border border-cyber-border rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Search Input Header */}
        <div className="p-4 border-b border-cyber-border flex items-center gap-3 bg-cyber-card/60">
          <Search className="w-5 h-5 text-cyber-cyan" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search modules, diagnostic tools, hosts, or IP addresses..."
            autoFocus
            className="flex-1 bg-transparent text-sm text-cyber-text placeholder:text-slate-500 focus:outline-none font-sans"
          />
          <button
            onClick={onClose}
            className="p-1 rounded-md text-cyber-subtext hover:text-cyber-text hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-4 space-y-4">
          {/* Modules */}
          {filteredModules.length > 0 && (
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyber-subtext px-2 mb-2 block">
                Platform Modules & Tools
              </span>
              <div className="space-y-1">
                {filteredModules.map((m) => {
                  const Icon = m.icon;
                  return (
                    <button
                      key={m.id}
                      onClick={() => {
                        onNavigateTab(m.id);
                        onClose();
                      }}
                      className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-cyber-card transition-colors text-left group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-cyber-cyan group-hover:border-cyber-cyan/50">
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <h4 className="text-xs font-semibold text-cyber-text">{m.title}</h4>
                          <span className="text-[10px] font-mono text-cyber-subtext">{m.category}</span>
                        </div>
                      </div>
                      <ArrowRight className="w-3.5 h-3.5 text-cyber-subtext group-hover:text-cyber-cyan group-hover:translate-x-0.5 transition-all" />
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Discovered Hosts */}
          {filteredDevices.length > 0 && (
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyber-subtext px-2 mb-2 block">
                Discovered Network Hosts ({filteredDevices.length})
              </span>
              <div className="space-y-1">
                {filteredDevices.slice(0, 6).map((d, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      onNavigateTab('discovery');
                      onClose();
                    }}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-cyber-card transition-colors text-left group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400 group-hover:border-emerald-500/50">
                        <Activity className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-mono font-bold text-cyber-cyan">{d.ip}</h4>
                          <span className="text-[10px] font-sans text-cyber-subtext">({d.vendor})</span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-400">
                          {d.hostname || d.mac || 'Active Host'}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-cyber-subtext group-hover:text-cyber-text">
                      Inspect
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {filteredModules.length === 0 && filteredDevices.length === 0 && (
            <div className="py-8 text-center text-xs text-cyber-subtext">
              No matching tools, devices, or commands found for "{query}".
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-cyber-border bg-cyber-bg/50 flex justify-between items-center text-[11px] font-mono text-cyber-subtext px-4">
          <span>Navigate with click or Enter</span>
          <div className="flex items-center gap-2">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">ESC</span>
            <span>to close</span>
          </div>
        </div>
      </div>
    </div>
  );
};
