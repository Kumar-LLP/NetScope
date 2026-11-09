import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'blue' | 'cyan' | 'emerald' | 'amber' | 'rose' | 'purple';
  trend?: string;
  loading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  variant = 'cyan',
  trend,
  loading = false
}) => {
  const iconColors = {
    blue: 'text-sky-400 bg-sky-950/50 border-sky-800/40',
    cyan: 'text-cyan-400 bg-cyan-950/50 border-cyan-800/40',
    emerald: 'text-emerald-400 bg-emerald-950/50 border-emerald-800/40',
    amber: 'text-amber-400 bg-amber-950/50 border-amber-800/40',
    rose: 'text-rose-400 bg-rose-950/50 border-rose-800/40',
    purple: 'text-purple-400 bg-purple-950/50 border-purple-800/40'
  };

  return (
    <div className="bg-cyber-card border border-cyber-border rounded-xl p-5 hover:border-cyber-muted transition-all duration-200">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-cyber-subtext uppercase tracking-wider">
          {title}
        </span>
        <div className={`p-2 rounded-lg border ${iconColors[variant]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        {loading ? (
          <div className="h-8 w-24 bg-slate-800 animate-pulse rounded"></div>
        ) : (
          <>
            <span className="text-2xl font-bold font-mono text-cyber-text tracking-tight">
              {value}
            </span>
            {unit && <span className="text-xs text-cyber-subtext font-mono">{unit}</span>}
          </>
        )}
      </div>

      {(subtitle || trend) && (
        <div className="mt-2 flex items-center justify-between text-xs text-cyber-subtext">
          <span>{subtitle}</span>
          {trend && <span className="font-mono text-cyber-cyan">{trend}</span>}
        </div>
      )}
    </div>
  );
};
