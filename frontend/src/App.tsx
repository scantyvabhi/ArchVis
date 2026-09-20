import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
} from '@xyflow/react';

import { TopBar } from './components/layout/TopBar';
import { ArchitectureCanvas } from './components/canvas/ArchitectureCanvas';
import { ComponentDrawer } from './components/sidebar/ComponentDrawer';
import { NodeConfigDrawer } from './components/drawer/NodeConfigDrawer';
import { FloatingAssistant } from './components/assistant/FloatingAssistant';
import { RepoIngestionModal } from './components/assistant/RepoIngestionModal';
import { MetricsOverlay } from './components/assistant/MetricsOverlay';

import {
  ArchitectureNode,
  ArchitectureEdge,
  AppMode,
  ComponentTemplate,
  SimulationMetrics,
  ChatMessage,
} from './types/architecture';
import { PRESET_ARCHITECTURES } from './constants/presets';
import { getLayoutedElements } from './utils/layout';
import {
  exportCanvasToPng,
  exportArchitectureJson,
  parseImportedJson,
} from './utils/export';
import {
  orchestrateAgents,
  generateArchitecture,
  parseRepo,
  sendChatMessage,
  checkBackendHealth,
} from './services/api';
import { AgentThinkingStep } from './types/architecture';

export function App() {
  // Load initial preset (e.g. E-Commerce Microservices)
  const initialPreset = PRESET_ARCHITECTURES[0];
  const [nodes, setNodes, onNodesChange] = useNodesState<ArchitectureNode>(initialPreset.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<ArchitectureEdge>(initialPreset.edges);

  const [mode, setMode] = useState<AppMode>('pro');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isRepoModalOpen, setIsRepoModalOpen] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [currentAgentThinking, setCurrentAgentThinking] = useState<AgentThinkingStep | undefined>(undefined);

  // Live Simulation Engine State
  const [isSimulating, setIsSimulating] = useState(false);
  const [metrics, setMetrics] = useState<SimulationMetrics>({
    isRunning: false,
    totalThroughput: 0,
    averageLatency: 0,
    p99Latency: 0,
    systemErrorRate: 0,
    bottlenecksCount: 0,
    overloadedNodes: [],
    warningNodes: [],
    tickCount: 0,
  });

  const workerRef = useRef<Worker | null>(null);

  // Chat History
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-msg',
      sender: 'assistant',
      text: `👋 Welcome to ArchVis AI!\n\nI can help you design scalable systems, diagnose latency bottlenecks, or reverse-engineer repos into visual flow diagrams.\n\n• Switch between **Learner Mode** (architectural concepts & rationales) and **Professional Mode** (concrete HLD/LLD tech stacks).\n• Click **Run Simulation** to watch traffic propagate and discover bottlenecks!`,
      timestamp: new Date().toISOString(),
    },
  ]);

  // Selected node object reference
  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || null;

  // Initialize Web Worker
  useEffect(() => {
    try {
      const worker = new Worker(
        new URL('./workers/simulation.worker.ts', import.meta.url),
        { type: 'module' }
      );
      workerRef.current = worker;

      worker.onmessage = (event: MessageEvent) => {
        const { type, payload } = event.data;
        if (type === 'TICK') {
          const { nodeUpdates, metrics: newMetrics } = payload;
          setMetrics(newMetrics);

          // Update nodes on canvas with simulated metrics
          setNodes((prevNodes) =>
            prevNodes.map((node) => {
              const update = nodeUpdates[node.id];
              if (!update) return node;
              return {
                ...node,
                data: {
                  ...node.data,
                  status: update.status,
                  rps: update.rps,
                  effectiveLatency: update.effectiveLatency,
                  effectiveErrorRate: update.effectiveErrorRate,
                  utilization: update.utilization,
                  droppedRps: update.droppedRps,
                },
              };
            })
          );
        }
      };

      // Push initial graph structure to worker
      worker.postMessage({
        type: 'INIT',
        payload: { nodes: initialPreset.nodes, edges: initialPreset.edges },
      });

      return () => {
        worker.terminate();
      };
    } catch (err) {
      console.warn('Simulation Web Worker initialization error:', err);
    }
  }, []);

  // Check backend health periodically
  useEffect(() => {
    const checkHealth = async () => {
      const health = await checkBackendHealth();
      setBackendHealthy(health.status === 'ok' || health.status === 'healthy');
    };
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  // Synchronize canvas graph changes with worker
  useEffect(() => {
    if (workerRef.current) {
      workerRef.current.postMessage({
        type: 'UPDATE_GRAPH',
        payload: { nodes, edges },
      });
    }
  }, [nodes, edges]);

  // Toggle Simulation Run / Stop
  const handleToggleSimulation = () => {
    const nextState = !isSimulating;
    setIsSimulating(nextState);

    if (workerRef.current) {
      if (nextState) {
        workerRef.current.postMessage({ type: 'START' });
      } else {
        workerRef.current.postMessage({ type: 'STOP' });
        // Reset node visual overload states
        setNodes((prev) =>
          prev.map((n) => ({
            ...n,
            data: {
              ...n.data,
              status: 'healthy',
              utilization: 0,
              droppedRps: 0,
              effectiveLatency: n.data.latency,
              effectiveErrorRate: n.data.failureRate,
            },
          }))
        );
        setMetrics((prev) => ({ ...prev, isRunning: false }));
      }
    }
  };

  // Connect two nodes
  const handleConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: 'default',
            animated: true,
            data: { protocol: 'HTTP/REST' },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  // Add Component from Sidebar Click
  const handleAddComponent = (template: ComponentTemplate) => {
    const newNodeId = `node-${Date.now()}`;
    const newNode: ArchitectureNode = {
      id: newNodeId,
      type: 'architectureNode',
      position: {
        x: 250 + Math.random() * 200,
        y: 180 + Math.random() * 200,
      },
      data: {
        label: template.label,
        category: template.category,
        tech: template.tech,
        latency: template.defaultLatency,
        rps: 1000,
        capacity: template.defaultCapacity,
        failureRate: template.defaultFailureRate,
        replication: template.defaultReplication,
        description: template.description,
        explanation: `${template.label} using ${template.tech}.`,
        status: 'healthy',
      },
    };

    setNodes((nds) => [...nds, newNode]);
    setSelectedNodeId(newNodeId);
  };

  // Drop Component from Drag and Drop
  const handleDropComponent = (
    template: ComponentTemplate,
    position: { x: number; y: number }
  ) => {
    const newNodeId = `node-${Date.now()}`;
    const newNode: ArchitectureNode = {
      id: newNodeId,
      type: 'architectureNode',
      position,
      data: {
        label: template.label,
        category: template.category,
        tech: template.tech,
        latency: template.defaultLatency,
        rps: 1000,
        capacity: template.defaultCapacity,
        failureRate: template.defaultFailureRate,
        replication: template.defaultReplication,
        description: template.description,
        explanation: `${template.label} using ${template.tech}.`,
        status: 'healthy',
      },
    };

    setNodes((nds) => [...nds, newNode]);
    setSelectedNodeId(newNodeId);
  };

  // Update Node Data from Drawer
  const handleUpdateNode = (id: string, updatedData: any) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          return {
            ...node,
            data: {
              ...node.data,
              ...updatedData,
            },
          };
        }
        return node;
      })
    );
  };

  // Delete Node & connected edges
  const handleDeleteNode = (id: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== id));
    setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
    if (selectedNodeId === id) setSelectedNodeId(null);
  };

  // Clear Canvas
  const handleClearCanvas = () => {
    if (confirm('Are you sure you want to clear the entire architecture canvas?')) {
      setNodes([]);
      setEdges([]);
      setSelectedNodeId(null);
      if (isSimulating) handleToggleSimulation();
    }
  };

  // Auto Layout using Dagre
  const handleAutoLayout = () => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(nodes, edges, 'LR');
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  };

  // Load Preset Architecture
  const handleLoadPreset = (presetId: string) => {
    const found = PRESET_ARCHITECTURES.find((p) => p.id === presetId);
    if (found) {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        found.nodes,
        found.edges,
        'LR'
      );
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      setMode(found.mode);
      setSelectedNodeId(null);

      // Add a helpful assistant note
      setMessages((prev) => [
        ...prev,
        {
          id: `preset-${Date.now()}`,
          sender: 'assistant',
          text: `Loaded **${found.name}** in ${found.mode.toUpperCase()} mode.\n\n${found.description}\n\nClick **Run Simulation** to test throughput limits!`,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  // Export to High-Res PNG
  const handleExportPng = async () => {
    try {
      const reactFlowInstance = document.querySelector('.react-flow') as any;
      const viewport = reactFlowInstance?.getViewport?.() || { x: 0, y: 0, zoom: 1 };
      await exportCanvasToPng(nodes, edges, viewport, `archvis-${mode}-architecture.png`);
    } catch (err) {
      alert('Could not export PNG. Check console for details.');
    }
  };

  // Export JSON
  const handleExportJson = () => {
    exportArchitectureJson(nodes, edges, `archvis-${mode}`);
  };

  // Import JSON
  const handleImportJson = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const parsed = parseImportedJson(content);
        setNodes(parsed.nodes);
        setEdges(parsed.edges);
      } catch (err: any) {
        alert(err.message || 'Invalid JSON architecture file');
      }
    };
    reader.readAsText(file);
  };

  // AI Architecture Generation via Prompt
  const handleGenerateArchitecture = async (prompt: string) => {
    setIsAiLoading(true);
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: prompt,
        timestamp: new Date().toISOString(),
      },
    ]);

    try {
      const result = await generateArchitecture(prompt, mode);
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        result.nodes,
        result.edges,
        'LR'
      );
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);

      let reply = `Synthesized architecture for: "${prompt}"\n\n${result.summary}`;
      if (result.recommendations && result.recommendations.length > 0) {
        reply += `\n\n**Key Design Considerations:**\n` + result.recommendations.map((r: string) => `• ${r}`).join('\n');
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          sender: 'assistant',
          text: reply,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ Could not generate architecture: ${err.message}. Please check your backend connection or Gemini API key.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsAiLoading(false);
    }
  };

  // Ingest GitHub Repository
  const handleIngestRepo = async (repoUrl: string) => {
    setIsAiLoading(true);
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: `Reverse-engineer repository: ${repoUrl}`,
        timestamp: new Date().toISOString(),
      },
    ]);

    try {
      const result = await parseRepo(repoUrl, mode);
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        result.nodes,
        result.edges,
        'LR'
      );
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);

      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          sender: 'assistant',
          text: `Extracted architecture from **${repoUrl}**:\n\n${result.summary}\n\n**Detected Technologies:** ${result.repo_info?.detected_tech?.join(', ') || 'Standard Stack'}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ Error analyzing repository: ${err.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
      throw err;
    } finally {
      setIsAiLoading(false);
    }
  };

  // Ingest Documentation Content
  const handleIngestDoc = async (docContent: string) => {
    await handleGenerateArchitecture(`System Design from Document Specification:\n${docContent.slice(0, 1500)}`);
  };

  // Send contextual AI Chat Message
  const handleSendChatMessage = async (messageText: string) => {
    setIsAiLoading(true);
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: messageText,
        timestamp: new Date().toISOString(),
      },
    ]);

    try {
      const result = await sendChatMessage(
        messageText,
        { nodes, edges },
        mode
      );

      // If the chat returned a diagram, apply it to the canvas
      if (result.diagram) {
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
          result.diagram.nodes,
          result.diagram.edges,
          'LR'
        );
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          sender: 'assistant',
          text: result.reply,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ Chat service temporarily unavailable: ${err.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsAiLoading(false);
    }
  };

  // Multi-Agent Orchestration
  const handleOrchestrateAgents = async (prompt: string, repoUrl?: string) => {
    setIsAiLoading(true);
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: prompt,
        timestamp: new Date().toISOString(),
      },
    ]);

    try {
      const { orchestrateAgents } = await import('./services/api');
      const result = await orchestrateAgents({
        prompt,
        repo_url: repoUrl,
        canvas_state: { nodes, edges },
        mode,
        orchestration_mode: 'consensus',
      });

      if (result.diagram) {
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
          result.diagram.nodes,
          result.diagram.edges,
          'LR'
        );
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);

        let reply = `🤖 **Multi-Agent Orchestration Complete**\n\n`;
        reply += `**Session:** ${result.session_id}\n`;
        reply += `**Execution Time:** ${result.total_execution_time_ms}ms\n\n`;
        reply += `**Summary:** ${result.diagram.summary}\n\n`;
        
        if (result.diagram.recommendations?.length) {
          reply += `**Recommendations:**\n` + result.diagram.recommendations.map((r: string) => `• ${r}`).join('\n') + '\n\n';
        }

        // Add agent execution summary
        reply += `**Agent Pipeline:**\n`;
        Object.entries(result.agent_results).forEach(([agent, summary]) => {
          reply += `• ${agent}: ${summary.status} (confidence: ${(summary.confidence * 100).toFixed(0)}%)\n`;
        });

        if (result.consensus_log?.length) {
          const lastConsensus = result.consensus_log[result.consensus_log.length - 1];
          if (lastConsensus.consensus_reached) {
            reply += `\n✅ **Consensus Reached** (score: ${(lastConsensus.consensus_score || 0) * 100}%)`;
          }
        }

        // Build thinking steps for the message
        const thinkingSteps = result.thinking_steps?.map((step: any) => ({
          agent: step.agent,
          agentName: step.agent_name,
          status: step.status,
          timestamp: step.timestamp,
          reasoning: step.reasoning,
          toolCalls: step.tool_calls?.map((tc: any) => ({
            tool: tc.tool,
            args: tc.args,
            result: tc.result,
            durationMs: tc.durationMs,
          })),
          modelUsed: step.model_used,
          modelFallback: step.model_fallback,
          confidence: step.confidence,
          outputPreview: step.output_preview,
        })) || [];

        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            sender: 'assistant',
            text: reply,
            timestamp: new Date().toISOString(),
            thinking: thinkingSteps,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: 'assistant',
            text: `⚠️ Multi-agent orchestration failed: ${result.error || 'Unknown error'}`,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ Multi-agent orchestration error: ${err.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsAiLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50 text-slate-800">
      {/* Top Navigation Bar */}
      <TopBar
        mode={mode}
        onToggleMode={setMode}
        isSimulating={isSimulating}
        onToggleSimulation={handleToggleSimulation}
        onClearCanvas={handleClearCanvas}
        onAutoLayout={handleAutoLayout}
        onExportPng={handleExportPng}
        onExportJson={handleExportJson}
        onImportJson={handleImportJson}
        onLoadPreset={handleLoadPreset}
        backendHealthy={backendHealthy}
      />

      {/* Central Canvas Viewport */}
      <main className="flex-1 relative w-full h-full overflow-hidden">
        <ArchitectureCanvas
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={handleConnect}
          onNodeClick={(node) => setSelectedNodeId(node.id)}
          onPaneClick={() => setSelectedNodeId(null)}
          onDropComponent={handleDropComponent}
        />

        {/* Live Simulation Telemetry Overlay */}
        <MetricsOverlay
          metrics={metrics}
          onFocusNode={(id) => setSelectedNodeId(id)}
        />

        {/* Right Sidebar Component Palette */}
        <ComponentDrawer
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          onAddComponent={handleAddComponent}
        />

        {/* Node Properties Configuration Drawer */}
        <NodeConfigDrawer
          selectedNode={selectedNode}
          onClose={() => setSelectedNodeId(null)}
          onUpdateNode={handleUpdateNode}
          onDeleteNode={handleDeleteNode}
        />

        {/* Bottom Floating AI Assistant */}
        <FloatingAssistant
          mode={mode}
          onToggleMode={setMode}
          onGenerateArchitecture={handleGenerateArchitecture}
          onSendMessage={handleSendChatMessage}
          onOrchestrateAgents={handleOrchestrateAgents}
          onOpenRepoIngestion={() => setIsRepoModalOpen(true)}
          onExportPng={handleExportPng}
          onExportJson={handleExportJson}
          messages={messages}
          setMessages={setMessages}
          isLoading={isAiLoading}
          nodesCount={nodes.length}
          currentAgentThinking={currentAgentThinking}
        />

        {/* Repo & Document Ingestion Modal */}
        <RepoIngestionModal
          isOpen={isRepoModalOpen}
          onClose={() => setIsRepoModalOpen(false)}
          onSubmitRepo={handleIngestRepo}
          onSubmitDoc={handleIngestDoc}
          mode={mode}
          isLoading={isAiLoading}
        />
      </main>
    </div>
  );
}

export default App;
