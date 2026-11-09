import React from 'react';

interface BadgeProps {
  variant?: 'blue' | 'cyan' | 'emerald' | 'amber' | 'rose' | 'purple' | 'gray';
  children: React.ReactNode;
  pulse?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'cyan',
  children,
  pulse = false,
  className = ''
}) => {
  const variantStyles = {
    blue: 'bg-sky-950/60 text-sky-400 border-sky-800/60',
    cyan: 'bg-cyan-950/60 text-cyan-400 border-cyan-800/60',
    emerald: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60',
    amber: 'bg-amber-950/60 text-amber-400 border-amber-800/60',
    rose: 'bg-rose-950/60 text-rose-400 border-rose-800/60',
    purple: 'bg-purple-950/60 text-purple-400 border-purple-800/60',
    gray: 'bg-slate-800/60 text-slate-400 border-slate-700/60'
  };

  const pulseStyles = {
    blue: 'bg-sky-400',
    cyan: 'bg-cyan-400',
    emerald: 'bg-emerald-400',
    amber: 'bg-amber-400',
    rose: 'bg-rose-400',
    purple: 'bg-purple-400',
    gray: 'bg-slate-400'
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${variantStyles[variant]} ${className}`}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pulseStyles[variant]}`}
          />
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${pulseStyles[variant]}`}
          />
        </span>
      )}
      {children}
    </span>
  );
};
