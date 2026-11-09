import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { TopologyResponse } from '../types/network';
import { TopologyFlow } from '../components/topology/TopologyFlow';
import { Badge } from '../components/common/Badge';
import { Network, Globe, Router, Laptop, Server, Smartphone, Info } from 'lucide-react';

export const TopologyPage: React.FC = () => {
  const [topology, setTopology] = useState<TopologyResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchTopology = async () => {
    try {
      setLoading(true);
      const data = await api.getTopology();
      setTopology(data);
    } catch (err) {
      console.error('Failed to load topology:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopology();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-cyber-border">
        <div>
          <h1 className="text-xl font-bold text-cyber-text tracking-tight flex items-center gap-2">
            Interactive Network Topology
            <Badge variant="cyan">Dynamic Graph</Badge>
          </h1>
          <p className="text-xs text-cyber-subtext mt-1">
            Visual map of upstream gateway routes, DNS resolvers, and connected LAN stations
          </p>
        </div>

        {/* Legend Pills */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-cyber-subtext">
          <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-cyber-card border border-cyber-border">
            <Globe className="w-3.5 h-3.5 text-cyan-400" />
            Internet
          </span>
          <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-cyber-card border border-cyber-border">
            <Router className="w-3.5 h-3.5 text-sky-400" />
            Gateway
          </span>
          <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-cyber-card border border-cyber-border">
            <Laptop className="w-3.5 h-3.5 text-emerald-400" />
            Host
          </span>
          <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-cyber-card border border-cyber-border">
            <Server className="w-3.5 h-3.5 text-purple-400" />
            DNS
          </span>
          <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-cyber-card border border-cyber-border">
            <Smartphone className="w-3.5 h-3.5 text-slate-400" />
            LAN Host
          </span>
        </div>
      </div>

      {/* Topology Canvas */}
      {topology && (
        <TopologyFlow
          initialNodes={topology.nodes as any}
          initialEdges={topology.edges as any}
          onRefresh={fetchTopology}
          loading={loading}
        />
      )}

      {/* Helpful usage guide notice */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 flex items-start gap-3 text-xs text-cyber-subtext">
        <Info className="w-4 h-4 text-cyber-cyan mt-0.5 flex-shrink-0" />
        <div>
          <p className="font-semibold text-cyber-text">How to Interact with Topology Graph:</p>
          <p className="mt-1 leading-relaxed">
            Drag any node to customize the layout. Scroll to zoom in and out. Click on any node to view detailed hardware
            addresses (MAC), manufacturer information (OUI), and active IP routes in the side drawer.
          </p>
        </div>
      </div>
    </div>
  );
};
