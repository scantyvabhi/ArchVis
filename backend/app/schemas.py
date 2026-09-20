from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class NodePosition(BaseModel):
    x: float
    y: float

class NodeData(BaseModel):
    label: str
    category: Literal['api', 'gateway', 'service', 'cache', 'database', 'queue', 'storage']
    tech: str
    latency: int = Field(default=20, description="Base latency in milliseconds")
    rps: int = Field(default=1000, description="Base traffic load in req/sec")
    capacity: int = Field(default=5000, description="Maximum throughput before bottlenecking")
    failureRate: float = Field(default=0.1, description="Base error/failure percentage (0-100)")
    replication: Optional[str] = Field(default=None, description="Replication / HA setup")
    description: Optional[str] = Field(default=None, description="Component overview")
    explanation: Optional[str] = Field(default=None, description="Educational architectural rationale")
    status: Optional[str] = Field(default="healthy")

class ArchitectureNode(BaseModel):
    id: str
    type: str = "architectureNode"
    position: NodePosition
    data: NodeData

class EdgeData(BaseModel):
    protocol: Optional[str] = "HTTP/REST"
    trafficRps: Optional[int] = None
    latency: Optional[int] = None

class ArchitectureEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = True
    data: Optional[EdgeData] = None

class GenerateArchitectureRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="System design description or prompt")
    mode: Literal['learner', 'pro'] = Field(default='pro', description="learner mode explains why, pro mode gives detailed specs")

class GenerateArchitectureResponse(BaseModel):
    nodes: List[ArchitectureNode]
    edges: List[ArchitectureEdge]
    summary: str
    recommendations: Optional[List[str]] = Field(default_factory=list)

class ParseRepoRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL e.g. https://github.com/fastapi/fastapi")
    mode: Literal['learner', 'pro'] = Field(default='pro')

class RepoInfo(BaseModel):
    repo_url: str
    detected_tech: List[str]
    primary_language: Optional[str] = None

class ParseRepoResponse(BaseModel):
    nodes: List[ArchitectureNode]
    edges: List[ArchitectureEdge]
    summary: str
    repo_info: RepoInfo

class CanvasState(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    canvas_state: CanvasState
    mode: Literal['learner', 'pro'] = Field(default='pro')

class ChatResponse(BaseModel):
    reply: str
    suggested_action: Optional[Dict[str, Any]] = None
    diagram: Optional[Dict[str, Any]] = None

class BottleneckItem(BaseModel):
    node_id: str
    label: str
    reason: str
    suggested_fix: str

class SimulationMetricsEstimate(BaseModel):
    estimated_max_rps: int
    estimated_p99_latency_ms: int

class SimulateResponse(BaseModel):
    valid: bool
    bottlenecks: List[BottleneckItem]
    metrics: SimulationMetricsEstimate


# Multi-Agent System Schemas
class AgentOrchestrationRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="System design prompt or question")
    repo_url: Optional[str] = Field(default=None, description="Optional GitHub repository URL to analyze")
    canvas_state: Optional[CanvasState] = Field(default=None, description="Current canvas state for context")
    mode: Literal['learner', 'pro'] = Field(default='pro')
    markdown_spec: Optional[str] = Field(default=None, description="Optional markdown specification to reconcile")
    orchestration_mode: Literal['sequential', 'parallel', 'consensus'] = Field(default='consensus')
    session_id: Optional[str] = Field(default=None, description="Optional session ID for continuity")

class AgentResultSummary(BaseModel):
    agent: str
    status: str
    confidence: float
    reasoning: str
    execution_time_ms: int
    error: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    model_used: Optional[str] = None
    model_fallback: Optional[bool] = None
    output_preview: Optional[str] = None

class AgentThinkingStep(BaseModel):
    agent: str
    agent_name: str
    status: str
    timestamp: str
    reasoning: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    model_used: Optional[str] = None
    model_fallback: Optional[bool] = None
    confidence: Optional[float] = None
    output_preview: Optional[str] = None

class ConsensusLogEntry(BaseModel):
    round: int
    agent: str
    status: str
    confidence: float
    reasoning: Optional[str] = None
    consensus_score: Optional[float] = None
    consensus_reached: Optional[bool] = None

class AgentOrchestrationResponse(BaseModel):
    session_id: str
    status: str
    diagram: Optional[Dict[str, Any]] = None
    agent_results: Dict[str, AgentResultSummary] = Field(default_factory=dict)
    consensus_log: List[ConsensusLogEntry] = Field(default_factory=list)
    total_execution_time_ms: int
    error: Optional[str] = None
    thinking_steps: Optional[List[AgentThinkingStep]] = None

class DiagramSpecResponse(BaseModel):
    nodes: List[ArchitectureNode]
    edges: List[ArchitectureEdge]
    viewport: Dict[str, float]
    metadata: Dict[str, Any]
    summary: str
    recommendations: List[str]
    hld_view: Dict[str, Any]
    lld_view: Dict[str, Any]
    semantic_zoom: Dict[str, Any]
    analysis: Dict[str, Any]
