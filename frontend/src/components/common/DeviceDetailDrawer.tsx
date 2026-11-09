import React from 'react';
import { DiscoveredDevice } from '../../types/network';
import { Badge } from './Badge';
import {
  X,
  Laptop,
  Router,
  Shield,
  Activity,
  Terminal,
  Radio,
  Copy,
  Clock,
  CheckCircle2
} from 'lucide-react';

interface DeviceDetailDrawerProps {
  device: DiscoveredDevice | null;
  onClose: () => void;
  onNavigateToPing?: (ip: string) => void;
  onNavigateToPortScan?: (ip: string) => void;
}

export const DeviceDetailDrawer: React.FC<DeviceDetailDrawerProps> = ({
  device,
  onClose,
  onNavigateToPing,
  onNavigateToPortScan
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!device) return null;

  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(device, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-cyber-surface border-l border-cyber-border h-full flex flex-col shadow-2xl animate-in slide-in-from-right-4">
        {/* Header */}
        <div className="p-5 border-b border-cyber-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyber-cyan">
              {device.is_gateway ? (
                <Router className="w-5 h-5 text-sky-400" />
              ) : device.is_local_host ? (
                <Laptop className="w-5 h-5 text-emerald-400" />
              ) : (
                <Shield className="w-5 h-5 text-slate-300" />
              )}
            </div>
            <div>
              <h2 className="text-sm font-bold text-cyber-text">{device.ip}</h2>
              <p className="text-xs text-cyber-subtext">{device.vendor}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-cyber-subtext hover:text-cyber-text hover:bg-cyber-card transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Status Pill */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-cyber-card border border-cyber-border">
            <span className="text-xs text-cyber-subtext">Operating Status:</span>
            <Badge variant="emerald" pulse>
              ACTIVE ON SUBNET
            </Badge>
          </div>

          {/* Properties Table */}
          <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 space-y-3 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext font-sans">IPv4 Address:</span>
              <span className="text-cyber-cyan font-bold">{device.ip}</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext font-sans">Physical Address (MAC):</span>
              <span className="text-cyber-text">{device.mac || 'Local System Adapter'}</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext font-sans">Hardware Vendor:</span>
              <span className="text-cyber-text font-sans font-medium">{device.vendor}</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext font-sans">Hostname:</span>
              <span className="text-cyber-text">{device.hostname || 'Unresolved (No PTR)'}</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext font-sans">Network Role:</span>
              <span className="text-cyber-text uppercase">
                {device.is_gateway ? 'Default Gateway Router' : device.is_local_host ? 'Localhost (This PC)' : 'LAN Host'}
              </span>
            </div>

            <div className="flex justify-between py-1">
              <span className="text-cyber-subtext font-sans">Discovery Latency:</span>
              <span className="text-emerald-400 font-bold">
                {device.response_time_ms ? `${device.response_time_ms} ms` : '< 1 ms (ARP Cache)'}
              </span>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="space-y-2 pt-2">
            <span className="text-[10px] font-mono uppercase text-cyber-subtext block">
              Quick Diagnostic Actions
            </span>

            {onNavigateToPing && (
              <button
                onClick={() => {
                  onNavigateToPing(device.ip);
                  onClose();
                }}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs text-cyber-text transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Activity className="w-4 h-4 text-cyber-cyan" />
                  <span>Execute ICMP Ping Test</span>
                </div>
                <span className="text-cyber-subtext text-[10px] font-mono">4 packets</span>
              </button>
            )}

            {onNavigateToPortScan && (
              <button
                onClick={() => {
                  onNavigateToPortScan(device.ip);
                  onClose();
                }}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-purple text-xs text-cyber-text transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Radio className="w-4 h-4 text-cyber-purple" />
                  <span>Audit TCP Ports on Host</span>
                </div>
                <span className="text-cyber-subtext text-[10px] font-mono">Common ports</span>
              </button>
            )}

            <button
              onClick={handleCopyJSON}
              className="w-full flex items-center justify-center gap-2 p-2.5 rounded-lg bg-slate-900 border border-cyber-border hover:border-cyber-muted text-xs text-cyber-subtext hover:text-cyber-text transition-colors"
            >
              {copied ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Device JSON Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Device Record (JSON)</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-cyber-border bg-cyber-bg/50 flex justify-between items-center text-xs text-cyber-subtext">
          <span>NetScope Device Profile</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-muted text-cyber-text"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
