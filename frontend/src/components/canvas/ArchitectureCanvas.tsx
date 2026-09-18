import React, { useCallback, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Connection,
  useReactFlow,
  ReactFlowProvider,
  BackgroundVariant,
  NodeTypes,
  EdgeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { CustomNode } from './CustomNode';
import { CustomEdge } from './CustomEdge';
import { ArchitectureNode, ArchitectureEdge, ComponentTemplate } from '../../types/architecture';

const nodeTypes: NodeTypes = {
  architectureNode: CustomNode as any,
};

const edgeTypes: EdgeTypes = {
  default: CustomEdge as any,
  architectureEdge: CustomEdge as any,
};

interface ArchitectureCanvasProps {
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  onNodesChange: any;
  onEdgesChange: any;
  onConnect: (connection: Connection) => void;
  onNodeClick: (node: ArchitectureNode) => void;
  onPaneClick: () => void;
  onDropComponent: (template: ComponentTemplate, position: { x: number; y: number }) => void;
}

const CanvasInner: React.FC<ArchitectureCanvasProps> = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onNodeClick,
  onPaneClick,
  onDropComponent,
}) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const rawData = event.dataTransfer.getData('application/archvis-node');
      if (!rawData) return;

      try {
        const template: ComponentTemplate = JSON.parse(rawData);
        const position = screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        onDropComponent(template, position);
      } catch (err) {
        console.error('Failed to parse dropped component:', err);
      }
    },
    [screenToFlowPosition, onDropComponent]
  );

  return (
    <div ref={reactFlowWrapper} className="w-full h-full relative" onDragOver={handleDragOver} onDrop={handleDrop}>
      <ReactFlow
        nodes={nodes as any}
        edges={edges as any}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={(_, node) => onNodeClick(node as unknown as ArchitectureNode)}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2.0}
        defaultEdgeOptions={{
          type: 'default',
          animated: true,
        }}
        className="bg-slate-50"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1.5}
          color="#CBD5E1"
          className="bg-[#F8FAFC]"
        />
        <Controls
          className="!bg-white !border-slate-200 !shadow-sm !rounded-xl overflow-hidden [&>button]:!border-slate-100 hover:[&>button]:!bg-slate-50"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={(node: any) => {
            const cat = node.data?.category;
            if (cat === 'database') return '#10B981';
            if (cat === 'queue') return '#8B5CF6';
            if (cat === 'cache') return '#F59E0B';
            if (cat === 'gateway') return '#F97316';
            if (cat === 'api') return '#06B6D4';
            return '#3B82F6';
          }}
          maskColor="rgba(241, 245, 249, 0.7)"
          className="!bg-white/90 !border !border-slate-200 !rounded-xl !shadow-sm overflow-hidden hidden sm:block"
        />
      </ReactFlow>
    </div>
  );
};

export const ArchitectureCanvas: React.FC<ArchitectureCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  );
};
