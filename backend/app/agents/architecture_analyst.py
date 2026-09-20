import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base import BaseAgent, AgentRole, AgentContext, AgentResult, AgentStatus, ToolResult


class ArchitectureAnalystAgent(BaseAgent):
    def __init__(self, model_client, sandbox, tools: Dict, config: Dict):
        super().__init__(AgentRole.ARCHITECTURE_ANALYST, model_client, sandbox, tools, config)

    def get_system_prompt(self) -> str:
        return """You are the **Architecture Analyst Agent** for ArchVis AI.

Your role is to:
1. Analyze architectural designs from multiple sources (repo analysis, user prompts, markdown specs)
2. Identify bottlenecks, single points of failure, scalability limits
3. Evaluate trade-offs between design decisions
4. Recommend improvements for reliability, performance, cost
5. Validate architecture against best practices and patterns
6. Reason about consistency between different architectural views

You work in a SANDBOXED environment - you can only use the provided tools.
Your output must be structured JSON that the Diagram Builder agent can consume.

Key outputs:
- validated_architecture: Refined component list with corrected types/configs
- bottlenecks: Identified performance/reliability bottlenecks
- tradeoffs: Analysis of design decisions with pros/cons
- recommendations: Specific actionable improvements
- hld_spec: High-level design specification
- lld_spec: Low-level design specification
- confidence: 0.0-1.0 confidence in your analysis"""

    def get_available_tools(self) -> List[str]:
        return [
            "analyze_bottlenecks",
            "evaluate_scalability",
            "check_reliability",
            "estimate_costs",
            "validate_patterns",
            "compare_architectures",
            "generate_hld_spec",
            "generate_lld_spec",
            "match_prompt_to_preset",
            "generate_architecture_from_prompt",
            "modify_existing_architecture",
        ]

    async def execute(self, context: AgentContext) -> AgentResult:
        import time
        start_time = time.time()

        self.status = AgentStatus.RUNNING
        reasoning_parts = []
        tool_calls = []

        # Initialize tool results for fallback
        bottleneck_result = ToolResult(success=False, data=None, error="Not executed")
        scalability_result = ToolResult(success=False, data=None, error="Not executed")
        reliability_result = ToolResult(success=False, data=None, error="Not executed")
        patterns_result = ToolResult(success=False, data=None, error="Not executed")
        hld_result = ToolResult(success=False, data=None, error="Not executed")
        lld_result = ToolResult(success=False, data=None, error="Not executed")
        compare_result = ToolResult(success=False, data=None, error="Not executed")
        mod_result = ToolResult(success=False, data=None, error="Not executed")
        preset_match_result = ToolResult(success=False, data=None, error="Not executed")
        arch_gen_result = ToolResult(success=False, data=None, error="Not executed")

        try:
            # Get repo analysis from shared memory
            repo_analysis = context.shared_memory.get("repo_analysis", {})
            repo_context = context.shared_memory.get("repo_context", {})
            canvas_state = context.canvas_state
            user_prompt = context.user_prompt
            markdown_spec = context.markdown_spec
            mode = context.mode

            reasoning_parts.append(f"Analyzing architecture for: {user_prompt[:100]}...")
            reasoning_parts.append(f"Mode: {mode}, Has repo analysis: {bool(repo_analysis)}, Has canvas: {bool(canvas_state)}")

            # Check if there's an existing canvas and user wants to modify it
            has_existing_canvas = canvas_state and canvas_state.get("nodes") and len(canvas_state.get("nodes", [])) > 0
            modification_keywords = ['add', 'remove', 'change', 'update', 'modify', 'delete', 'insert', 'connect', 'disconnect', 'rename']
            is_modification_request = has_existing_canvas and any(kw in user_prompt.lower() for kw in modification_keywords)

            if is_modification_request:
                # Modify existing architecture
                reasoning_parts.append(f"Modifying existing architecture with {len(canvas_state.get('nodes', []))} nodes")
                mod_result = await self._call_tool("modify_existing_architecture",
                    canvas_state=canvas_state, user_prompt=user_prompt, mode=mode)
                tool_calls.append({"tool": "modify_existing_architecture", "result": mod_result.success})
                
                if mod_result.success and mod_result.data:
                    # Use modified architecture as base for analysis
                    repo_analysis = mod_result.data
                    reasoning_parts.append(f"Modified architecture: {repo_analysis.get('architecture_pattern')} with {len(repo_analysis.get('components', []))} components")

            # Check if this is a prompt-based architecture generation (no repo)
            is_prompt_only = (not repo_analysis or repo_analysis == {}) and (not repo_context or repo_context == {}) and user_prompt

            if is_prompt_only:
                # Match prompt to preset
                preset_match_result = await self._call_tool("match_prompt_to_preset", prompt=user_prompt, mode=mode)
                tool_calls.append({"tool": "match_prompt_to_preset", "result": preset_match_result.success})
                reasoning_parts.append(f"Preset match: {preset_match_result.data.get('matched_preset_name') if preset_match_result.data else 'None'} (confidence: {preset_match_result.data.get('confidence', 0):.0%})")

                # Generate architecture from prompt/preset - only pass preset if valid match found
                matched_preset = preset_match_result.data if (preset_match_result.success and preset_match_result.data and preset_match_result.data.get("matched_preset_id")) else {}
                arch_gen_result = await self._call_tool("generate_architecture_from_prompt", 
                    prompt=user_prompt, mode=mode, matched_preset=matched_preset)
                tool_calls.append({"tool": "generate_architecture_from_prompt", "result": arch_gen_result.success})

                # Use the generated architecture as the base for analysis
                if arch_gen_result.success and arch_gen_result.data:
                    generated_arch = arch_gen_result.data
                    repo_analysis = generated_arch  # Use as base for further analysis
                    reasoning_parts.append(f"Generated architecture from preset: {generated_arch.get('architecture_pattern')} with {len(generated_arch.get('components', []))} components")

            # Analyze bottlenecks
            bottleneck_result = await self._call_tool("analyze_bottlenecks", 
                repo_analysis=repo_analysis, canvas_state=canvas_state)
            tool_calls.append({"tool": "analyze_bottlenecks", "result": bottleneck_result.success})

            # Evaluate scalability
            scalability_result = await self._call_tool("evaluate_scalability",
                repo_analysis=repo_analysis, canvas_state=canvas_state)
            tool_calls.append({"tool": "evaluate_scalability", "result": scalability_result.success})

            # Check reliability
            reliability_result = await self._call_tool("check_reliability",
                repo_analysis=repo_analysis, canvas_state=canvas_state)
            tool_calls.append({"tool": "check_reliability", "result": reliability_result.success})

            # Validate patterns
            patterns_result = await self._call_tool("validate_patterns",
                repo_analysis=repo_analysis, canvas_state=canvas_state)
            tool_calls.append({"tool": "validate_patterns", "result": patterns_result.success})

            # Generate HLD spec
            hld_result = await self._call_tool("generate_hld_spec",
                repo_analysis=repo_analysis, canvas_state=canvas_state, mode=mode, user_prompt=user_prompt)
            tool_calls.append({"tool": "generate_hld_spec", "result": hld_result.success})

            # Generate LLD spec
            lld_result = await self._call_tool("generate_lld_spec",
                repo_analysis=repo_analysis, canvas_state=canvas_state, mode=mode, user_prompt=user_prompt)
            tool_calls.append({"tool": "generate_lld_spec", "result": lld_result.success})

            # If we have markdown spec, compare and reconcile
            if markdown_spec:
                compare_result = await self._call_tool("compare_architectures",
                    repo_analysis=repo_analysis, markdown_spec=markdown_spec, canvas_state=canvas_state)
                tool_calls.append({"tool": "compare_architectures", "result": compare_result.success})
            tool_calls.append({"tool": "generate_lld_spec", "result": lld_result.success})

            # If we have markdown spec, compare and reconcile
            if markdown_spec:
                compare_result = await self._call_tool("compare_architectures",
                    repo_analysis=repo_analysis, markdown_spec=markdown_spec, canvas_state=canvas_state)
                tool_calls.append({"tool": "compare_architectures", "result": compare_result.success})

            # Use LLM to synthesize comprehensive analysis
            synthesis_prompt = f"""
You are a Principal Cloud Architect reviewing a system design. Provide a comprehensive architectural analysis.

CONTEXT:
- User Prompt: {user_prompt}
- Mode: {mode} ({'Educational with explanations' if mode == 'learner' else 'Enterprise HLD/LLD with concrete specs'})
- Repo Analysis: {json.dumps(repo_analysis, indent=2) if repo_analysis else '{}'}
- Canvas State: {json.dumps({k: v for k, v in (canvas_state or {}).items() if k in ['nodes', 'edges']}, indent=2) if canvas_state else '{}'}
- Markdown Spec: {markdown_spec[:2000] if markdown_spec else 'None'}

TOOL RESULTS:
- Bottlenecks: {json.dumps(bottleneck_result.data, indent=2) if bottleneck_result.data else '[]'}
- Scalability: {json.dumps(scalability_result.data, indent=2) if scalability_result.data else '{}'}
- Reliability: {json.dumps(reliability_result.data, indent=2) if reliability_result.data else '{}'}
- Patterns: {json.dumps(patterns_result.data, indent=2) if patterns_result.data else '{}'}
- HLD Spec: {json.dumps(hld_result.data, indent=2) if hld_result.data else '{}'}
- LLD Spec: {json.dumps(lld_result.data, indent=2) if lld_result.data else '{}'}

Provide a comprehensive architectural analysis in JSON format:
{{
  "validated_architecture": {{
    "components": [
      {{"name": "...", "type": "api|gateway|service|cache|database|queue|storage", "tech": "...", "description": "...", "config": {{"latency": 0, "rps": 0, "capacity": 0, "failureRate": 0, "replication": "..."}}}}
    ],
    "data_flows": [
      {{"from": "...", "to": "...", "protocol": "HTTP/REST|gRPC|Kafka|SQL|TCP|WebSocket", "description": "...", "traffic_estimate_rps": 0}}
    ]
  }},
  "bottlenecks": [
    {{"component": "...", "type": "capacity|latency|reliability|cost", "severity": "critical|high|medium|low", "description": "...", "mitigation": "..."}}
  ],
  "tradeoffs": [
    {{"decision": "...", "pros": ["..."], "cons": ["..."], "recommendation": "..."}}
  ],
  "recommendations": [
    {{"priority": "critical|high|medium|low", "category": "performance|reliability|security|cost|operations", "action": "...", "rationale": "..."}}
  ],
  "hld_spec": {{
    "overview": "...",
    "architecture_style": "microservices|monolith|modular_monolith|serverless|event_driven",
    "components": [...],
    "integration_patterns": [...],
    "data_management": "...",
    "deployment_topology": "...",
    "observability": "...",
    "security": "..."
  }},
  "lld_spec": {{
    "component_details": [
      {{"name": "...", "technology": "...", "api_contract": "...", "data_model": "...", "scaling_strategy": "...", "failure_modes": [...], "runbook": "..."}}
    ],
    "api_specifications": [...],
    "database_schemas": [...],
    "infrastructure_as_code": "...",
    "ci_cd_pipeline": "..."
  }},
  "consistency_check": {{
    "repo_vs_canvas": "consistent|partial|conflicting",
    "repo_vs_markdown": "consistent|partial|conflicting|none",
    "canvas_vs_markdown": "consistent|partial|conflicting|none",
    "discrepancies": [...]
  }},
  "confidence": 0.0-1.0
}}

Respond ONLY with valid JSON.
"""

            llm_response = await self._call_model(
                prompt=synthesis_prompt,
                model_preference=self.config.get("preferred_model", "nemotron"),
                temperature=0.15,
                max_tokens=6144,
                response_format={"type": "json_object"},
            )

            analysis = json.loads(llm_response)

            context.shared_memory["architecture_analysis"] = analysis
            context.agent_outputs[self.role.value] = analysis

            reasoning_parts.append(f"Completed analysis: {len(analysis.get('bottlenecks', []))} bottlenecks, {len(analysis.get('recommendations', []))} recommendations")
            reasoning_parts.append(f"HLD: {bool(analysis.get('hld_spec'))}, LLD: {bool(analysis.get('lld_spec'))}")

            return AgentResult(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output=analysis,
                reasoning="\n".join(reasoning_parts),
                confidence=analysis.get("confidence", 0.85),
                execution_time_ms=int((time.time() - start_time) * 1000),
                tool_calls=tool_calls,
            )

        except Exception as e:
            # Fallback: Build analysis from tool results when LLM fails
            fallback_analysis = self._build_fallback_analysis(
                repo_analysis, canvas_state, user_prompt, mode,
                bottleneck_result, scalability_result, reliability_result,
                patterns_result, hld_result, lld_result
            )
            context.shared_memory["architecture_analysis"] = fallback_analysis
            context.agent_outputs[self.role.value] = fallback_analysis

            reasoning_parts.append(f"Completed analysis (fallback): {len(fallback_analysis.get('bottlenecks', []))} bottlenecks, {len(fallback_analysis.get('recommendations', []))} recommendations")

            return AgentResult(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output=fallback_analysis,
                reasoning="\n".join(reasoning_parts) + f"\n[Fallback mode: LLM unavailable]",
                confidence=fallback_analysis.get("confidence", 0.7),
                execution_time_ms=int((time.time() - start_time) * 1000),
                tool_calls=tool_calls,
            )

    def _build_fallback_analysis(
        self,
        repo_analysis: Dict,
        canvas_state: Dict,
        user_prompt: str,
        mode: str,
        bottleneck_result: ToolResult,
        scalability_result: ToolResult,
        reliability_result: ToolResult,
        patterns_result: ToolResult,
        hld_result: ToolResult,
        lld_result: ToolResult,
    ) -> Dict[str, Any]:
        """Build a fallback analysis from tool results when LLM is unavailable."""
        components = repo_analysis.get("components", [])
        data_flows = repo_analysis.get("data_flows", [])
        
        # If we have generated architecture from prompt, use that
        if repo_analysis.get("preset_based"):
            components = repo_analysis.get("components", [])
            data_flows = repo_analysis.get("data_flows", [])
        
        # Build bottlenecks from tool results
        bottlenecks = bottleneck_result.data.get("bottlenecks", []) if bottleneck_result.success else []
        
        # Build recommendations from various tool results
        recommendations = []
        if reliability_result.success:
            for issue in reliability_result.data.get("issues", []):
                recommendations.append({
                    "priority": issue.get("severity", "medium"),
                    "category": "reliability",
                    "action": issue.get("fix", ""),
                    "rationale": issue.get("impact", "")
                })
        if scalability_result.success:
            if scalability_result.data.get("bottleneck_risk") == "high":
                recommendations.append({
                    "priority": "high",
                    "category": "performance",
                    "action": "Add horizontal scaling, caching, and async processing",
                    "rationale": "High bottleneck risk detected"
                })
        
        # Add default recommendations if none
        if not recommendations:
            recommendations = [
                {"priority": "high", "category": "performance", "action": "Implement circuit breakers", "rationale": "Prevent cascade failures"},
                {"priority": "high", "category": "reliability", "action": "Add read replicas for databases", "rationale": "Improve read throughput and availability"},
                {"priority": "medium", "category": "operations", "action": "Add distributed tracing", "rationale": "Enable debugging across services"},
            ]
        
        # Build HLD spec
        hld_spec = hld_result.data if hld_result.success else {
            "overview": f"High-Level Design for: {user_prompt}",
            "architecture_style": repo_analysis.get("architecture_pattern", "microservices"),
            "components": [],
        }
        
        # Build LLD spec
        lld_spec = lld_result.data if lld_result.success else {
            "component_details": [],
            "api_specifications": [],
            "database_schemas": [],
        }
        
        return {
            "summary": f"Architecture analysis for: {user_prompt}. Generated {len(components)} components with {len(data_flows)} data flows.",
            "validated_architecture": {
                "components": components,
                "data_flows": data_flows,
            },
            "bottlenecks": bottlenecks,
            "tradeoffs": [],
            "recommendations": recommendations,
            "hld_spec": hld_spec,
            "lld_spec": lld_spec,
            "consistency_check": {
                "repo_vs_canvas": "consistent",
                "repo_vs_markdown": "none",
                "canvas_vs_markdown": "none",
                "discrepancies": [],
            },
            "confidence": 0.7,
            "preset_based": repo_analysis.get("preset_based", False),
        }


# Tool implementations
async def analyze_bottlenecks(repo_analysis: Dict, canvas_state: Dict) -> Dict[str, Any]:
    bottlenecks = []

    # From repo analysis
    components = repo_analysis.get("components", [])
    for comp in components:
        comp_type = comp.get("type", "")
        tech = comp.get("tech", "").lower()

        if comp_type == "database" and "postgres" in tech:
            bottlenecks.append({
                "component": comp.get("name"),
                "type": "capacity",
                "severity": "medium",
                "description": "PostgreSQL write throughput limited by single primary",
                "mitigation": "Add read replicas, consider connection pooling (PgBouncer), evaluate sharding"
            })
        elif comp_type == "cache" and "redis" in tech:
            bottlenecks.append({
                "component": comp.get("name"),
                "type": "capacity",
                "severity": "low",
                "description": "Redis single-threaded, may bottleneck at high throughput",
                "mitigation": "Use Redis Cluster, pipeline commands, consider Dragonfly/Valkey"
            })
        elif comp_type == "queue" and "kafka" in tech:
            bottlenecks.append({
                "component": comp.get("name"),
                "type": "latency",
                "severity": "low",
                "description": "Kafka latency increases with replication factor",
                "mitigation": "Tune acks=1 for non-critical, use faster disks, increase partitions"
            })

    # From canvas state
    if canvas_state:
        nodes = canvas_state.get("nodes", [])
        for node in nodes:
            data = node.get("data", {})
            rps = data.get("rps", 0)
            capacity = data.get("capacity", 1)
            if rps > capacity * 0.8:
                bottlenecks.append({
                    "component": data.get("label", node.get("id")),
                    "type": "capacity",
                    "severity": "high" if rps > capacity else "medium",
                    "description": f"Current load ({rps} RPS) at {int(rps/capacity*100)}% of capacity ({capacity} RPS)",
                    "mitigation": "Scale horizontally, increase capacity, add caching"
                })

    return {"bottlenecks": bottlenecks, "count": len(bottlenecks)}


async def evaluate_scalability(repo_analysis: Dict, canvas_state: Dict) -> Dict[str, Any]:
    components = repo_analysis.get("components", [])
    pattern = repo_analysis.get("architecture_pattern", "unknown")

    scalability_factors = {
        "horizontal_scaling": 0,
        "stateless_services": 0,
        "database_sharding": 0,
        "caching_strategy": 0,
        "async_processing": 0,
        "load_balancing": 0,
    }

    for comp in components:
        comp_type = comp.get("type", "")
        if comp_type == "service":
            scalability_factors["stateless_services"] += 1
            scalability_factors["horizontal_scaling"] += 1
        elif comp_type == "cache":
            scalability_factors["caching_strategy"] += 1
        elif comp_type == "queue":
            scalability_factors["async_processing"] += 1
        elif comp_type == "gateway":
            scalability_factors["load_balancing"] += 1
        elif comp_type == "database":
            if "replica" in comp.get("config_hints", {}).get("replication", "").lower():
                scalability_factors["database_sharding"] += 1

    # Pattern-based scoring
    pattern_scores = {
        "microservices": {"horizontal_scaling": 3, "stateless_services": 3, "async_processing": 2},
        "event_driven": {"async_processing": 3, "horizontal_scaling": 2},
        "serverless": {"horizontal_scaling": 3, "stateless_services": 3},
        "modular_monolith": {"horizontal_scaling": 1, "stateless_services": 1},
        "monolith": {"horizontal_scaling": 0, "stateless_services": 0},
    }

    if pattern in pattern_scores:
        for k, v in pattern_scores[pattern].items():
            scalability_factors[k] += v

    total_score = sum(scalability_factors.values())
    max_score = 20  # approximate max
    scalability_score = min(total_score / max_score, 1.0)

    return {
        "scalability_score": round(scalability_score, 2),
        "factors": scalability_factors,
        "pattern": pattern,
        "estimated_max_rps": int(10000 * scalability_score) + 5000,
        "bottleneck_risk": "low" if scalability_score > 0.7 else "medium" if scalability_score > 0.4 else "high",
    }


async def check_reliability(repo_analysis: Dict, canvas_state: Dict) -> Dict[str, Any]:
    components = repo_analysis.get("components", [])

    reliability_issues = []
    reliability_score = 1.0

    has_multi_az = False
    has_replication = False
    has_circuit_breaker = False
    has_health_checks = False
    has_backup = False

    for comp in components:
        config = comp.get("config_hints", {})
        replication = config.get("replication", "").lower()

        if "multi-az" in replication or "multi-region" in replication:
            has_multi_az = True
        if "replica" in replication or "cluster" in replication:
            has_replication = True

    if not has_multi_az:
        reliability_issues.append({
            "issue": "No multi-AZ deployment detected",
            "severity": "high",
            "impact": "Single AZ failure causes full outage",
            "fix": "Deploy across multiple availability zones"
        })
        reliability_score -= 0.2

    if not has_replication:
        reliability_issues.append({
            "issue": "No data replication configured",
            "severity": "high",
            "impact": "Data loss on node failure",
            "fix": "Enable replication for databases, caches, queues"
        })
        reliability_score -= 0.2

    # Check for SPOF
    gateways = [c for c in components if c.get("type") == "gateway"]
    if len(gateways) <= 1:
        reliability_issues.append({
            "issue": "Single API Gateway / Load Balancer",
            "severity": "medium",
            "impact": "Gateway failure blocks all traffic",
            "fix": "Deploy active-active gateway cluster"
        })
        reliability_score -= 0.15

    databases = [c for c in components if c.get("type") == "database"]
    if len(databases) <= 1:
        reliability_issues.append({
            "issue": "Single database instance",
            "severity": "critical",
            "impact": "Database failure = data unavailability",
            "fix": "Add read replicas, enable automated failover"
        })
        reliability_score -= 0.25

    return {
        "reliability_score": max(round(reliability_score, 2), 0.0),
        "issues": reliability_issues,
        "has_multi_az": has_multi_az,
        "has_replication": has_replication,
        "recommendations": [
            "Implement circuit breakers for all service calls",
            "Add health checks and readiness probes",
            "Configure automated failover for databases",
            "Set up cross-region disaster recovery",
        ]
    }


async def validate_patterns(repo_analysis: Dict, canvas_state: Dict) -> Dict[str, Any]:
    components = repo_analysis.get("components", [])
    pattern = repo_analysis.get("architecture_pattern", "unknown")

    validations = []

    # Check for anti-patterns
    service_count = len([c for c in components if c.get("type") == "service"])
    db_count = len([c for c in components if c.get("type") == "database"])

    if pattern == "microservices" and service_count < 3:
        validations.append({
            "pattern": "microservices",
            "check": "sufficient_services",
            "passed": False,
            "message": f"Only {service_count} services for microservices pattern",
            "severity": "medium"
        })

    if db_count == 0:
        validations.append({
            "pattern": pattern,
            "check": "persistence_layer",
            "passed": False,
            "message": "No database component detected",
            "severity": "high"
        })

    # Check for gateway in microservices
    gateway_count = len([c for c in components if c.get("type") == "gateway"])
    if pattern == "microservices" and gateway_count == 0:
        validations.append({
            "pattern": "microservices",
            "check": "api_gateway",
            "passed": False,
            "message": "Microservices without API Gateway - direct service exposure",
            "severity": "high"
        })

    # Check for async communication
    queue_count = len([c for c in components if c.get("type") == "queue"])
    if pattern in ["microservices", "event_driven"] and queue_count == 0:
        validations.append({
            "pattern": pattern,
            "check": "async_communication",
            "passed": False,
            "message": "No message queue for async communication",
            "severity": "medium"
        })

    # Check for caching
    cache_count = len([c for c in components if c.get("type") == "cache"])
    if cache_count == 0 and service_count > 0:
        validations.append({
            "pattern": pattern,
            "check": "caching_layer",
            "passed": False,
            "message": "No caching layer for read-heavy services",
            "severity": "low"
        })

    passed = sum(1 for v in validations if v["passed"])
    total = len(validations) if validations else 1

    return {
        "pattern": pattern,
        "validations": validations,
        "passed_checks": passed,
        "total_checks": total,
        "pattern_adherence_score": round(passed / total, 2) if total > 0 else 1.0,
    }


async def generate_hld_spec(repo_analysis: Dict, canvas_state: Dict, mode: str, user_prompt: str) -> Dict[str, Any]:
    components = repo_analysis.get("components", [])
    pattern = repo_analysis.get("architecture_pattern", "unknown")

    hld_components = []
    for comp in components:
        hld_components.append({
            "name": comp.get("name"),
            "type": comp.get("type"),
            "technology": comp.get("tech"),
            "responsibility": comp.get("description"),
            "scaling": comp.get("config_hints", {}).get("scaling", "Horizontal"),
            "availability": comp.get("config_hints", {}).get("replication", "Active-Passive"),
            "interfaces": [],  # Will be filled from data_flows
        })

    data_flows = repo_analysis.get("data_flows", [])
    for flow in data_flows:
        for comp in hld_components:
            if comp["name"] == flow.get("from"):
                comp["interfaces"].append({
                    "direction": "outbound",
                    "target": flow.get("to"),
                    "protocol": flow.get("protocol"),
                    "description": flow.get("description"),
                })
            elif comp["name"] == flow.get("to"):
                comp["interfaces"].append({
                    "direction": "inbound",
                    "source": flow.get("from"),
                    "protocol": flow.get("protocol"),
                    "description": flow.get("description"),
                })

    return {
        "overview": f"High-Level Design for: {user_prompt}",
        "architecture_style": pattern,
        "components": hld_components,
        "integration_patterns": [
            "Synchronous: REST/gRPC for query paths",
            "Asynchronous: Kafka/RabbitMQ for event processing",
            "Caching: Redis for read acceleration",
        ],
        "data_management": "Polyglot persistence - PostgreSQL for ACID, Redis for cache, Kafka for events",
        "deployment_topology": "Containerized (Docker) on Kubernetes, multi-AZ, GitOps deployment",
        "observability": "Prometheus metrics, Grafana dashboards, Jaeger tracing, ELK logging",
        "security": "mTLS between services, OAuth2/OIDC auth, WAF at gateway, secrets in Vault",
    }


async def generate_lld_spec(repo_analysis: Dict, canvas_state: Dict, mode: str, user_prompt: str) -> Dict[str, Any]:
    components = repo_analysis.get("components", [])

    lld_components = []
    for comp in components:
        comp_type = comp.get("type")
        tech = comp.get("tech", "")

        # Technology-specific details
        api_contract = ""
        data_model = ""
        scaling_strategy = ""
        failure_modes = []
        runbook = ""

        if comp_type == "service":
            api_contract = f"REST/GraphQL API, OpenAPI 3.0 spec, {tech} framework"
            data_model = "Domain models in application layer, DTOs for API"
            scaling_strategy = "HPA based on CPU > 70%, custom metrics (RPS, latency)"
            failure_modes = ["Downstream timeout", "Database connection exhaustion", "Memory leak"]
            runbook = "1. Check logs for errors 2. Verify downstream health 3. Scale replicas 4. Restart if needed"
        elif comp_type == "database":
            api_contract = "SQL interface, connection pooling required"
            data_model = "Normalized relational schema, migrations via Alembic/Flyway"
            scaling_strategy = "Read replicas for SELECT, vertical scaling for writes, consider sharding"
            failure_modes = ["Primary failure", "Replication lag", "Disk full", "Connection storm"]
            runbook = "1. Check replication status 2. Promote replica if primary down 3. Scale storage 4. Check slow queries"
        elif comp_type == "cache":
            api_contract = "Redis protocol (RESPE), TTL-based expiration"
            data_model = "Key-value with structured values (Hash, JSON, Sorted Sets)"
            scaling_strategy = "Redis Cluster with hash slots, read replicas"
            failure_modes = ["Memory pressure", "Network partition", "Persistence delay"]
            runbook = "1. Check memory usage 2. Evict expired keys 3. Failover to replica 4. Warm cache"
        elif comp_type == "queue":
            api_contract = f"{tech} protocol, producer/consumer patterns"
            data_model = "Topic/partition model, message schema via Avro/Protobuf"
            scaling_strategy = "Add partitions, increase consumer group members"
            failure_modes = ["Broker down", "Consumer lag", "Disk full", "Under-replicated partitions"]
            runbook = "1. Check broker health 2. Rebalance partitions 3. Add consumers 4. Monitor lag"
        elif comp_type == "gateway":
            api_contract = "HTTP/HTTPS, rate limiting, auth validation, request routing"
            data_model = "Route configuration, rate limit policies, cert management"
            scaling_strategy = "Horizontal scaling, sticky sessions for WebSocket"
            failure_modes = ["Config reload failure", "Upstream timeout", "Certificate expiry"]
            runbook = "1. Validate config syntax 2. Check upstream health 3. Renew certs 4. Drain connections"
        else:
            api_contract = f"{tech} standard interface"
            data_model = "Technology-specific data model"
            scaling_strategy = "Horizontal scaling"
            failure_modes = ["Generic failures"]
            runbook = "Standard troubleshooting"

        lld_components.append({
            "name": comp.get("name"),
            "technology": tech,
            "type": comp_type,
            "api_contract": api_contract,
            "data_model": data_model,
            "scaling_strategy": scaling_strategy,
            "failure_modes": failure_modes,
            "runbook": runbook,
            "configuration": {
                "latency_ms": 20 if comp_type != "database" else 50,
                "target_rps": 1000,
                "max_capacity_rps": 5000,
                "failure_rate_percent": 0.1,
                "replication": comp.get("config_hints", {}).get("replication", "N/A"),
            }
        })

    return {
        "component_details": lld_components,
        "api_specifications": [
            {
                "service": c["name"],
                "endpoints": [
                    {"method": "GET", "path": f"/api/v1/{c['name'].lower().replace(' ', '-')}", "description": "List resources"},
                    {"method": "POST", "path": f"/api/v1/{c['name'].lower().replace(' ', '-')}", "description": "Create resource"},
                    {"method": "GET", "path": f"/api/v1/{c['name'].lower().replace(' ', '-')}/{{id}}", "description": "Get resource"},
                ]
            }
            for c in lld_components if c["type"] == "service"
        ],
        "database_schemas": [
            {
                "database": c["name"],
                "tables": [
                    {"name": "users", "columns": ["id", "email", "created_at"]},
                    {"name": "orders", "columns": ["id", "user_id", "total", "status", "created_at"]},
                ]
            }
            for c in lld_components if c["type"] == "database"
        ],
        "infrastructure_as_code": "Terraform modules for VPC, EKS/GKE, RDS, ElastiCache, MSK",
        "ci_cd_pipeline": "GitHub Actions -> Build -> Test -> Security Scan -> Deploy to Staging -> Manual Approval -> Production",
    }


async def compare_architectures(repo_analysis: Dict, markdown_spec: str, canvas_state: Dict) -> Dict[str, Any]:
    discrepancies = []

    # Extract key concepts from markdown
    markdown_lower = markdown_spec.lower()

    # Check for components mentioned in markdown but missing in repo
    repo_components = {c.get("name", "").lower() for c in repo_analysis.get("components", [])}
    markdown_keywords = ["api gateway", "load balancer", "database", "cache", "queue", "service", "storage", "cdn", "auth"]

    for kw in markdown_keywords:
        if kw in markdown_lower and not any(kw in rc for rc in repo_components):
            discrepancies.append({
                "type": "missing_in_repo",
                "element": kw,
                "source": "markdown",
                "description": f"'{kw}' mentioned in markdown but not detected in repository"
            })

    # Check for components in repo but not in markdown
    for comp in repo_analysis.get("components", []):
        comp_name = comp.get("name", "").lower()
        if comp_name and comp_name not in markdown_lower:
            discrepancies.append({
                "type": "missing_in_markdown",
                "element": comp.get("name"),
                "source": "repository",
                "description": f"'{comp.get('name')}' found in repo but not documented in markdown"
            })

    repo_vs_markdown = "consistent"
    if any(d["type"] == "missing_in_repo" for d in discrepancies):
        repo_vs_markdown = "partial"
    if any(d["type"] == "missing_in_markdown" for d in discrepancies):
        repo_vs_markdown = "conflicting" if repo_vs_markdown == "partial" else "partial"

    return {
        "repo_vs_markdown": repo_vs_markdown,
        "discrepancies": discrepancies,
        "summary": f"Found {len(discrepancies)} discrepancies between repository and markdown specification",
    }


async def estimate_costs(repo_analysis: Dict, canvas_state: Dict) -> Dict[str, Any]:
    """Rough monthly cost estimation for AWS"""
    components = repo_analysis.get("components", [])

    # Very rough estimates (USD/month)
    cost_map = {
        "api": 50,  # ALB + Lambda/Fargate
        "gateway": 100,  # Kong/Envoy on EC2/Fargate
        "service": 200,  # Fargate/ECS tasks
        "cache": 150,  # ElastiCache
        "database": 300,  # RDS
        "queue": 100,  # MSK/SQS
        "storage": 50,  # S3
    }

    total = 0
    breakdown = {}
    for comp in components:
        comp_type = comp.get("type", "service")
        cost = cost_map.get(comp_type, 100)
        # Scale by replication
        replication = comp.get("config_hints", {}).get("replication", "").lower()
        multiplier = 1
        if "3" in replication or "cluster" in replication:
            multiplier = 3
        elif "replica" in replication:
            multiplier = 2

        comp_cost = cost * multiplier
        breakdown[comp.get("name", comp_type)] = comp_cost
        total += comp_cost

    return {
        "estimated_monthly_usd": total,
        "breakdown": breakdown,
        "assumptions": "AWS us-east-1, on-demand pricing, moderate traffic",
        "optimization_potential": "Reserved instances (30-40%), Savings Plans, Spot for batch",
    }


# Preset matching and prompt-based architecture generation
PRESET_DEFINITIONS = {
    "ecommerce-microservices": {
        "id": "ecommerce-microservices",
        "name": "E-Commerce Microservices",
        "description": "Scalable transactional e-commerce engine with caching, message queue decoupling, and database replication.",
        "mode": "pro",
        "keywords": ["ecommerce", "flipkart", "amazon", "shop", "store", "cart", "order", "payment", "product", "catalog", "inventory", "marketplace", "retail", "shopping"],
        "tech_indicators": {
            "frameworks": ["go", "node.js", "express", "nestjs", "spring", "fastapi", "django", "java", "python"],
            "databases": ["postgresql", "mysql", "aurora", "postgres"],
            "caches": ["redis"],
            "queues": ["kafka", "rabbitmq"],
        },
        "pattern": "microservices",
        "components_template": [
            {"type": "api", "label": "Client Apps", "tech": "React Native & Web", "capacity": 20000},
            {"type": "gateway", "label": "API Gateway", "tech": "Kong / Envoy", "capacity": 12000},
            {"type": "service", "label": "Order Service", "tech": "Go / gRPC", "capacity": 3500},
            {"type": "service", "label": "User & Catalog Service", "tech": "Node.js / Express", "capacity": 5000},
            {"type": "cache", "label": "Redis Cluster", "tech": "Redis 7.2", "capacity": 25000},
            {"type": "queue", "label": "Kafka Event Bus", "tech": "Apache Kafka", "capacity": 30000},
            {"type": "service", "label": "Notification Worker", "tech": "Python Celery", "capacity": 2500},
            {"type": "database", "label": "Postgres Primary", "tech": "PostgreSQL", "capacity": 3000},
        ],
    },
    "video-streaming": {
        "id": "video-streaming",
        "name": "Global Video Streaming (YouTube/Netflix)",
        "description": "High-throughput video upload, asynchronous multi-bitrate transcoding pipeline, and global CDN delivery.",
        "mode": "pro",
        "keywords": ["video", "youtube", "netflix", "stream", "transcode", "hls", "dash", "media", "encoding", "ffmpeg", "cdn", "ott", "streaming"],
        "tech_indicators": {
            "frameworks": ["fastapi", "go", "node.js", "python"],
            "queues": ["kafka", "rabbitmq", "sqs"],
            "storage": ["s3", "gcs", "blob"],
        },
        "pattern": "microservices",
        "components_template": [
            {"type": "api", "label": "Viewer & Creator Clients", "tech": "Smart TVs & Web Players", "capacity": 50000},
            {"type": "gateway", "label": "Global CDN Network", "tech": "Fastly / Akamai Edge", "capacity": 60000},
            {"type": "gateway", "label": "Ingress Load Balancer", "tech": "NGINX Plus / AWS ALB", "capacity": 15000},
            {"type": "service", "label": "Video Metadata Service", "tech": "FastAPI / gRPC", "capacity": 6000},
            {"type": "queue", "label": "Transcode Queue", "tech": "RabbitMQ / AWS SQS", "capacity": 10000},
            {"type": "service", "label": "Transcoding Cluster", "tech": "FFmpeg GPU Workers", "capacity": 800},
            {"type": "storage", "label": "Object Storage (S3)", "tech": "Amazon S3", "capacity": 15000},
            {"type": "database", "label": "NoSQL Metadata DB", "tech": "ScyllaDB / Cassandra", "capacity": 10000},
        ],
    },
    "learner-url-shortener": {
        "id": "learner-url-shortener",
        "name": "URL Shortener (TinyURL) - Learner Guide",
        "description": "Clear educational architecture showing how high-read systems scale using reverse proxy, cache, and database.",
        "mode": "learner",
        "keywords": ["url", "shorten", "tinyurl", "bitly", "link", "redirect", "shortener"],
        "tech_indicators": {
            "frameworks": ["node.js", "express", "fastapi", "flask", "go", "python"],
            "caches": ["redis"],
            "databases": ["postgresql", "mysql", "postgres"],
        },
        "pattern": "monolith",
        "components_template": [
            {"type": "api", "label": "Web Browser / Mobile", "tech": "Client Browser", "capacity": 10000},
            {"type": "gateway", "label": "Load Balancer", "tech": "NGINX Reverse Proxy", "capacity": 8000},
            {"type": "service", "label": "URL Shortener App", "tech": "Node.js / FastAPI", "capacity": 4000},
            {"type": "cache", "label": "Redis Cache", "tech": "Redis", "capacity": 15000},
            {"type": "database", "label": "Persistent Database", "tech": "PostgreSQL", "capacity": 2500},
        ],
    },
    "chat-messaging": {
        "id": "chat-messaging",
        "name": "Real-time Chat & Messaging (WhatsApp/Slack)",
        "description": "Low-latency bidirectional messaging with WebSocket gateways, Pub/Sub routing, and persistent history.",
        "mode": "pro",
        "keywords": ["chat", "whatsapp", "slack", "messaging", "realtime", "websocket", "messenger", "telegram", "discord"],
        "tech_indicators": {
            "frameworks": ["go", "node.js", "elixir", "rust"],
            "caches": ["redis"],
            "databases": ["cassandra", "scylladb", "postgresql"],
            "queues": ["kafka", "nats", "pulsar"],
        },
        "pattern": "microservices",
        "components_template": [
            {"type": "api", "label": "Chat Mobile & Web", "tech": "React Native & WebSockets", "capacity": 25000},
            {"type": "gateway", "label": "WebSocket Gateway", "tech": "Go / Gorilla WS", "capacity": 15000},
            {"type": "cache", "label": "Redis Pub/Sub", "tech": "Redis Cluster", "capacity": 30000},
            {"type": "database", "label": "Message History Store", "tech": "Cassandra / ScyllaDB", "capacity": 8000},
        ],
    },
    "ride-hailing": {
        "id": "ride-hailing",
        "name": "Ride-Hailing Platform (Uber/Lyft)",
        "description": "Real-time ride matching with geospatial indexing, trip orchestration, and surge pricing.",
        "mode": "pro",
        "keywords": ["uber", "lyft", "ride", "hailing", "taxi", "driver", "passenger", "matching", "geospatial", "surge"],
        "tech_indicators": {
            "frameworks": ["go", "java", "node.js", "python"],
            "databases": ["postgresql", "cassandra", "redis"],
            "caches": ["redis"],
            "queues": ["kafka", "pulsar"],
        },
        "pattern": "microservices",
        "components_template": [
            {"type": "api", "label": "Rider & Driver Apps", "tech": "React Native / Swift / Kotlin", "capacity": 30000},
            {"type": "gateway", "label": "API Gateway", "tech": "Envoy / Kong", "capacity": 20000},
            {"type": "service", "label": "Trip Matching Service", "tech": "Go / Redis Geospatial", "capacity": 5000},
            {"type": "service", "label": "Driver Location Service", "tech": "Redis / WebSocket", "capacity": 15000},
            {"type": "service", "label": "Pricing & Surge Engine", "tech": "Python / ML", "capacity": 3000},
            {"type": "queue", "label": "Trip Event Queue", "tech": "Apache Kafka", "capacity": 50000},
            {"type": "database", "label": "Trip History DB", "tech": "PostgreSQL / Cassandra", "capacity": 10000},
            {"type": "database", "label": "Geospatial Index", "tech": "Redis / PostGIS", "capacity": 20000},
        ],
    },
    "food-delivery": {
        "id": "food-delivery",
        "name": "Food Delivery Platform (DoorDash/Swiggy/Zomato)",
        "description": "Three-sided marketplace with restaurant onboarding, order orchestration, and driver dispatch.",
        "mode": "pro",
        "keywords": ["food", "delivery", "doordash", "swiggy", "zomato", "restaurant", "order", "driver", "dispatch", "marketplace"],
        "tech_indicators": {
            "frameworks": ["go", "node.js", "python", "java"],
            "databases": ["postgresql", "cassandra", "mongodb"],
            "caches": ["redis"],
            "queues": ["kafka", "rabbitmq"],
        },
        "pattern": "microservices",
        "components_template": [
            {"type": "api", "label": "Customer / Restaurant / Driver Apps", "tech": "React Native / Flutter", "capacity": 40000},
            {"type": "gateway", "label": "API Gateway", "tech": "Kong / Envoy", "capacity": 25000},
            {"type": "service", "label": "Order Service", "tech": "Go / gRPC", "capacity": 5000},
            {"type": "service", "label": "Restaurant Service", "tech": "Node.js / Express", "capacity": 4000},
            {"type": "service", "label": "Dispatch Service", "tech": "Python / Geospatial", "capacity": 3000},
            {"type": "queue", "label": "Order Event Queue", "tech": "Kafka", "capacity": 30000},
            {"type": "cache", "label": "Redis Cache", "tech": "Redis Cluster", "capacity": 30000},
            {"type": "database", "label": "Order DB", "tech": "PostgreSQL", "capacity": 5000},
            {"type": "database", "label": "Restaurant Catalog", "tech": "MongoDB / Elasticsearch", "capacity": 8000},
        ],
    },
    "social-media": {
        "id": "social-media",
        "name": "Social Media Platform (Twitter/Instagram)",
        "description": "High-fanout feed generation, media storage, and real-time notifications at massive scale.",
        "mode": "pro",
        "keywords": ["twitter", "instagram", "facebook", "social", "feed", "timeline", "tweet", "post", "follow", "media"],
        "tech_indicators": {
            "frameworks": ["go", "java", "scala", "python"],
            "databases": ["cassandra", "scylladb", "postgresql", "redis"],
            "caches": ["redis", "memcached"],
            "queues": ["kafka", "pulsar"],
            "storage": ["s3", "gcs"],
        },
        "pattern": "microservices",
        "components_template": [
            {"type": "api", "label": "Client Apps", "tech": "iOS / Android / Web", "capacity": 100000},
            {"type": "gateway", "label": "Edge Load Balancer", "tech": "Envoy / HAProxy", "capacity": 50000},
            {"type": "service", "label": "Feed Generation Service", "tech": "Go / Redis", "capacity": 10000},
            {"type": "service", "label": "Timeline Service", "tech": "Scala / Flink", "capacity": 5000},
            {"type": "service", "label": "Media Service", "tech": "Python / FFmpeg", "capacity": 2000},
            {"type": "queue", "label": "Fanout Queue", "tech": "Kafka / Pulsar", "capacity": 100000},
            {"type": "cache", "label": "Feed Cache", "tech": "Redis Cluster", "capacity": 50000},
            {"type": "database", "label": "User Graph DB", "tech": "Cassandra / ScyllaDB", "capacity": 20000},
            {"type": "storage", "label": "Media Storage", "tech": "S3 / GCS", "capacity": 20000},
        ],
    },
    "fintech-payments": {
        "id": "fintech-payments",
        "name": "FinTech Payments Platform (Stripe/Razorpay)",
        "description": "Secure payment processing with fraud detection, ledger accounting, and multi-currency support.",
        "mode": "pro",
        "keywords": ["payment", "stripe", "razorpay", "fintech", "transaction", "ledger", "fraud", "wallet", "banking"],
        "tech_indicators": {
            "frameworks": ["go", "java", "rust", "python"],
            "databases": ["postgresql", "cockroachdb", "mysql"],
            "caches": ["redis"],
            "queues": ["kafka", "nats"],
        },
        "pattern": "microservices",
        "components_template": [
            {"type": "api", "label": "Merchant / Customer Apps", "tech": "React / SDKs", "capacity": 20000},
            {"type": "gateway", "label": "Payment Gateway", "tech": "Envoy / Custom", "capacity": 15000},
            {"type": "service", "label": "Payment Processing", "tech": "Go / Rust", "capacity": 5000},
            {"type": "service", "label": "Fraud Detection", "tech": "Python / ML", "capacity": 2000},
            {"type": "service", "label": "Ledger Service", "tech": "Java / CockroachDB", "capacity": 3000},
            {"type": "queue", "label": "Transaction Queue", "tech": "Kafka / NATS", "capacity": 20000},
            {"type": "database", "label": "Transaction Ledger", "tech": "CockroachDB / PostgreSQL", "capacity": 5000},
            {"type": "cache", "label": "Risk Cache", "tech": "Redis", "capacity": 15000},
        ],
    },
}


async def match_prompt_to_preset(prompt: str, mode: str = "pro") -> Dict[str, Any]:
    """
    Match a user prompt to the closest preset architecture.
    """
    try:
        prompt_lower = prompt.lower()
        
        best_match = None
        best_score = 0
        all_scores = {}
        
        for preset_id, preset in PRESET_DEFINITIONS.items():
            # Skip if mode doesn't match (unless no mode-specific preset)
            if preset.get("mode") != mode and mode == "learner":
                # Allow pro presets in learner mode if no learner match
                pass
            elif preset.get("mode") == "learner" and mode == "pro":
                continue  # Skip learner-only presets in pro mode
                
            score = 0
            matched_keywords = []
            
            # Keyword matching
            for keyword in preset["keywords"]:
                if keyword in prompt_lower:
                    score += 10
                    matched_keywords.append(keyword)
            
            # Partial keyword matching (substring)
            for keyword in preset["keywords"]:
                if keyword not in matched_keywords:
                    for word in prompt_lower.split():
                        if word in keyword or keyword in word:
                            score += 3
                            matched_keywords.append(keyword)
                            break
            
            all_scores[preset_id] = {"score": score, "matched_keywords": matched_keywords}
            
            if score > best_score:
                best_score = score
                best_match = preset_id
        
        # If no good match, try to infer from tech mentions
        if best_score < 10:
            tech_hints = {
                "kafka": "ecommerce-microservices",
                "redis": "ecommerce-microservices",
                "microservice": "ecommerce-microservices",
                "websocket": "chat-messaging",
                "geospatial": "ride-hailing",
                "surge": "ride-hailing",
                "dispatch": "food-delivery",
                "restaurant": "food-delivery",
                "feed": "social-media",
                "timeline": "social-media",
                "fraud": "fintech-payments",
                "ledger": "fintech-payments",
            }
            for hint, preset_id in tech_hints.items():
                if hint in prompt_lower:
                    best_match = preset_id
                    best_score = 8
                    break
        
        confidence = min(best_score / 30.0, 1.0) if best_match else 0.0
        
        return {
            "matched_preset_id": best_match,
            "matched_preset_name": PRESET_DEFINITIONS[best_match]["name"] if best_match else None,
            "matched_preset_mode": PRESET_DEFINITIONS[best_match]["mode"] if best_match else mode,
            "confidence": confidence,
            "all_scores": all_scores,
            "reasoning": f"Best match: {best_match} with score {best_score}" if best_match else "No strong preset match, will generate custom architecture",
        }
    except Exception as e:
        import traceback
        print(f"ERROR in match_prompt_to_preset: {e}")
        traceback.print_exc()
        return {"matched_preset_id": None, "error": str(e)}


async def generate_architecture_from_prompt(prompt: str, mode: str = "pro", matched_preset: Dict = None) -> Dict[str, Any]:
    """
    Generate a complete architecture from a prompt, using a matched preset as base if available.
    """
    # If we have a matched preset, customize it
    if matched_preset and matched_preset.get("matched_preset_id"):
        preset = PRESET_DEFINITIONS[matched_preset["matched_preset_id"]]
        template = preset["components_template"]
        
        # Customize based on prompt specifics
        components = []
        for i, tmpl in enumerate(template):
            comp = {
                "name": tmpl["label"],
                "type": tmpl["type"],
                "tech": tmpl["tech"],
                "description": f"{tmpl['label']} for {prompt[:50]}",
                "config": {
                    "latency": 20,
                    "rps": 1000,
                    "capacity": tmpl.get("capacity", 5000),
                    "failureRate": 0.1,
                    "replication": "Auto-scaling",
                },
                "explanation": f"Core {tmpl['type']} component for the {preset['name'].lower()} architecture.",
            }
            components.append(comp)
        
        # Generate data flows based on architecture pattern
        data_flows = []
        if preset["pattern"] == "microservices":
            # Standard microservices flow
            data_flows = [
                {"from": "Client Apps", "to": "API Gateway", "protocol": "HTTPS", "traffic_estimate_rps": 5000},
                {"from": "API Gateway", "to": "Order Service", "protocol": "gRPC", "traffic_estimate_rps": 3000},
                {"from": "API Gateway", "to": "User & Catalog Service", "protocol": "gRPC", "traffic_estimate_rps": 2000},
                {"from": "Order Service", "to": "Kafka Event Bus", "protocol": "Kafka", "traffic_estimate_rps": 3000},
                {"from": "Order Service", "to": "Postgres Primary", "protocol": "SQL", "traffic_estimate_rps": 2000},
                {"from": "User & Catalog Service", "to": "Redis Cluster", "protocol": "TCP", "traffic_estimate_rps": 2000},
                {"from": "Kafka Event Bus", "to": "Notification Worker", "protocol": "Kafka", "traffic_estimate_rps": 1000},
            ]
        elif preset["pattern"] == "monolith":
            data_flows = [
                {"from": "Web Browser / Mobile", "to": "Load Balancer", "protocol": "HTTPS", "traffic_estimate_rps": 2000},
                {"from": "Load Balancer", "to": "URL Shortener App", "protocol": "HTTP/REST", "traffic_estimate_rps": 2000},
                {"from": "URL Shortener App", "to": "Redis Cache", "protocol": "TCP", "traffic_estimate_rps": 1500},
                {"from": "URL Shortener App", "to": "Persistent Database", "protocol": "SQL", "traffic_estimate_rps": 500},
            ]
        
        return {
            "summary": f"Architecture for: {prompt}. Based on {preset['name']} pattern.",
            "architecture_pattern": preset["pattern"],
            "pattern_confidence": matched_preset.get("confidence", 0.8),
            "components": components,
            "data_flows": data_flows,
            "infrastructure": {
                "cloud": "aws",
                "containerization": "docker",
                "orchestration": "kubernetes",
                "ci_cd": "github-actions",
            },
            "scalability_concerns": [
                "Database write throughput at peak",
                "Cache invalidation strategy",
                "Cross-service latency in microservices",
            ],
            "recommendations": [
                "Implement circuit breakers for all service calls",
                "Use read replicas for database scaling",
                "Add distributed tracing (Jaeger/Zipkin)",
                "Configure auto-scaling based on CPU and custom metrics",
            ],
            "confidence": matched_preset.get("confidence", 0.8),
            "preset_based": True,
            "preset_id": matched_preset["matched_preset_id"],
        }
    
    # No preset match - generate custom architecture via LLM prompt
    # This would be handled by the LLM call in the agent's execute method
    return {
        "summary": f"Custom architecture for: {prompt}",
        "architecture_pattern": "custom",
        "pattern_confidence": 0.5,
        "components": [],
        "data_flows": [],
        "infrastructure": {},
        "scalability_concerns": [],
        "recommendations": [],
        "confidence": 0.5,
        "preset_based": False,
    }


async def modify_existing_architecture(canvas_state: Dict[str, Any], user_prompt: str, mode: str = "pro") -> Dict[str, Any]:
    """
    Modify an existing architecture based on user prompt.
    """
    nodes = canvas_state.get("nodes", [])
    edges = canvas_state.get("edges", [])
    prompt_lower = user_prompt.lower()
    
    # Parse existing components
    existing_components = []
    for node in nodes:
        data = node.get("data", {})
        existing_components.append({
            "name": data.get("label", node.get("id")),
            "type": data.get("category", "service"),
            "tech": data.get("tech", "TBD"),
            "description": data.get("description", ""),
            "config": {
                "latency": data.get("latency", 20),
                "rps": data.get("rps", 1000),
                "capacity": data.get("capacity", 5000),
                "failureRate": data.get("failureRate", 0.1),
                "replication": data.get("replication", "Auto-scaling"),
            },
            "explanation": data.get("explanation", ""),
        })
    
    # Parse existing data flows
    existing_flows = []
    for edge in edges:
        edge_data = edge.get("data", {})
        existing_flows.append({
            "from": edge.get("source"),
            "to": edge.get("target"),
            "protocol": edge_data.get("protocol", "HTTP/REST"),
            "description": edge.get("label", ""),
            "traffic_estimate_rps": edge_data.get("trafficRps", 1000),
        })
    
    # Analyze what modification is needed
    components = list(existing_components)
    data_flows = list(existing_flows)
    
    if any(kw in prompt_lower for kw in ['add', 'insert']):
        # Add new component
        if 'database' in prompt_lower or 'db' in prompt_lower or 'postgres' in prompt_lower or 'mysql' in prompt_lower:
            new_comp = {
                "name": "New Database",
                "type": "database",
                "tech": "PostgreSQL",
                "description": "Added database for data persistence",
                "config": {"latency": 22, "rps": 700, "capacity": 2500, "failureRate": 0.1, "replication": "Primary-Replica"},
                "explanation": "Added database component as requested",
            }
            components.append(new_comp)
            # Connect to last service if exists
            services = [c for c in components if c["type"] == "service"]
            if services:
                data_flows.append({"from": services[-1]["name"], "to": "New Database", "protocol": "SQL", "traffic_estimate_rps": 500})
        
        elif 'cache' in prompt_lower or 'redis' in prompt_lower:
            new_comp = {
                "name": "New Cache",
                "type": "cache",
                "tech": "Redis",
                "description": "Added cache layer for performance",
                "config": {"latency": 2, "rps": 2000, "capacity": 25000, "failureRate": 0.05, "replication": "Cluster"},
                "explanation": "Added cache component as requested",
            }
            components.append(new_comp)
            services = [c for c in components if c["type"] == "service"]
            if services:
                data_flows.append({"from": services[-1]["name"], "to": "New Cache", "protocol": "TCP", "traffic_estimate_rps": 1000})
        
        elif 'queue' in prompt_lower or 'kafka' in prompt_lower or 'message' in prompt_lower:
            new_comp = {
                "name": "New Message Queue",
                "type": "queue",
                "tech": "Kafka",
                "description": "Added message queue for async processing",
                "config": {"latency": 10, "rps": 1000, "capacity": 10000, "failureRate": 0.05, "replication": "3x"},
                "explanation": "Added message queue as requested",
            }
            components.append(new_comp)
            services = [c for c in components if c["type"] == "service"]
            if services:
                data_flows.append({"from": services[-1]["name"], "to": "New Message Queue", "protocol": "Kafka", "traffic_estimate_rps": 500})
        
        elif 'service' in prompt_lower or 'microservice' in prompt_lower:
            new_comp = {
                "name": "New Service",
                "type": "service",
                "tech": "FastAPI",
                "description": "Added new microservice",
                "config": {"latency": 25, "rps": 1000, "capacity": 5000, "failureRate": 0.2, "replication": "Auto-scaling"},
                "explanation": "Added new service component as requested",
            }
            components.append(new_comp)
            # Connect from gateway if exists
            gateways = [c for c in components if c["type"] == "gateway"]
            if gateways:
                data_flows.append({"from": gateways[-1]["name"], "to": "New Service", "protocol": "gRPC", "traffic_estimate_rps": 1000})
    
    elif any(kw in prompt_lower for kw in ['remove', 'delete']):
        # Remove component by name (simple approach - remove last matching type)
        if 'database' in prompt_lower:
            components = [c for c in components if c["type"] != "database"]
        elif 'cache' in prompt_lower:
            components = [c for c in components if c["type"] != "cache"]
        elif 'queue' in prompt_lower:
            components = [c for c in components if c["type"] != "queue"]
        elif 'service' in prompt_lower:
            services = [c for c in components if c["type"] == "service"]
            if services:
                components = [c for c in components if c["name"] != services[-1]["name"]]
        
        # Rebuild data flows for remaining components
        data_flows = [f for f in data_flows if 
            any(c["name"] == f["from"] for c in components) and 
            any(c["name"] == f["to"] for c in components)]
    
    elif any(kw in prompt_lower for kw in ['change', 'update', 'modify', 'rename']):
        # Update existing component properties
        for comp in components:
            if 'latency' in prompt_lower:
                # Extract number if present
                import re
                nums = re.findall(r'\d+', prompt_lower)
                if nums:
                    comp["config"]["latency"] = int(nums[0])
            if 'capacity' in prompt_lower or 'rps' in prompt_lower:
                import re
                nums = re.findall(r'\d+', prompt_lower)
                if nums:
                    comp["config"]["capacity"] = int(nums[0])
            if 'replication' in prompt_lower:
                if 'multi' in prompt_lower or '3' in prompt_lower:
                    comp["config"]["replication"] = "3x Replication"
                elif 'replica' in prompt_lower:
                    comp["config"]["replication"] = "Primary-Replica"
    
    elif any(kw in prompt_lower for kw in ['connect', 'link']):
        # Add connection between components
        # Simple approach: connect last two components if not already connected
        if len(components) >= 2:
            data_flows.append({
                "from": components[-2]["name"],
                "to": components[-1]["name"],
                "protocol": "HTTP/REST",
                "traffic_estimate_rps": 1000,
            })
    
    # Determine architecture pattern
    pattern = "microservices" if len([c for c in components if c["type"] == "service"]) > 1 else "monolith"
    
    return {
        "summary": f"Modified architecture: {user_prompt}",
        "architecture_pattern": pattern,
        "pattern_confidence": 0.8,
        "components": components,
        "data_flows": data_flows,
        "infrastructure": {
            "cloud": "aws",
            "containerization": "docker",
            "orchestration": "kubernetes",
            "ci_cd": "github-actions",
        },
        "scalability_concerns": [
            "Database write throughput at peak",
            "Cache invalidation strategy",
            "Cross-service latency in microservices",
        ],
        "recommendations": [
            "Implement circuit breakers for all service calls",
            "Use read replicas for database scaling",
            "Add distributed tracing (Jaeger/Zipkin)",
            "Configure auto-scaling based on CPU and custom metrics",
        ],
        "confidence": 0.8,
        "preset_based": False,
    }