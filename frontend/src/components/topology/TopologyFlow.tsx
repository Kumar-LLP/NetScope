import React, { useState } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CustomNode } from './CustomNodes';
import { RefreshCw, X, Shield, Activity, Radio } from 'lucide-react';

interface TopologyFlowProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  onRefresh: () => void;
  loading?: boolean;
}

const nodeTypes = {
  customNode: CustomNode,
  internetNode: CustomNode,
  gatewayNode: CustomNode,
  hostNode: CustomNode,
  deviceNode: CustomNode,
  dnsNode: CustomNode
};

export const TopologyFlow: React.FC<TopologyFlowProps> = ({
  initialNodes,
  initialEdges,
  onRefresh,
  loading = false
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // Sync if initial props change
  React.useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  React.useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node);
  };

  return (
    <div className="relative w-full h-[650px] bg-cyber-bg border border-cyber-border rounded-xl overflow-hidden">
      {/* Top action toolbar */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-3 bg-cyber-surface/90 backdrop-blur-md border border-cyber-border rounded-lg p-2 shadow-lg">
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-cyber-card border border-cyber-border hover:border-cyber-cyan text-xs font-medium text-cyber-text transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyber-cyan' : ''}`} />
          <span>Refresh Graph</span>
        </button>
        <span className="text-xs font-mono text-cyber-subtext border-l border-cyber-border pl-3">
          {nodes.length} Nodes Connected
        </span>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
      >
        <Background color="#1E293B" gap={20} size={1} />
        <Controls />
        <MiniMap
          nodeStrokeColor="#06B6D4"
          nodeColor="#151D2E"
          maskColor="rgba(11, 15, 23, 0.7)"
        />
      </ReactFlow>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute top-4 right-4 z-20 w-80 bg-cyber-surface/95 backdrop-blur-md border border-cyber-border rounded-xl p-4 shadow-2xl animate-in fade-in slide-in-from-right-4">
          <div className="flex items-center justify-between pb-3 border-b border-cyber-border">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-cyber-cyan" />
              <h3 className="text-sm font-semibold text-cyber-text">
                {selectedNode.data.label as string}
              </h3>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-cyber-subtext hover:text-cyber-text p-1 rounded-md"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-3 space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-cyber-border/50">
              <span className="text-cyber-subtext">Node Role:</span>
              <span className="font-mono text-cyber-cyan uppercase">
                {selectedNode.data.nodeType as string}
              </span>
            </div>

            {Boolean(selectedNode.data.ip) && (
              <div className="flex justify-between py-1 border-b border-cyber-border/50">
                <span className="text-cyber-subtext">IP Address:</span>
                <span className="font-mono text-cyber-text">
                  {selectedNode.data.ip as string}
                </span>
              </div>
            )}

            {Boolean(selectedNode.data.mac) && (
              <div className="flex justify-between py-1 border-b border-cyber-border/50">
                <span className="text-cyber-subtext">MAC Address:</span>
                <span className="font-mono text-cyber-text">
                  {selectedNode.data.mac as string}
                </span>
              </div>
            )}

            {Boolean(selectedNode.data.vendor) && (
              <div className="flex justify-between py-1 border-b border-cyber-border/50">
                <span className="text-cyber-subtext">Manufacturer:</span>
                <span className="text-cyber-text font-medium">
                  {selectedNode.data.vendor as string}
                </span>
              </div>
            )}

            <div className="flex justify-between py-1">
              <span className="text-cyber-subtext">Link Status:</span>
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <Radio className="w-3.5 h-3.5 animate-pulse" />
                Active Link
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
