import React from 'react';
import { Bell, ShieldAlert, CheckCircle, Wifi, Activity, X } from 'lucide-react';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const EVENTS = [
  {
    id: '1',
    title: 'Network Telemetry Engine Started',
    desc: 'High-frequency 1Hz sampling loop active on local adapter.',
    time: 'Just now',
    type: 'success',
    icon: Activity
  },
  {
    id: '2',
    title: 'Default Gateway Baseline Verified',
    desc: 'Upstream gateway router resolved at 192.168.1.254.',
    time: '2m ago',
    type: 'info',
    icon: Wifi
  },
  {
    id: '3',
    title: 'Subnet Discovery Completed',
    desc: 'ARP cache sweep identified active stations and mapped vendor OUIs.',
    time: '5m ago',
    type: 'success',
    icon: CheckCircle
  },
  {
    id: '4',
    title: 'Security Baseline Satisfied',
    desc: 'No rogue DHCP/gateways or unencrypted Telnet listeners detected.',
    time: '12m ago',
    type: 'info',
    icon: ShieldAlert
  }
];

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end animate-in fade-in">
      <div className="w-full max-w-sm bg-cyber-surface border-l border-cyber-border h-full flex flex-col shadow-2xl animate-in slide-in-from-right-4">
        <div className="p-4 border-b border-cyber-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-cyber-cyan" />
            <h3 className="text-sm font-semibold text-cyber-text">Notification Center</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-cyber-subtext hover:text-cyber-text hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {EVENTS.map((ev) => {
            const Icon = ev.icon;
            return (
              <div
                key={ev.id}
                className="p-3 rounded-xl bg-cyber-card border border-cyber-border hover:border-cyber-muted transition-colors space-y-1"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-cyber-cyan" />
                    <h4 className="text-xs font-semibold text-cyber-text">{ev.title}</h4>
                  </div>
                  <span className="text-[10px] font-mono text-cyber-subtext">{ev.time}</span>
                </div>
                <p className="text-[11px] text-cyber-subtext leading-relaxed pl-5.5">{ev.desc}</p>
              </div>
            );
          })}
        </div>

        <div className="p-3 border-t border-cyber-border bg-cyber-bg/50 flex justify-between items-center text-[11px] text-cyber-subtext">
          <span>NetScope Audit Logging</span>
          <button
            onClick={onClose}
            className="px-2.5 py-1 rounded bg-cyber-card border border-cyber-border hover:border-cyber-muted text-cyber-text"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
};
