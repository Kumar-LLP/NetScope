import React from 'react';
import {
  Activity,
  Radio,
  Search,
  Network,
  Terminal,
  ShieldAlert,
  BarChart3,
  History,
  Settings,
  BookOpen,
  Wifi
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenGlossary: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  onOpenGlossary
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'discovery', label: 'Device Discovery', icon: Search },
    { id: 'topology', label: 'Network Topology', icon: Network },
    { id: 'diagnostics', label: 'Diagnostic Tools', icon: Terminal },
    { id: 'ports', label: 'Port Diagnostics', icon: Radio },
    { id: 'traffic', label: 'Traffic Analytics', icon: BarChart3 },
    { id: 'security', label: 'Security Insights', icon: ShieldAlert },
    { id: 'history', label: 'Scan History', icon: History },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-cyber-surface border-r border-cyber-border flex flex-col h-screen select-none">
      {/* Brand Logo */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-cyber-border">
        <div className="relative p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-sky-500/20 border border-cyber-cyan/40">
          <Wifi className="w-5 h-5 text-cyber-cyan" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-lg text-cyber-text tracking-wide">NetScope</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-cyber-subtext font-mono truncate">NOC & Threat Intelligence</p>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold tracking-wider uppercase text-slate-500">
          Operations Center
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-cyber-card text-cyber-cyan border border-cyber-cyan/30 shadow-sm'
                  : 'text-cyber-subtext hover:text-cyber-text hover:bg-cyber-card/60'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyber-cyan' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Educational Mode & System Card */}
      <div className="p-4 border-t border-cyber-border space-y-3">
        <button
          onClick={onOpenGlossary}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-blue text-xs font-medium text-cyber-text transition-colors"
        >
          <BookOpen className="w-4 h-4 text-cyber-blue" />
          <span>Learning Center</span>
        </button>

        <div className="bg-cyber-card/60 border border-cyber-border/80 rounded-lg p-2.5 text-[11px] font-mono text-cyber-subtext flex items-center justify-between">
          <span>Engine Status</span>
          <span className="text-emerald-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            Active 1Hz
          </span>
        </div>
      </div>
    </aside>
  );
};
