import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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
)
from .ai_agent import AIAgent
from .repo_parser import RepoParser

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
