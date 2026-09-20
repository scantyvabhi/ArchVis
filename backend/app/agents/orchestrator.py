import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .base import (
    BaseAgent, AgentRole, AgentContext, AgentResult, AgentStatus,
    MultiModelClient, SandboxManager, create_agent_context
)
from .repo_fetcher import RepoFetcherAgent
from .architecture_analyst import ArchitectureAnalystAgent
from .diagram_builder import DiagramBuilderAgent


class OrchestrationMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONSENSUS = "consensus"


@dataclass
class OrchestrationResult:
    session_id: str
    status: str
    final_diagram: Optional[Dict[str, Any]] = None
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    consensus_log: List[Dict[str, Any]] = field(default_factory=list)
    total_execution_time_ms: int = 0
    error: Optional[str] = None


class AgentOrchestrator:
    def __init__(
        self,
        model_client: MultiModelClient,
        sandbox: SandboxManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.model_client = model_client
        self.sandbox = sandbox
        self.config = config or {}
        
        # Shared tools registry
        self.tools = self._register_tools()
        
        # Initialize agents
        self.agents = {
            AgentRole.REPO_FETCHER: RepoFetcherAgent(model_client, sandbox, self.tools, config),
            AgentRole.ARCHITECTURE_ANALYST: ArchitectureAnalystAgent(model_client, sandbox, self.tools, config),
            AgentRole.DIAGRAM_BUILDER: DiagramBuilderAgent(model_client, sandbox, self.tools, config),
        }
        
        # Execution mode
        self.mode = OrchestrationMode(self.config.get("orchestration_mode", "consensus"))
        self.max_consensus_rounds = self.config.get("max_consensus_rounds", 3)
        self.consensus_threshold = self.config.get("consensus_threshold", 0.8)

    def _register_tools(self) -> Dict[str, callable]:
        """Register all available tools for agents"""
        from .repo_fetcher import (
            fetch_github_repo, parse_repo_structure, extract_tech_stack,
            analyze_readme, detect_architecture_pattern, infer_components
        )
        from .architecture_analyst import (
            analyze_bottlenecks, evaluate_scalability, check_reliability,
            validate_patterns, generate_hld_spec, generate_lld_spec,
            compare_architectures, estimate_costs,
            match_prompt_to_preset, generate_architecture_from_prompt
        )
        from .diagram_builder import (
            generate_hld_diagram, generate_lld_diagram, layout_components,
            apply_semantic_zoom, validate_diagram, export_diagram_spec
        )

        return {
            # Repo Fetcher tools
            "fetch_github_repo": fetch_github_repo,
            "parse_repo_structure": parse_repo_structure,
            "extract_tech_stack": extract_tech_stack,
            "analyze_readme": analyze_readme,
            "detect_architecture_pattern": detect_architecture_pattern,
            "infer_components": infer_components,
            # Architecture Analyst tools
            "analyze_bottlenecks": analyze_bottlenecks,
            "evaluate_scalability": evaluate_scalability,
            "check_reliability": check_reliability,
            "validate_patterns": validate_patterns,
            "generate_hld_spec": generate_hld_spec,
            "generate_lld_spec": generate_lld_spec,
            "compare_architectures": compare_architectures,
            "estimate_costs": estimate_costs,
            "match_prompt_to_preset": match_prompt_to_preset,
            "generate_architecture_from_prompt": generate_architecture_from_prompt,
            # Diagram Builder tools
            "generate_hld_diagram": generate_hld_diagram,
            "generate_lld_diagram": generate_lld_diagram,
            "layout_components": layout_components,
            "apply_semantic_zoom": apply_semantic_zoom,
            "validate_diagram": validate_diagram,
            "export_diagram_spec": export_diagram_spec,
        }

    async def orchestrate(
        self,
        user_prompt: str,
        repo_url: Optional[str] = None,
        canvas_state: Optional[Dict[str, Any]] = None,
        mode: str = "pro",
        markdown_spec: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> OrchestrationResult:
        session_id = session_id or str(uuid.uuid4())
        start_time = datetime.utcnow()

        # Create shared context
        context = create_agent_context(
            session_id=session_id,
            user_prompt=user_prompt,
            repo_url=repo_url,
            canvas_state=canvas_state,
            mode=mode,
            markdown_spec=markdown_spec,
        )

        try:
            if self.mode == OrchestrationMode.SEQUENTIAL:
                result = await self._run_sequential(context)
            elif self.mode == OrchestrationMode.PARALLEL:
                result = await self._run_parallel(context)
            else:  # CONSENSUS
                result = await self._run_consensus(context)

            result.session_id = session_id
            result.total_execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return result

        except Exception as e:
            return OrchestrationResult(
                session_id=session_id,
                status="failed",
                error=str(e),
                total_execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            )

    async def _run_sequential(self, context: AgentContext) -> OrchestrationResult:
        """Run agents in sequence: Fetcher -> Analyst -> Builder"""
        agent_order = [
            AgentRole.REPO_FETCHER,
            AgentRole.ARCHITECTURE_ANALYST,
            AgentRole.DIAGRAM_BUILDER,
        ]

        agent_results = {}
        consensus_log = []

        for role in agent_order:
            agent = self.agents[role]
            result = await agent.execute(context)
            agent_results[role.value] = result
            
            consensus_log.append({
                "round": 0,
                "agent": role.value,
                "status": result.status.value,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
            })

            # Stop on failure
            if result.status == AgentStatus.FAILED:
                break

            # Update context with agent output
            context.agent_outputs[role.value] = result.output

        final_diagram = agent_results.get(AgentRole.DIAGRAM_BUILDER.value, AgentResult(
            agent_role=AgentRole.DIAGRAM_BUILDER, status=AgentStatus.FAILED, output={}, 
            reasoning="", confidence=0, execution_time_ms=0
        )).output

        return OrchestrationResult(
            session_id=context.session_id,
            status="completed" if final_diagram else "failed",
            final_diagram=final_diagram,
            agent_results=agent_results,
            consensus_log=consensus_log,
        )

    async def _run_parallel(self, context: AgentContext) -> OrchestrationResult:
        """Run Fetcher and Analyst in parallel, then Builder"""
        # First, run fetcher (needed for analyst)
        fetcher_result = await self.agents[AgentRole.REPO_FETCHER].execute(context)
        context.agent_outputs[AgentRole.REPO_FETCHER.value] = fetcher_result.output

        # Then run analyst and builder in parallel
        analyst_task = self.agents[AgentRole.ARCHITECTURE_ANALYST].execute(context)
        builder_task = self.agents[AgentRole.DIAGRAM_BUILDER].execute(context)

        analyst_result, builder_result = await asyncio.gather(analyst_task, builder_task, return_exceptions=True)

        agent_results = {
            AgentRole.REPO_FETCHER.value: fetcher_result,
            AgentRole.ARCHITECTURE_ANALYST.value: analyst_result if not isinstance(analyst_result, Exception) else AgentResult(
                agent_role=AgentRole.ARCHITECTURE_ANALYST, status=AgentStatus.FAILED, output={}, reasoning="", confidence=0, execution_time_ms=0, error=str(analyst_result)
            ),
            AgentRole.DIAGRAM_BUILDER.value: builder_result if not isinstance(builder_result, Exception) else AgentResult(
                agent_role=AgentRole.DIAGRAM_BUILDER, status=AgentStatus.FAILED, output={}, reasoning="", confidence=0, execution_time_ms=0, error=str(builder_result)
            ),
        }

        consensus_log = [
            {"round": 0, "agent": r.value, "status": agent_results[r.value].status.value, "confidence": agent_results[r.value].confidence}
            for r in AgentRole
        ]

        return OrchestrationResult(
            session_id=context.session_id,
            status="completed",
            final_diagram=agent_results[AgentRole.DIAGRAM_BUILDER.value].output,
            agent_results=agent_results,
            consensus_log=consensus_log,
        )

    async def _run_consensus(self, context: AgentContext) -> OrchestrationResult:
        """Run agents with iterative consensus building"""
        agent_results = {}
        consensus_log = []

        # Round 0: Run repo fetcher only if repo_url is provided
        has_repo = bool(context.repo_url)
        if has_repo:
            fetcher_result = await self.agents[AgentRole.REPO_FETCHER].execute(context)
            agent_results[AgentRole.REPO_FETCHER.value] = fetcher_result
            context.agent_outputs[AgentRole.REPO_FETCHER.value] = fetcher_result.output
            consensus_log.append(self._log_consensus(0, AgentRole.REPO_FETCHER, fetcher_result))
        else:
            # For prompt-only requests, skip repo fetcher
            agent_results[AgentRole.REPO_FETCHER.value] = AgentResult(
                agent_role=AgentRole.REPO_FETCHER,
                status=AgentStatus.COMPLETED,
                output={},
                reasoning="Skipped: No repository URL provided",
                confidence=1.0,
                execution_time_ms=0,
            )
            consensus_log.append(self._log_consensus(0, AgentRole.REPO_FETCHER, agent_results[AgentRole.REPO_FETCHER.value]))

        # Run analyst and builder with initial context
        for round_num in range(self.max_consensus_rounds):
            # Analyst runs with current context
            analyst_result = await self.agents[AgentRole.ARCHITECTURE_ANALYST].execute(context)
            agent_results[AgentRole.ARCHITECTURE_ANALYST.value] = analyst_result
            context.agent_outputs[AgentRole.ARCHITECTURE_ANALYST.value] = analyst_result.output
            # Also store in shared_memory for diagram_builder
            context.shared_memory["architecture_analysis"] = analyst_result.output
            consensus_log.append(self._log_consensus(round_num + 1, AgentRole.ARCHITECTURE_ANALYST, analyst_result))

            # Builder runs with analyst output
            builder_result = await self.agents[AgentRole.DIAGRAM_BUILDER].execute(context)
            agent_results[AgentRole.DIAGRAM_BUILDER.value] = builder_result
            context.agent_outputs[AgentRole.DIAGRAM_BUILDER.value] = builder_result.output
            consensus_log.append(self._log_consensus(round_num + 1, AgentRole.DIAGRAM_BUILDER, builder_result))

            # Check consensus
            consensus_reached, consensus_score = self._check_consensus(agent_results)
            consensus_log[-1]["consensus_score"] = consensus_score
            consensus_log[-1]["consensus_reached"] = consensus_reached

            if consensus_reached:
                context.consensus_round = round_num + 1
                break

            # If not consensus, feed back discrepancies for next round
            if round_num < self.max_consensus_rounds - 1:
                discrepancies = self._identify_discrepancies(agent_results)
                context.shared_memory["consensus_discrepancies"] = discrepancies
                context.consensus_round = round_num + 1

        final_diagram = agent_results.get(AgentRole.DIAGRAM_BUILDER.value, AgentResult(
            agent_role=AgentRole.DIAGRAM_BUILDER, status=AgentStatus.FAILED, output={}, reasoning="", confidence=0, execution_time_ms=0
        )).output

        return OrchestrationResult(
            session_id=context.session_id,
            status="completed" if final_diagram else "failed",
            final_diagram=final_diagram,
            agent_results=agent_results,
            consensus_log=consensus_log,
        )

    def _log_consensus(self, round_num: int, role: AgentRole, result: AgentResult) -> Dict[str, Any]:
        return {
            "round": round_num,
            "agent": role.value,
            "status": result.status.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning[:200] + "..." if len(result.reasoning) > 200 else result.reasoning,
        }

    def _check_consensus(self, agent_results: Dict[str, AgentResult]) -> tuple[bool, float]:
        """Check if agents have reached consensus"""
        # Only consider agents that completed successfully
        completed_results = [r for r in agent_results.values() if r.status == AgentStatus.COMPLETED]
        
        if not completed_results:
            return False, 0.0

        confidences = [r.confidence for r in completed_results]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        
        # Consensus requires high average confidence and no agent with very low confidence
        consensus = avg_confidence >= self.consensus_threshold and min_confidence >= 0.6
        
        return consensus, avg_confidence

    def _identify_discrepancies(self, agent_results: Dict[str, AgentResult]) -> List[Dict[str, Any]]:
        """Identify discrepancies between agent outputs for feedback"""
        discrepancies = []

        analyst_output = agent_results.get(AgentRole.ARCHITECTURE_ANALYST.value, AgentResult(
            agent_role=AgentRole.ARCHITECTURE_ANALYST, status=AgentStatus.FAILED, output={}, reasoning="", confidence=0, execution_time_ms=0
        )).output

        builder_output = agent_results.get(AgentRole.DIAGRAM_BUILDER.value, AgentResult(
            agent_role=AgentRole.DIAGRAM_BUILDER, status=AgentStatus.FAILED, output={}, reasoning="", confidence=0, execution_time_ms=0
        )).output

        # Check component count match
        analyst_components = analyst_output.get("validated_architecture", {}).get("components", [])
        builder_nodes = builder_output.get("nodes", [])

        if len(analyst_components) != len(builder_nodes):
            discrepancies.append({
                "type": "component_count_mismatch",
                "analyst_count": len(analyst_components),
                "builder_count": len(builder_nodes),
                "message": f"Analyst identified {len(analyst_components)} components but builder created {len(builder_nodes)} nodes"
            })

        # Check for missing bottleneck mitigations in diagram
        bottlenecks = analyst_output.get("bottlenecks", [])
        if bottlenecks:
            builder_components = {n.get("data", {}).get("label") for n in builder_nodes}
            for bn in bottlenecks:
                if bn.get("component") not in builder_components:
                    discrepancies.append({
                        "type": "bottleneck_not_addressed",
                        "component": bn.get("component"),
                        "message": f"Bottleneck in '{bn.get('component')}' not reflected in diagram"
                    })

        return discrepancies


async def create_orchestrator(config: Dict[str, Any]) -> AgentOrchestrator:
    """Factory function to create orchestrator with all dependencies"""
    model_client = MultiModelClient(config)
    sandbox = SandboxManager(
        max_execution_time=config.get("sandbox_timeout", 30),
        max_memory_mb=config.get("sandbox_memory_mb", 512),
    )
    
    orchestrator = AgentOrchestrator(model_client, sandbox, config)
    return orchestrator