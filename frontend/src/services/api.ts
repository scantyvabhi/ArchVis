import { ArchitectureNode, ArchitectureEdge, AppMode } from '../types/architecture';

const API_BASE_URL = '/api';

export interface GenerateArchitectureResponse {
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  summary: string;
  recommendations?: string[];
}

export interface ParseRepoResponse {
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  summary: string;
  repo_info: {
    repo_url: string;
    detected_tech: string[];
    primary_language?: string;
  };
}

export interface ChatResponse {
  reply: string;
  suggested_action?: any;
  thinking?: AgentThinkingStep[];
  diagram?: {
    nodes: ArchitectureNode[];
    edges: ArchitectureEdge[];
    viewport: { x: number; y: number; zoom: number };
    metadata: any;
    summary: string;
    recommendations: string[];
    hld_view: any;
    lld_view: any;
    semantic_zoom: any;
    analysis: any;
  };
}

export interface SimulateResponse {
  valid: boolean;
  bottlenecks: Array<{
    node_id: string;
    label: string;
    reason: string;
    suggested_fix: string;
  }>;
  metrics: {
    estimated_max_rps: number;
    estimated_p99_latency_ms: number;
  };
}

// Multi-Agent Types
export interface AgentResultSummary {
  agent: string;
  status: string;
  confidence: number;
  reasoning: string;
  execution_time_ms: number;
  error?: string;
  tool_calls?: Array<{
    tool: string;
    args?: any;
    result: 'success' | 'failed';
    durationMs?: number;
  }>;
  model_used?: string;
  model_fallback?: boolean;
  output_preview?: string;
}

export interface AgentThinkingStep {
  agent: string;
  agent_name: string;
  status: string;
  timestamp: string;
  reasoning?: string;
  tool_calls?: Array<{
    tool: string;
    args?: any;
    result: 'success' | 'failed';
    durationMs?: number;
  }>;
  model_used?: string;
  model_fallback?: boolean;
  confidence?: number;
  output_preview?: string;
}

export interface ConsensusLogEntry {
  round: number;
  agent: string;
  status: string;
  confidence: number;
  reasoning?: string;
  consensus_score?: number;
  consensus_reached?: boolean;
}

export interface AgentOrchestrationRequest {
  prompt: string;
  repo_url?: string;
  canvas_state?: { nodes: ArchitectureNode[]; edges: ArchitectureEdge[] };
  mode: AppMode;
  markdown_spec?: string;
  orchestration_mode?: 'sequential' | 'parallel' | 'consensus';
  session_id?: string;
}

export interface AgentOrchestrationResponse {
  session_id: string;
  status: string;
  diagram?: {
    nodes: ArchitectureNode[];
    edges: ArchitectureEdge[];
    viewport: { x: number; y: number; zoom: number };
    metadata: any;
    summary: string;
    recommendations: string[];
    hld_view: any;
    lld_view: any;
    semantic_zoom: any;
    analysis: any;
  };
  agent_results: Record<string, AgentResultSummary>;
  consensus_log: ConsensusLogEntry[];
  total_execution_time_ms: number;
  error?: string;
  thinking_steps?: AgentThinkingStep[];
}

export interface AvailableModelsResponse {
  available_models: Record<string, boolean>;
  default_preference: string;
  fallback_order: string[];
}

export async function generateArchitecture(
  prompt: string,
  mode: AppMode = 'pro'
): Promise<GenerateArchitectureResponse> {
  const response = await fetch(`${API_BASE_URL}/generate-architecture`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, mode }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

export async function parseRepo(
  repoUrl: string,
  mode: AppMode = 'pro'
): Promise<ParseRepoResponse> {
  const response = await fetch(`${API_BASE_URL}/parse-repo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, mode }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

export async function parseRepoWithPreset(
  repoUrl: string,
  mode: AppMode = 'pro'
): Promise<ParseRepoResponse> {
  const response = await fetch(`${API_BASE_URL}/parse-repo-with-preset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, mode }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

export async function sendChatMessage(
  message: string,
  canvasState: { nodes: ArchitectureNode[]; edges: ArchitectureEdge[] },
  mode: AppMode = 'pro'
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      canvas_state: canvasState,
      mode,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

// Multi-Agent API Functions
export async function orchestrateAgents(
  request: AgentOrchestrationRequest
): Promise<AgentOrchestrationResponse> {
  const response = await fetch(`${API_BASE_URL}/agent/orchestrate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

export async function agentChat(
  message: string,
  canvasState: { nodes: ArchitectureNode[]; edges: ArchitectureEdge[] },
  mode: AppMode = 'pro'
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      canvas_state: canvasState,
      mode,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

export async function getAvailableModels(): Promise<AvailableModelsResponse> {
  const response = await fetch(`${API_BASE_URL}/agent/models`);
  if (!response.ok) {
    return { available_models: {}, default_preference: 'nemotron', fallback_order: [] };
  }
  return response.json();
}

export async function validateDiagram(
  nodes: ArchitectureNode[],
  edges: ArchitectureEdge[],
  mode: AppMode = 'pro'
): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/agent/validate-diagram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nodes, edges, mode }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

export async function validateSimulation(
  nodes: ArchitectureNode[],
  edges: ArchitectureEdge[]
): Promise<SimulateResponse> {
  const response = await fetch(`${API_BASE_URL}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nodes, edges }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

export async function checkBackendHealth(): Promise<{ status: string; gemini_available: boolean }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      return response.json();
    }
    return { status: 'offline', gemini_available: false };
  } catch {
    return { status: 'offline', gemini_available: false };
  }
}
