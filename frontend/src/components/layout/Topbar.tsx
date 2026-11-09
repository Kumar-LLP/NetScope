import React, { useState, useEffect } from 'react';
import { TelemetryPayload } from '../../types/network';
import { ArrowDown, ArrowUp, Activity, Wifi, BookOpen, ShieldCheck } from 'lucide-react';
import { Badge } from '../common/Badge';

interface TopbarProps {
  telemetry: TelemetryPayload | null;
  wsConnected: boolean;
  onOpenGlossary: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  telemetry,
  wsConnected,
  onOpenGlossary
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

      {/* Right Controls & Clock */}
      <div className="flex items-center gap-4">
        <button
          onClick={onOpenGlossary}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-blue text-xs font-medium text-cyber-text transition-colors"
        >
          <BookOpen className="w-3.5 h-3.5 text-cyber-blue" />
          <span className="hidden sm:inline">Learn Networking</span>
        </button>

        <div className="flex items-center gap-2 text-xs font-mono text-cyber-subtext px-2 py-1 rounded bg-slate-900 border border-slate-800">
          <span>UTC</span>
          <span className="text-cyber-text font-medium">{timeStr}</span>
        </div>
      </div>
    </header>
  );
};
