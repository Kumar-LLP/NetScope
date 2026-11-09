import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SecurityFinding } from '../types/network';
import { Badge } from '../components/common/Badge';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  RefreshCw,
  CheckCircle,
  ExternalLink
} from 'lucide-react';

export const SecurityInsightsPage: React.FC = () => {
  const [findings, setFindings] = useState<SecurityFinding[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchFindings = async () => {
    try {
      setLoading(true);
      const data = await api.getSecurityFindings();
      setFindings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, []);

  const criticalCount = findings.filter((f) => f.severity === 'critical').length;
  const highCount = findings.filter((f) => f.severity === 'high').length;
  const mediumCount = findings.filter((f) => f.severity === 'medium').length;

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

        <button
          onClick={fetchFindings}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs font-medium text-cyber-text transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyber-cyan' : ''}`} />
          <span>Re-run Security Audit</span>
        </button>
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
          <span className="text-[10px] font-mono text-cyber-subtext uppercase">Audit State</span>
          <div className="text-xl font-mono font-bold text-emerald-400 mt-1">Active</div>
        </div>
      </div>

      {/* Findings Cards List */}
      <div className="space-y-4">
        {findings.map((finding, idx) => {
          const isCritical = finding.severity === 'critical';
          const isHigh = finding.severity === 'high';
          const isMedium = finding.severity === 'medium';

          const borderStyle = isCritical
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
              key={idx}
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
                    <h3 className="text-sm font-semibold text-cyber-text">{finding.title}</h3>
                    <span className="text-[10px] font-mono text-cyber-subtext">
                      Rule ID: {finding.rule_id} • Category: {finding.category}
                    </span>
                  </div>
                </div>

                <Badge variant={badgeVariant} className="self-start sm:self-auto">
                  {finding.severity.toUpperCase()}
                </Badge>
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
            </div>
          );
        })}
      </div>
    </div>
  );
};
