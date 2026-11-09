import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Globe, Router, Laptop, Smartphone, Server } from 'lucide-react';

export const CustomNode = memo(({ data }: NodeProps) => {
  const nodeType = data.nodeType as string;

  const nodeConfigs: Record<string, { icon: any; border: string; glow: string; text: string }> = {
    internet: {
      icon: Globe,
      border: 'border-cyan-500/50',
      glow: 'shadow-[0_0_15px_rgba(6,182,212,0.2)]',
      text: 'text-cyan-400'
    },
    gateway: {
      icon: Router,
      border: 'border-sky-500/50',
      glow: 'shadow-[0_0_15px_rgba(56,189,248,0.2)]',
      text: 'text-sky-400'
    },
    host: {
      icon: Laptop,
      border: 'border-emerald-500/50',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]',
      text: 'text-emerald-400'
    },
    device: {
      icon: Smartphone,
      border: 'border-slate-700 hover:border-slate-500',
      glow: 'shadow-sm',
      text: 'text-slate-300'
    },
    dns: {
      icon: Server,
      border: 'border-purple-500/50',
      glow: 'shadow-[0_0_15px_rgba(139,92,246,0.2)]',
      text: 'text-purple-400'
    }
  };

  const config = nodeConfigs[nodeType] || nodeConfigs.device;
  const Icon = config.icon;

  return (
    <div
      className={`min-w-[190px] bg-cyber-card/90 backdrop-blur-md border ${config.border} ${config.glow} rounded-xl p-3 text-left transition-all duration-200 cursor-pointer`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-cyber-cyan !w-2 !h-2 !border-none"
      />

      <div className="flex items-center gap-2.5">
        <div className={`p-2 rounded-lg bg-slate-900/80 border border-slate-800 ${config.text}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 overflow-hidden">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-cyber-text truncate">
              {data.label as string}
            </h4>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          </div>
          <p className="text-[10px] text-cyber-subtext truncate mt-0.5">
            {(data.subLabel as string) || (data.vendor as string) || 'Active Host'}
          </p>
        </div>
      </div>

      {Boolean(data.ip) && (
        <div className="mt-2.5 pt-2 border-t border-cyber-border flex items-center justify-between text-[11px] font-mono text-cyber-cyan">
          <span>{data.ip as string}</span>
          {Boolean(data.mac) && (
            <span className="text-[9px] text-cyber-subtext uppercase">
              {((data.mac as string) || '').slice(-8)}
            </span>
          )}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-cyber-cyan !w-2 !h-2 !border-none"
      />
    </div>
  );
});
CustomNode.displayName = 'CustomNode';
