import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SecurityFinding, GatewayBaselineResponse } from '../types/network';
import { Badge } from '../components/common/Badge';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  RefreshCw,
  CheckCircle,
  Download,
  Check,
  RotateCcw,
  Clock,
  Filter
} from 'lucide-react';

export const SecurityInsightsPage: React.FC = () => {
  const [findings, setFindings] = useState<SecurityFinding[]>([]);
  const [baseline, setBaseline] = useState<GatewayBaselineResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'active' | 'acknowledged' | 'resolved' | 'all'>('active');
  const [customMacInput, setCustomMacInput] = useState<string>('');
  const [showCustomMac, setShowCustomMac] = useState<boolean>(false);

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

  const loadData = async () => {
    try {
      setLoading(true);
      const [findingsData, baselineData] = await Promise.all([
        statusFilter === 'all' || statusFilter === 'acknowledged' || statusFilter === 'resolved'
          ? api.getSecurityFindingsHistory(200)
          : api.getSecurityFindings(),
        api.getGatewayBaseline()
      ]);
      setFindings(findingsData);
      setBaseline(baselineData);
    } catch (err) {
      console.error('Failed to load security insights data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleConfirmBaseline = async (macToConfirm?: string) => {
    try {
      setActionLoading('confirm-baseline');
      await api.confirmGatewayBaseline(macToConfirm || baseline?.detected_mac || undefined);
      setShowCustomMac(false);
      setCustomMacInput('');
      await loadData();
    } catch (err: any) {
      alert(`Error confirming baseline: ${err.message || err}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResetBaseline = async () => {
    if (!confirm('Are you sure you want to reset the confirmed gateway MAC baseline?')) return;
    try {
      setActionLoading('reset-baseline');
      await api.resetGatewayBaseline();
      await loadData();
    } catch (err: any) {
      alert(`Error resetting baseline: ${err.message || err}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleAcknowledgeFinding = async (findingId: number) => {
    try {
      setActionLoading(`ack-${findingId}`);
      await api.acknowledgeSecurityFinding(findingId);
      await loadData();
    } catch (err: any) {
      alert(`Error acknowledging finding: ${err.message || err}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolveFinding = async (findingId: number) => {
    try {
      setActionLoading(`resolve-${findingId}`);
      await api.resolveSecurityFinding(findingId);
      await loadData();
    } catch (err: any) {
      alert(`Error resolving finding: ${err.message || err}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await api.exportSecurityFindings(format);
      downloadBlob(blob, `netscope_security_findings_${Date.now()}.${format}`);
    } catch (err: any) {
      alert(`Export failed: ${err.message || err}`);
    }
  };

  const filteredFindings = findings.filter((f) => {
    if (statusFilter === 'all') return true;
    return (f.status || 'active').toLowerCase() === statusFilter;
  });

  const criticalCount = findings.filter((f) => f.severity === 'critical' && f.status !== 'resolved').length;
  const highCount = findings.filter((f) => f.severity === 'high' && f.status !== 'resolved').length;
  const mediumCount = findings.filter((f) => f.severity === 'medium' && f.status !== 'resolved').length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Security Insights & Vulnerability Auditing
            <Badge variant={criticalCount > 0 ? 'rose' : 'emerald'}>
              {findings.length} Observations
            </Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Deterministic security heuristics evaluating ARP consistency, unencrypted services, and exposure risks
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          <div className="flex items-center gap-1 bg-cyber-card border border-cyber-border rounded-lg p-0.5">
            <button
              onClick={() => handleExport('csv')}
              className="px-2.5 py-1 text-xs font-medium text-cyber-subtext hover:text-cyber-cyan transition-colors flex items-center gap-1"
              title="Export as CSV"
            >
              <Download className="w-3 h-3" /> CSV
            </button>
            <span className="text-cyber-border">|</span>
            <button
              onClick={() => handleExport('json')}
              className="px-2.5 py-1 text-xs font-medium text-cyber-subtext hover:text-cyber-cyan transition-colors flex items-center gap-1"
              title="Export as JSON"
            >
              <Download className="w-3 h-3" /> JSON
            </button>
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs font-medium text-cyber-text transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyber-cyan' : ''}`} />
            <span>Re-run Audit</span>
          </button>
        </div>
      </div>

      {/* Gateway ARP Baseline Protection Card */}
      <div className={`p-5 rounded-xl border transition-all ${
        baseline?.status === 'mismatch'
          ? 'bg-rose-950/20 border-rose-700/60'
          : baseline?.status === 'confirmed'
          ? 'bg-emerald-950/10 border-emerald-700/40'
          : 'bg-amber-950/20 border-amber-700/50'
      }`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              {baseline?.status === 'mismatch' ? (
                <ShieldAlert className="w-5 h-5 text-rose-400" />
              ) : baseline?.status === 'confirmed' ? (
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              )}
              <h2 className="text-sm font-semibold text-cyber-text tracking-wide">
                Default Gateway MAC Baseline Security
              </h2>
              <Badge variant={
                baseline?.status === 'confirmed' ? 'emerald' :
                baseline?.status === 'mismatch' ? 'rose' : 'amber'
              }>
                {baseline?.status ? baseline.status.toUpperCase() : 'UNKNOWN'}
              </Badge>
            </div>
            <p className="text-xs text-cyber-subtext leading-relaxed">
              {baseline?.status === 'confirmed'
                ? 'Gateway MAC is confirmed by operator. Any ARP divergence from this baseline will trigger an immediate high-priority alert.'
                : baseline?.status === 'mismatch'
                ? 'CRITICAL WARNING: The detected gateway MAC does not match your confirmed baseline! Potential ARP Poisoning / Man-In-The-Middle attack.'
                : 'The gateway MAC has been detected but is UNCONFIRMED. Inspect the MAC below and confirm it to protect against ARP spoofing.'}
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
            {baseline?.status !== 'confirmed' && (
              <button
                onClick={() => handleConfirmBaseline()}
                disabled={actionLoading === 'confirm-baseline' || !baseline?.detected_mac}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-cyan/20 border border-cyber-cyan hover:bg-cyber-cyan/30 text-xs font-semibold text-cyber-cyan transition-colors disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Confirm Current MAC</span>
              </button>
            )}

            <button
              onClick={() => setShowCustomMac(!showCustomMac)}
              className="px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-subtext text-xs text-cyber-text transition-colors"
            >
              {showCustomMac ? 'Cancel' : 'Enter Custom MAC'}
            </button>

            {baseline?.baseline_mac && (
              <button
                onClick={handleResetBaseline}
                disabled={actionLoading === 'reset-baseline'}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-cyber-card border border-rose-900/40 hover:border-rose-600 text-xs text-rose-400 transition-colors disabled:opacity-50"
                title="Reset confirmed baseline"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>

        {/* Custom MAC Input Bar */}
        {showCustomMac && (
          <div className="mt-4 pt-4 border-t border-cyber-border flex items-center gap-3">
            <input
              type="text"
              placeholder="e.g. 00:11:22:33:44:55"
              value={customMacInput}
              onChange={(e) => setCustomMacInput(e.target.value)}
              className="bg-black/60 border border-cyber-border rounded px-3 py-1.5 text-xs font-mono text-cyber-text focus:outline-none focus:border-cyber-cyan w-64"
            />
            <button
              onClick={() => handleConfirmBaseline(customMacInput)}
              disabled={!customMacInput || actionLoading === 'confirm-baseline'}
              className="px-3 py-1.5 rounded bg-cyber-cyan text-black font-semibold text-xs disabled:opacity-50"
            >
              Save & Confirm
            </button>
          </div>
        )}

        {/* Gateway Telemetry Metadata */}
        <div className="mt-4 pt-3 border-t border-cyber-border/40 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          <div>
            <span className="text-cyber-subtext text-[10px] block uppercase">Gateway IP:</span>
            <span className="text-cyber-text font-bold">{baseline?.gateway_ip || 'None detected'}</span>
          </div>
          <div>
            <span className="text-cyber-subtext text-[10px] block uppercase">Detected MAC (Live):</span>
            <span className="text-cyber-cyan font-bold">{baseline?.detected_mac || 'None'}</span>
          </div>
          <div>
            <span className="text-cyber-subtext text-[10px] block uppercase">Confirmed Baseline MAC:</span>
            <span className={`font-bold ${baseline?.status === 'mismatch' ? 'text-rose-400' : 'text-emerald-400'}`}>
              {baseline?.baseline_mac || '(Unconfirmed)'}
            </span>
          </div>
        </div>
      </div>

      {/* Severity Ticker Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
          <span className="text-[10px] font-mono text-cyber-subtext uppercase">Critical Risks</span>
          <div className="text-xl font-mono font-bold text-rose-400 mt-1">{criticalCount}</div>
        </div>

        <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
          <span className="text-[10px] font-mono text-cyber-subtext uppercase">High Priority</span>
          <div className="text-xl font-mono font-bold text-amber-400 mt-1">{highCount}</div>
        </div>

        <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
          <span className="text-[10px] font-mono text-cyber-subtext uppercase">Medium Severity</span>
          <div className="text-xl font-mono font-bold text-sky-400 mt-1">{mediumCount}</div>
        </div>

        <div className="bg-cyber-card border border-cyber-border rounded-xl p-4">
          <span className="text-[10px] font-mono text-cyber-subtext uppercase">Total Stored</span>
          <div className="text-xl font-mono font-bold text-cyber-cyan mt-1">{findings.length}</div>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-cyber-border pb-2 text-xs">
        <span className="text-cyber-subtext flex items-center gap-1 font-mono uppercase text-[11px] mr-2">
          <Filter className="w-3.5 h-3.5" /> Filter:
        </span>
        {(['active', 'acknowledged', 'resolved', 'all'] as const).map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1 rounded-md font-medium capitalize transition-colors ${
              statusFilter === st
                ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40'
                : 'text-cyber-subtext hover:text-cyber-text'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Findings Cards List */}
      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="text-center py-12 bg-cyber-card border border-cyber-border rounded-xl">
            <ShieldCheck className="w-12 h-12 text-emerald-400/80 mx-auto mb-3" />
            <h3 className="text-base font-medium text-cyber-text">No {statusFilter !== 'all' ? statusFilter : ''} Findings</h3>
            <p className="text-xs text-cyber-subtext mt-1">
              Your network interfaces and observed traffic comply with all baseline security heuristics.
            </p>
          </div>
        ) : (
          filteredFindings.map((finding) => {
            const isCritical = finding.severity === 'critical';
            const isHigh = finding.severity === 'high';
            const isMedium = finding.severity === 'medium';
            const isResolved = finding.status === 'resolved';
            const isAcked = finding.status === 'acknowledged';

            const borderStyle = isResolved
              ? 'border-cyber-border/40 bg-cyber-card/40 opacity-75'
              : isCritical
              ? 'border-rose-800/60 bg-rose-950/20'
              : isHigh
              ? 'border-amber-800/60 bg-amber-950/20'
              : isMedium
              ? 'border-sky-800/60 bg-sky-950/20'
              : 'border-cyber-border bg-cyber-card';

            const badgeVariant = isCritical
              ? 'rose'
              : isHigh
              ? 'amber'
              : isMedium
              ? 'cyan'
              : 'emerald';

            return (
              <div
                key={finding.id || finding.rule_id}
                className={`border rounded-xl p-5 space-y-4 transition-all duration-200 ${borderStyle}`}
              >
                {/* Finding Title & Badges */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-cyber-border/60 pb-3">
                  <div className="flex items-center gap-2.5">
                    <ShieldAlert
                      className={`w-5 h-5 flex-shrink-0 ${
                        isCritical ? 'text-rose-400' : isHigh ? 'text-amber-400' : 'text-cyber-cyan'
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-cyber-text">{finding.title}</h3>
                        {finding.status && (
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                            finding.status === 'resolved'
                              ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/50'
                              : finding.status === 'acknowledged'
                              ? 'bg-amber-950/40 text-amber-400 border border-amber-800/50'
                              : 'bg-rose-950/40 text-rose-400 border border-rose-800/50'
                          }`}>
                            {finding.status.toUpperCase()}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] font-mono text-cyber-subtext">
                        Rule ID: {finding.rule_id} • Category: {finding.category}
                        {finding.target ? ` • Target: ${finding.target}` : ''}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    <Badge variant={badgeVariant}>
                      {finding.severity.toUpperCase()}
                    </Badge>

                    {/* Finding Lifecycle Actions */}
                    {finding.id && (
                      <div className="flex items-center gap-1.5 ml-2">
                        {!isAcked && !isResolved && (
                          <button
                            onClick={() => handleAcknowledgeFinding(finding.id!)}
                            disabled={actionLoading === `ack-${finding.id}`}
                            className="px-2.5 py-1 rounded bg-cyber-card border border-cyber-border hover:border-amber-500 text-[11px] font-mono text-amber-400 transition-colors disabled:opacity-50"
                            title="Acknowledge this finding"
                          >
                            Acknowledge
                          </button>
                        )}

                        {!isResolved && (
                          <button
                            onClick={() => handleResolveFinding(finding.id!)}
                            disabled={actionLoading === `resolve-${finding.id}`}
                            className="px-2.5 py-1 rounded bg-emerald-950/40 border border-emerald-800 hover:bg-emerald-900/40 text-[11px] font-mono text-emerald-400 transition-colors disabled:opacity-50"
                            title="Mark finding as resolved"
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Technical Description & Evidence */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <h4 className="font-semibold text-cyber-text mb-1">Observation & Context</h4>
                    <p className="text-cyber-subtext leading-relaxed">{finding.description}</p>
                    <div className="mt-2.5 p-2.5 rounded bg-black/50 border border-cyber-border/80 font-mono text-cyber-cyan text-[11px]">
                      <span className="text-cyber-subtext block text-[9px] uppercase">Telemetry Evidence:</span>
                      {finding.evidence}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-cyber-text mb-1">Threat Impact</h4>
                    <p className="text-cyber-subtext leading-relaxed">{finding.impact}</p>

                    <h4 className="font-semibold text-emerald-400 mt-3 mb-1 flex items-center gap-1.5">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Recommended Remediation Action
                    </h4>
                    <p className="text-cyber-text leading-relaxed bg-emerald-950/30 border border-emerald-800/40 p-2.5 rounded">
                      {finding.remediation}
                    </p>
                  </div>
                </div>

                {/* Timestamps Footer */}
                {(finding.created_at || finding.acknowledged_at || finding.resolved_at) && (
                  <div className="pt-2 border-t border-cyber-border/40 flex items-center gap-4 text-[10px] font-mono text-cyber-subtext">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Detected: {finding.created_at ? new Date(finding.created_at).toLocaleString() : 'N/A'}
                    </span>
                    {finding.acknowledged_at && (
                      <span className="text-amber-400/80">
                        Ack: {new Date(finding.acknowledged_at).toLocaleString()}
                      </span>
                    )}
                    {finding.resolved_at && (
                      <span className="text-emerald-400/80">
                        Resolved: {new Date(finding.resolved_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
