import React, { useState, useEffect } from 'react';
import { TelemetryPayload } from '../../types/network';
import { ArrowDown, ArrowUp, Activity, Search, Bell, BookOpen } from 'lucide-react';
import { Badge } from '../common/Badge';

interface TopbarProps {
  telemetry: TelemetryPayload | null;
  wsConnected: boolean;
  onOpenGlossary: () => void;
  onOpenSearch: () => void;
  onOpenNotifications: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  telemetry,
  wsConnected,
  onOpenGlossary,
  onOpenSearch,
  onOpenNotifications
}) => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      setTimeStr(new Date().toLocaleTimeString());
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const downFormatted = telemetry?.bandwidth.download_formatted || '0 KB/s';
  const upFormatted = telemetry?.bandwidth.upload_formatted || '0 KB/s';
  const pingMs = telemetry?.ping_ms !== undefined && telemetry.ping_ms !== null ? `${telemetry.ping_ms} ms` : 'N/A';

  return (
    <header className="h-16 bg-cyber-surface/90 backdrop-blur-md border-b border-cyber-border px-6 flex items-center justify-between z-20">
      {/* Left Connection Badges */}
      <div className="flex items-center gap-3">
        <Badge variant={wsConnected ? 'emerald' : 'rose'} pulse={wsConnected}>
          {wsConnected ? 'LIVE FEED CONNECTED' : 'DISCONNECTED'}
        </Badge>

        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-cyber-card border border-cyber-border text-xs font-mono text-cyber-subtext">
          <Activity className="w-3.5 h-3.5 text-cyber-cyan" />
          <span>Latency:</span>
          <span className="text-cyber-text font-medium">{pingMs}</span>
        </div>

        <div className="hidden md:flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1 text-emerald-400">
            <ArrowDown className="w-3.5 h-3.5" />
            <span>{downFormatted}</span>
          </div>
          <div className="flex items-center gap-1 text-sky-400">
            <ArrowUp className="w-3.5 h-3.5" />
            <span>{upFormatted}</span>
          </div>
        </div>
      </div>

      {/* Center Search Bar Trigger */}
      <div className="flex items-center">
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-cyber-card border border-cyber-border hover:border-cyber-cyan/50 text-xs text-cyber-subtext hover:text-cyber-text transition-all group"
          title="Global Search (Ctrl+K)"
        >
          <Search className="w-3.5 h-3.5 text-cyber-cyan group-hover:scale-110 transition-transform" />
          <span className="hidden lg:inline text-xs">Search tools, hosts & IPs...</span>
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-slate-900 border border-slate-700 text-slate-400 rounded">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* Right Controls & Clock */}
      <div className="flex items-center gap-3">
        {/* Notification Bell */}
        <button
          onClick={onOpenNotifications}
          className="relative p-2 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan/50 text-cyber-subtext hover:text-cyber-text transition-colors"
          title="Notification Center"
        >
          <Bell className="w-4 h-4 text-cyber-subtext" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyber-cyan animate-pulse border-2 border-cyber-surface" />
        </button>

        <button
          onClick={onOpenGlossary}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-blue text-xs font-medium text-cyber-text transition-colors"
        >
          <BookOpen className="w-3.5 h-3.5 text-cyber-blue" />
          <span className="hidden sm:inline">Learn Networking</span>
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-cyber-subtext px-2 py-1 rounded bg-slate-900 border border-slate-800">
          <span>UTC</span>
          <span className="text-cyber-text font-medium">{timeStr}</span>
        </div>
      </div>
    </header>
  );
};
