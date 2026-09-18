import { Node, Edge } from '@xyflow/react';

export type ComponentCategory =
  | 'api'
  | 'gateway'
  | 'service'
  | 'cache'
  | 'database'
  | 'queue'
  | 'storage';

export type NodeStatus = 'healthy' | 'warning' | 'overloaded';

export interface ArchitectureNodeData extends Record<string, unknown> {
  label: string;
  category: ComponentCategory;
  tech: string;
  latency: number; // in milliseconds
  rps: number; // current incoming/processed RPS
  capacity: number; // max RPS supported
  failureRate: number; // baseline failure % (0 - 100)
  replication?: string; // e.g. "Primary-Replica (3x)", "Multi-Region"
  description?: string;
  explanation?: string; // Learner mode: Why this was chosen
  // Dynamic simulation values:
  status?: NodeStatus;
  effectiveLatency?: number;
  effectiveErrorRate?: number;
  utilization?: number; // 0 - 100%
  droppedRps?: number;
}

export type ArchitectureNode = Node<ArchitectureNodeData, 'architectureNode'>;

export interface ArchitectureEdgeData extends Record<string, unknown> {
  protocol?: 'HTTP/REST' | 'gRPC' | 'WebSocket' | 'Kafka Topic' | 'TCP' | 'SQL';
  trafficRps?: number;
  latency?: number;
  label?: string;
}

export type ArchitectureEdge = Edge<ArchitectureEdgeData>;

export interface SimulationMetrics {
  isRunning: boolean;
  totalThroughput: number; // aggregate RPS handled
  averageLatency: number; // ms
  p99Latency: number; // ms
  systemErrorRate: number; // %
  bottlenecksCount: number;
  overloadedNodes: string[];
  warningNodes: string[];
  tickCount: number;
}

export type AppMode = 'learner' | 'pro';

export interface PresetArchitecture {
  id: string;
  name: string;
  description: string;
  mode: AppMode;
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
}

export interface ComponentTemplate {
  id: string;
  label: string;
  category: ComponentCategory;
  tech: string;
  defaultLatency: number;
  defaultCapacity: number;
  defaultFailureRate: number;
  defaultReplication: string;
  description: string;
  iconName: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  suggestedAction?: {
    type: 'highlight_node' | 'load_preset' | 'apply_architecture';
    payload: any;
  };
}
