import React, { useState, useEffect } from 'react';
import { DiscoveredDevice, DeviceUpdateRequest } from '../../types/network';
import { Badge } from './Badge';
import { api } from '../../services/api';
import {
  X,
  Laptop,
  Router,
  Shield,
  Activity,
  Radio,
  Copy,
  CheckCircle2,
  Save,
  Tag,
  FileText,
  CheckSquare,
  Square
} from 'lucide-react';

interface DeviceDetailDrawerProps {
  device: DiscoveredDevice | null;
  onClose: () => void;
  onNavigateToPing?: (ip: string) => void;
  onNavigateToPortScan?: (ip: string) => void;
  onDeviceUpdated?: (updated: DiscoveredDevice) => void;
}

export const DeviceDetailDrawer: React.FC<DeviceDetailDrawerProps> = ({
  device,
  onClose,
  onNavigateToPing,
  onNavigateToPortScan,
  onDeviceUpdated
}) => {
  const [copied, setCopied] = useState(false);
  const [saving, setSaving] = useState(false);
  const [customName, setCustomName] = useState('');
  const [category, setCategory] = useState('');
  const [notes, setNotes] = useState('');
  const [isTrusted, setIsTrusted] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (device) {
      setCustomName(device.custom_name || '');
      setCategory(device.category || 'General');
      setNotes(device.notes || '');
      setIsTrusted(Boolean(device.is_trusted));
      setSaveSuccess(false);
    }
  }, [device]);

  if (!device) return null;

  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(device, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveInventory = async () => {
    if (!device.id) {
      alert('Cannot update device without a database ID.');
      return;
    }
    try {
      setSaving(true);
      const updateData: DeviceUpdateRequest = {
        custom_name: customName.trim() || null,
        category: category.trim() || null,
        notes: notes.trim() || null,
        is_trusted: isTrusted
      };
      const updated = await api.updateDevice(device.id, updateData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
      if (onDeviceUpdated) {
        onDeviceUpdated(updated);
      }
    } catch (err: any) {
      alert(`Failed to update device: ${err.message || err}`);
    } finally {
      setSaving(false);
    }
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
              <h2 className="text-sm font-bold text-cyber-text">
                {customName || device.hostname || device.ip}
              </h2>
              <p className="text-xs text-cyber-subtext font-mono">{device.ip} • {device.vendor}</p>
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
          {/* Status & Trust Pill */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-cyber-card border border-cyber-border">
            <span className="text-xs text-cyber-subtext">Operating Status:</span>
            <div className="flex items-center gap-2">
              {isTrusted && (
                <Badge variant="emerald">TRUSTED</Badge>
              )}
              <Badge variant={device.status === 'online' ? 'emerald' : 'gray'} pulse={device.status === 'online'}>
                {device.status.toUpperCase()}
              </Badge>
            </div>
          </div>

          {/* Inventory Management Form */}
          <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 space-y-3 text-xs">
            <span className="text-[10px] font-mono uppercase text-cyber-cyan block font-semibold">
              Device Inventory & Classification
            </span>

            <div>
              <label className="text-cyber-subtext text-[11px] block mb-1">Custom Device Name</label>
              <input
                type="text"
                placeholder="e.g. Master Bedroom Smart TV"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="w-full bg-black/50 border border-cyber-border rounded px-2.5 py-1.5 text-cyber-text text-xs focus:outline-none focus:border-cyber-cyan font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-cyber-subtext text-[11px] block mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-black/50 border border-cyber-border rounded px-2 py-1.5 text-cyber-text text-xs focus:outline-none focus:border-cyber-cyan font-mono"
                >
                  <option value="General">General Host</option>
                  <option value="Workstation">Workstation</option>
                  <option value="Server">Server / Infrastructure</option>
                  <option value="Router / Gateway">Router / Gateway</option>
                  <option value="IoT / Embedded">IoT / Smart Device</option>
                  <option value="Mobile">Mobile Device</option>
                  <option value="Printer">Network Printer</option>
                </select>
              </div>

              <div>
                <label className="text-cyber-subtext text-[11px] block mb-1">Trust Status</label>
                <button
                  type="button"
                  onClick={() => setIsTrusted(!isTrusted)}
                  className={`w-full flex items-center justify-center gap-2 py-1.5 rounded border text-xs font-medium transition-colors ${
                    isTrusted
                      ? 'bg-emerald-950/40 border-emerald-700/60 text-emerald-400'
                      : 'bg-black/40 border-cyber-border text-cyber-subtext'
                  }`}
                >
                  {isTrusted ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
                  <span>{isTrusted ? 'Verified Trusted' : 'Untrusted / New'}</span>
                </button>
              </div>
            </div>

            <div>
              <label className="text-cyber-subtext text-[11px] block mb-1">Inventory Notes</label>
              <textarea
                rows={2}
                placeholder="Operational notes, static assignment, or rack location..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full bg-black/50 border border-cyber-border rounded px-2.5 py-1.5 text-cyber-text text-xs focus:outline-none focus:border-cyber-cyan resize-none"
              />
            </div>

            <button
              onClick={handleSaveInventory}
              disabled={saving}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-cyber-cyan/20 border border-cyber-cyan hover:bg-cyber-cyan/30 text-cyber-cyan font-semibold text-xs transition-colors disabled:opacity-50"
            >
              {saveSuccess ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Inventory Saved!</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>{saving ? 'Saving...' : 'Update Device Inventory'}</span>
                </>
              )}
            </button>
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
              <span className="text-cyber-subtext font-sans">DNS Hostname:</span>
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
