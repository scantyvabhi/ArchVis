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
