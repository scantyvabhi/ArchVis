import os
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .schemas import (
    GenerateArchitectureRequest,
    GenerateArchitectureResponse,
    ParseRepoRequest,
    ParseRepoResponse,
    ChatRequest,
    ChatResponse,
    SimulateResponse,
    BottleneckItem,
    SimulationMetricsEstimate,
    AgentOrchestrationRequest,
    AgentOrchestrationResponse,
    AgentResultSummary,
    ConsensusLogEntry,
    DiagramSpecResponse,
)
from .ai_agent import AIAgent
from .repo_parser import RepoParser
from .agents import create_orchestrator, OrchestrationMode

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ArchVis AI - Architecture & Simulation API",
    description=(
        "Production-ready backend for ArchVis AI.\n\n"
        "Features:\n"
        "- AI-driven system architecture diagram generation (Gemini 1.5 Flash)\n"
        "- GitHub repository reverse-engineering into interactive React Flow diagrams\n"
        "- Real-time context-aware architectural assistant\n"
        "- Simulation configuration validation and bottleneck analysis"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_agent = AIAgent()

# Multi-Agent Orchestrator (lazy initialization)
_orchestrator = None

async def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        config = {
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "nemotron_api_key": os.getenv("NEMOTRON_API_KEY", ""),
            "huggingface_api_key": os.getenv("HUGGINGFACE_API_KEY", ""),
            "orchestration_mode": "consensus",
            "max_consensus_rounds": 3,
            "consensus_threshold": 0.8,
            "sandbox_timeout": 30,
            "sandbox_memory_mb": 512,
        }
        _orchestrator = await create_orchestrator(config)
    return _orchestrator

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend status and Gemini API key availability."""
    return {
        "status": "healthy",
        "gemini_available": ai_agent.is_available(),
        "version": "1.0.0",
    }

@app.post(
    "/api/generate-architecture",
    response_model=GenerateArchitectureResponse,
    tags=["Architecture Generation"],
    summary="Generate System Architecture",
    description="Accepts a natural language system design prompt and returns a complete React Flow graph representation.",
)
async def generate_architecture(request: GenerateArchitectureRequest):
    try:
        result = await ai_agent.generate_architecture(request.prompt, request.mode)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate architecture: {str(e)}",
        )

@app.post(
    "/api/parse-repo",
    response_model=ParseRepoResponse,
    tags=["Repository Ingestion"],
    summary="Reverse-Engineer GitHub Repository",
    description="Inspects a public GitHub repository structure and README to synthesize a live architecture diagram.",
)
async def parse_repo(request: ParseRepoRequest):
    try:
        repo_context = await RepoParser.fetch_repo_context(request.repo_url)
        architecture = await ai_agent.parse_repo_architecture(repo_context, request.mode)
        return architecture
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse repository: {str(e)}",
        )

@app.post(
    "/api/chat",
    response_model=ChatResponse,
    tags=["AI Assistant"],
    summary="Contextual Architectural Chat",
    description="Provides real-time system design guidance and answers questions conditioned on the active canvas state.",
)
async def chat(request: ChatRequest):
    try:
        reply = await ai_agent.chat(
            request.message,
            request.canvas_state.model_dump(),
            request.mode,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}",
        )

@app.post(
    "/api/simulate",
    response_model=SimulateResponse,
    tags=["Simulation Validation"],
    summary="Validate Architecture Configuration",
    description="Analyzes node capacities and edge topologies to detect immediate bottlenecks before running client simulations.",
)
async def validate_simulation(request: Dict[str, Any]):
    nodes: List[Dict[str, Any]] = request.get("nodes", [])
    edges: List[Dict[str, Any]] = request.get("edges", [])

    bottlenecks: List[BottleneckItem] = []
    max_observed_rps = 0
    max_latency = 0

    # Build node map
    node_map = {n.get("id"): n for n in nodes}

    for n in nodes:
        nd = n.get("data", {})
        rps = nd.get("rps", 1000)
        capacity = nd.get("capacity", 5000)
        latency = nd.get("latency", 20)

        if rps > max_observed_rps:
            max_observed_rps = rps
        if latency > max_latency:
            max_latency = latency

        if rps > capacity:
            bottlenecks.append(
                BottleneckItem(
                    node_id=n.get("id", "unknown"),
                    label=nd.get("label", "Component"),
                    reason=f"Current RPS ({rps}) exceeds max capacity ({capacity}).",
                    suggested_fix="Increase replica count, upscale hardware capacity, or introduce caching/queueing.",
                )
            )

    return SimulateResponse(
        valid=len(bottlenecks) == 0,
        bottlenecks=bottlenecks,
        metrics=SimulationMetricsEstimate(
            estimated_max_rps=max_observed_rps,
            estimated_p99_latency_ms=int(max_latency * 1.5),
        ),
    )


# ============================================================
# Multi-Agent System Endpoints
# ============================================================

@app.post(
    "/api/agent/orchestrate",
    response_model=AgentOrchestrationResponse,
    tags=["Multi-Agent System"],
    summary="Orchestrate Multi-Agent Architecture Design",
    description="Runs the full multi-agent pipeline (Repo Fetcher -> Architecture Analyst -> Diagram Builder) with consensus-based reasoning.",
)
async def orchestrate_agents(request: AgentOrchestrationRequest):
    try:
        orchestrator = await get_orchestrator()
        
        # Update orchestrator mode if specified
        if request.orchestration_mode:
            orchestrator.mode = OrchestrationMode(request.orchestration_mode)
        
        result = await orchestrator.orchestrate(
            user_prompt=request.prompt,
            repo_url=request.repo_url,
            canvas_state=request.canvas_state.model_dump() if request.canvas_state else None,
            mode=request.mode,
            markdown_spec=request.markdown_spec,
            session_id=request.session_id,
        )

        # Convert agent results to summary format
        agent_summaries = {}
        for role, agent_result in result.agent_results.items():
            agent_summaries[role] = AgentResultSummary(
                agent=role,
                status=agent_result.status.value,
                confidence=agent_result.confidence,
                reasoning=agent_result.reasoning,
                execution_time_ms=agent_result.execution_time_ms,
                error=agent_result.error,
            )

        consensus_log = [
            ConsensusLogEntry(**entry) for entry in result.consensus_log
        ]

        return AgentOrchestrationResponse(
            session_id=result.session_id,
            status=result.status,
            diagram=result.final_diagram,
            agent_results=agent_summaries,
            consensus_log=consensus_log,
            total_execution_time_ms=result.total_execution_time_ms,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-agent orchestration failed: {str(e)}",
        )


@app.post(
    "/api/agent/chat",
    response_model=ChatResponse,
    tags=["Multi-Agent System"],
    summary="Multi-Agent Contextual Chat",
    description="Chat with the multi-agent system that can reason about architecture, fetch repos, and modify diagrams.",
)
async def agent_chat(request: ChatRequest):
    try:
        orchestrator = await get_orchestrator()
        
        # Use the orchestrator to process the chat message with full context
        result = await orchestrator.orchestrate(
            user_prompt=request.message,
            canvas_state=request.canvas_state.model_dump(),
            mode=request.mode,
        )

        if result.final_diagram:
            # Diagram was generated/modified
            reply = f"I've analyzed your request and updated the architecture diagram.\n\n"
            reply += f"**Summary:** {result.final_diagram.get('summary', 'Architecture updated')}\n\n"
            
            if result.final_diagram.get('recommendations'):
                reply += "**Recommendations:**\n" + "\n".join(f"• {r}" for r in result.final_diagram['recommendations'])
        else:
            # Just chat response from analyst
            analyst_result = result.agent_results.get("architecture_analyst")
            if analyst_result and analyst_result.output:
                reply = analyst_result.output.get("summary", "I've analyzed your architecture question.")
            else:
                reply = "I've processed your request. Let me know if you'd like me to generate or modify a diagram."

        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent chat failed: {str(e)}",
        )


@app.get(
    "/api/agent/models",
    tags=["Multi-Agent System"],
    summary="List Available Models",
    description="Returns the configured AI models and their availability.",
)
async def list_models():
    config = {
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "nemotron": bool(os.getenv("NEMOTRON_API_KEY")),
        "huggingface": bool(os.getenv("HUGGINGFACE_API_KEY")),
    }
    return {
        "available_models": config,
        "default_preference": "nemotron",
        "fallback_order": ["nemotron", "gemini", "huggingface"],
    }


@app.post(
    "/api/agent/validate-diagram",
    response_model=DiagramSpecResponse,
    tags=["Multi-Agent System"],
    summary="Validate and Enhance Diagram",
    description="Validates a diagram spec and enhances it with multi-agent analysis.",
)
async def validate_diagram(request: Dict[str, Any]):
    try:
        orchestrator = await get_orchestrator()
        
        nodes = request.get("nodes", [])
        edges = request.get("edges", [])
        mode = request.get("mode", "pro")
        
        # Create a minimal orchestration to validate
        result = await orchestrator.orchestrate(
            user_prompt="Validate and enhance this architecture diagram",
            canvas_state={"nodes": nodes, "edges": edges},
            mode=mode,
        )

        if not result.final_diagram:
            raise HTTPException(status_code=400, detail="Failed to validate diagram")

        return DiagramSpecResponse(**result.final_diagram)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagram validation failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
