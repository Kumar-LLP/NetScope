import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { HealthInfo } from '../types/network';
import { Badge } from '../components/common/Badge';
import { Settings, Server, Database, Shield, Sliders, CheckCircle2, Trash2 } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [settings, setSettings] = useState<any>(null);
  const [pruning, setPruning] = useState<boolean>(false);
  const [pruneResult, setPruneResult] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getHealth(), api.getSettings()])
      .then(([h, s]) => {
        setHealth(h);
        setSettings(s);
      })
      .catch((e) => console.error(e));
  }, []);

  const handlePruneHistory = async () => {
    if (!confirm('Prune historical telemetry metrics older than 30 days?')) return;
    try {
      setPruning(true);
      const res = await api.cleanupHistory(30);
      setPruneResult(`Pruned ${res.pruned?.metrics || 0} telemetry rows and ${res.pruned?.diagnostics || 0} diagnostics.`);
    } catch (err: any) {
      alert(`Pruning failed: ${err.message || err}`);
    } finally {
      setPruning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            System & Platform Configuration
            <Badge variant="cyan">Configuration</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Engine runtime parameters, persistence status, and security guardrail settings
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Runtime Environment Card */}
        <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2.5 border-b border-cyber-border pb-3">
            <Server className="w-4 h-4 text-cyber-cyan" />
            <h3 className="text-sm font-semibold text-cyber-text">Host Runtime Environment</h3>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext">Operating System:</span>
              <span className="text-cyber-text font-medium">{health?.platform || 'Windows 11'}</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext">NetScope Engine:</span>
              <span className="text-cyber-cyan font-bold">v{health?.version || '1.0.0'}</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext">Backend Framework:</span>
              <span className="text-cyber-text">Python FastAPI + Asyncio</span>
            </div>

            <div className="flex justify-between py-1">
              <span className="text-cyber-subtext">Engine Health:</span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {health?.status.toUpperCase() || 'HEALTHY'}
              </span>
            </div>
          </div>
        </div>

        {/* Database & Storage Card */}
        <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2.5 border-b border-cyber-border pb-3">
            <Database className="w-4 h-4 text-cyber-blue" />
            <h3 className="text-sm font-semibold text-cyber-text">Storage & Persistence</h3>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext">Database Engine:</span>
              <span className="text-cyber-text font-medium">SQLite 3 (WAL Mode)</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext">ORM Layer:</span>
              <span className="text-cyber-text">SQLAlchemy 2.0 Async</span>
            </div>

            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext">Telemetry Sampling:</span>
              <span className="text-cyber-cyan">Every 1.5 Seconds (1Hz)</span>
            </div>

            <div className="flex justify-between py-1">
              <span className="text-cyber-subtext">DB Connectivity:</span>
              <span className="text-emerald-400 font-bold">Connected</span>
            </div>

            <div className="pt-2 border-t border-cyber-border/60 flex items-center justify-between">
              <span className="text-cyber-subtext">Retention (30 Days):</span>
              <button
                onClick={handlePruneHistory}
                disabled={pruning}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-950/30 border border-rose-900/60 hover:border-rose-600 text-rose-400 text-xs transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-3 h-3" />
                <span>{pruning ? 'Pruning...' : 'Prune Old History'}</span>
              </button>
            </div>
            {pruneResult && (
              <p className="text-[11px] text-emerald-400 pt-1">{pruneResult}</p>
            )}
          </div>
        </div>

        {/* Security Policies Card */}
        <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 space-y-4 md:col-span-2">
          <div className="flex items-center gap-2.5 border-b border-cyber-border pb-3">
            <Shield className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-cyber-text">Safety & Permission Guardrails</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3 rounded-lg bg-cyber-surface border border-cyber-border">
              <h4 className="font-semibold text-cyber-text mb-1">Non-Elevated Execution</h4>
              <p className="text-cyber-subtext text-[11px] leading-relaxed">
                NetScope operates strictly with standard user privileges on Windows 11. No Administrator or WinPcap installation required.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-cyber-surface border border-cyber-border">
              <h4 className="font-semibold text-cyber-text mb-1">Target Authorization</h4>
              <p className="text-cyber-subtext text-[11px] leading-relaxed">
                Port diagnostics enforce explicit confirmation before scanning. Concurrency is limited to 50 sockets to avoid local router overload.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-cyber-surface border border-cyber-border">
              <h4 className="font-semibold text-cyber-text mb-1">Zero Payload Storage</h4>
              <p className="text-cyber-subtext text-[11px] leading-relaxed">
                NetScope monitors metric rates and hardware metadata only. It never captures, inspects, or logs private plaintext traffic payloads.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
