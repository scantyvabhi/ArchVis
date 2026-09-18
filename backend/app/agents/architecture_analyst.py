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
        ]

    async def execute(self, context: AgentContext) -> AgentResult:
        import time
        start_time = time.time()

        self.status = AgentStatus.RUNNING
        reasoning_parts = []
        tool_calls = []

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
            return AgentResult(
                agent_role=self.role,
                status=AgentStatus.FAILED,
                output={},
                reasoning="\n".join(reasoning_parts),
                confidence=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                tool_calls=tool_calls,
            )


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