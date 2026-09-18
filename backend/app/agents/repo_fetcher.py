import re
import json
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base import BaseAgent, AgentRole, AgentContext, AgentResult, AgentStatus, ToolResult
from ..repo_parser import RepoParser


class RepoFetcherAgent(BaseAgent):
    def __init__(self, model_client, sandbox, tools: Dict, config: Dict):
        super().__init__(AgentRole.REPO_FETCHER, model_client, sandbox, tools, config)

    def get_system_prompt(self) -> str:
        return """You are the **Repository Fetcher Agent** for ArchVis AI.

Your role is to:
1. Fetch and analyze GitHub repositories to extract architectural information
2. Identify technologies, frameworks, databases, message queues, and infrastructure from code
3. Parse README files and documentation for system design context
4. Detect architectural patterns (microservices, monolith, event-driven, etc.)
5. Extract deployment configurations (Docker, K8s, cloud provider configs)

You work in a SANDBOXED environment - you can only use the provided tools.
Your output must be structured JSON that other agents can consume.

Key outputs:
- detected_tech: List of technologies with versions if possible
- architecture_pattern: "microservices" | "monolith" | "modular_monolith" | "serverless" | "event_driven" | "unknown"
- components: List of identified components with type, name, config hints
- data_flow: Inferred data flow between components
- infrastructure: Cloud, containers, orchestration details
- confidence: 0.0-1.0 confidence in your analysis"""

    def get_available_tools(self) -> List[str]:
        return [
            "fetch_github_repo",
            "parse_repo_structure",
            "extract_tech_stack",
            "analyze_readme",
            "detect_architecture_pattern",
            "infer_components",
        ]

    async def execute(self, context: AgentContext) -> AgentResult:
        import time
        start_time = time.time()

        self.status = AgentStatus.RUNNING
        reasoning_parts = []
        tool_calls = []

        try:
            if not context.repo_url:
                return AgentResult(
                    agent_role=self.role,
                    status=AgentStatus.FAILED,
                    output={},
                    reasoning="No repository URL provided",
                    confidence=0.0,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    error="Missing repo_url in context",
                )

            reasoning_parts.append(f"Fetching repository: {context.repo_url}")

            # Fetch repo context using existing parser
            repo_context_result = await self._call_tool("fetch_github_repo", repo_url=context.repo_url)
            tool_calls.append({"tool": "fetch_github_repo", "args": {"repo_url": context.repo_url}, "result": repo_context_result.success})

            if not repo_context_result.success:
                return AgentResult(
                    agent_role=self.role,
                    status=AgentStatus.FAILED,
                    output={},
                    reasoning="Failed to fetch repository",
                    confidence=0.0,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    error=repo_context_result.error,
                )

            repo_context = repo_context_result.data
            reasoning_parts.append(f"Fetched repo: {repo_context.get('repo', 'unknown')}, detected tech: {repo_context.get('detected_tech', [])}")

            # Parse structure
            structure_result = await self._call_tool("parse_repo_structure", repo_context=repo_context)
            tool_calls.append({"tool": "parse_repo_structure", "result": structure_result.success})

            # Extract tech stack
            tech_result = await self._call_tool("extract_tech_stack", repo_context=repo_context)
            tool_calls.append({"tool": "extract_tech_stack", "result": tech_result.success})

            # Analyze README
            readme_result = await self._call_tool("analyze_readme", repo_context=repo_context)
            tool_calls.append({"tool": "analyze_readme", "result": readme_result.success})

            # Detect architecture pattern
            pattern_result = await self._call_tool("detect_architecture_pattern", repo_context=repo_context, tech_stack=tech_result.data)
            tool_calls.append({"tool": "detect_architecture_pattern", "result": pattern_result.success})

            # Infer components
            components_result = await self._call_tool("infer_components", repo_context=repo_context, tech_stack=tech_result.data)
            tool_calls.append({"tool": "infer_components", "result": components_result.success})

            # Use LLM to synthesize and reason about the architecture
            synthesis_prompt = f"""
Analyze this GitHub repository and synthesize a comprehensive architectural understanding:

Repository: {repo_context.get('repo_url', 'unknown')}
Owner/Repo: {repo_context.get('owner', '')}/{repo_context.get('repo', '')}
Detected Technologies: {repo_context.get('detected_tech', [])}
Files Found: {repo_context.get('files', [])[:50]}
README Excerpt: {repo_context.get('readme_excerpt', '')[:3000]}

Tech Stack Analysis: {json.dumps(tech_result.data, indent=2) if tech_result.data else '{}'}
Architecture Pattern: {pattern_result.data.get('pattern', 'unknown') if pattern_result.data else 'unknown'}
Pattern Confidence: {pattern_result.data.get('confidence', 0) if pattern_result.data else 0}
Inferred Components: {json.dumps(components_result.data, indent=2) if components_result.data else '[]'}

Provide a detailed architectural analysis in JSON format with:
{{
  "summary": "Executive summary of the architecture",
  "architecture_pattern": "microservices|monolith|modular_monolith|serverless|event_driven|unknown",
  "pattern_confidence": 0.0-1.0,
  "components": [
    {{"name": "component-name", "type": "api|gateway|service|cache|database|queue|storage", "tech": "specific technology", "description": "what it does", "config_hints": {{"replication": "...", "scaling": "..."}}}}
  ],
  "data_flows": [
    {{"from": "component-a", "to": "component-b", "protocol": "HTTP/REST|gRPC|Kafka|SQL|TCP", "description": "what flows"}}
  ],
  "infrastructure": {{
    "cloud": "aws|gcp|azure|on-prem|unknown",
    "containerization": "docker|kubernetes|none",
    "orchestration": "ecs|eks|k8s|docker-compose|none",
    "ci_cd": "github-actions|gitlab|jenkins|unknown"
  }},
  "scalability_concerns": ["concern1", "concern2"],
  "recommendations": ["rec1", "rec2"],
  "confidence": 0.0-1.0
}}

Respond ONLY with valid JSON.
"""

            llm_response = await self._call_model(
                prompt=synthesis_prompt,
                model_preference=self.config.get("preferred_model", "nemotron"),
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )

            analysis = json.loads(llm_response)

            # Store in shared memory for other agents
            context.shared_memory["repo_analysis"] = analysis
            context.shared_memory["repo_context"] = repo_context
            context.agent_outputs[self.role.value] = analysis

            reasoning_parts.append(f"Synthesized architecture: {analysis.get('architecture_pattern', 'unknown')} with {len(analysis.get('components', []))} components")

            return AgentResult(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output=analysis,
                reasoning="\n".join(reasoning_parts),
                confidence=analysis.get("confidence", 0.8),
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
async def fetch_github_repo(repo_url: str) -> Dict[str, Any]:
    return await RepoParser.fetch_repo_context(repo_url)


async def parse_repo_structure(repo_context: Dict[str, Any]) -> Dict[str, Any]:
    files = repo_context.get("files", [])
    structure = {
        "total_files": len(files),
        "directories": [f for f in files if not "." in f or f.endswith("/")],
        "config_files": [f for f in files if any(f.endswith(ext) for ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".conf"])],
        "source_files": [f for f in files if any(f.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".java", ".rs", ".cpp", ".cs"])],
        "docker_files": [f for f in files if "docker" in f.lower()],
        "k8s_files": [f for f in files if any(k in f.lower() for k in ["k8s", "kubernetes", ".yaml"]) and "deployment" in f.lower()],
    }
    return structure


async def extract_tech_stack(repo_context: Dict[str, Any]) -> Dict[str, Any]:
    detected = repo_context.get("detected_tech", [])
    files = repo_context.get("files", [])

    tech_categories = {
        "languages": [],
        "frameworks": [],
        "databases": [],
        "message_queues": [],
        "caches": [],
        "infrastructure": [],
        "monitoring": [],
        "auth": [],
    }

    tech_map = {
        # Languages
        "Python": "languages", "JavaScript": "languages", "TypeScript": "languages",
        "Go": "languages", "Java": "languages", "Rust": "languages", "C#": "languages",
        # Frameworks
        "FastAPI": "frameworks", "Django": "frameworks", "Flask": "frameworks",
        "Express": "frameworks", "NestJS": "frameworks", "Spring Boot": "frameworks",
        "Gin": "frameworks", "Actix": "frameworks", "ASP.NET": "frameworks",
        # Databases
        "PostgreSQL": "databases", "MySQL": "databases", "MongoDB": "databases",
        "Redis": "caches", "Cassandra": "databases", "DynamoDB": "databases",
        "Elasticsearch": "databases", "ClickHouse": "databases",
        # Message Queues
        "Kafka": "message_queues", "RabbitMQ": "message_queues", "NATS": "message_queues",
        "SQS": "message_queues", "PubSub": "message_queues", "Pulsar": "message_queues",
        # Caches
        "Redis": "caches", "Memcached": "caches", "Dragonfly": "caches",
        # Infrastructure
        "Docker": "infrastructure", "Kubernetes": "infrastructure", "Terraform": "infrastructure",
        "AWS": "infrastructure", "GCP": "infrastructure", "Azure": "infrastructure",
        "Helm": "infrastructure", "ArgoCD": "infrastructure",
        # Monitoring
        "Prometheus": "monitoring", "Grafana": "monitoring", "Datadog": "monitoring",
        "New Relic": "monitoring", "Jaeger": "monitoring", "Zipkin": "monitoring",
        # Auth
        "OAuth": "auth", "OIDC": "auth", "JWT": "auth", "Keycloak": "auth", "Auth0": "auth",
    }

    for tech in detected:
        for keyword, category in tech_map.items():
            if keyword.lower() in tech.lower():
                if tech not in tech_categories[category]:
                    tech_categories[category].append(tech)

    return tech_categories


async def analyze_readme(repo_context: Dict[str, Any]) -> Dict[str, Any]:
    readme = repo_context.get("readme_excerpt", "")
    if not readme:
        return {"has_readme": False, "summary": "", "architecture_hints": []}

    readme_lower = readme.lower()
    architecture_keywords = {
        "microservice": ["microservice", "micro-service"],
        "monolith": ["monolith", "monolithic"],
        "event-driven": ["event-driven", "event driven", "event sourcing", "cqrs"],
        "serverless": ["serverless", "lambda", "cloud function", "faas"],
        "api-gateway": ["api gateway", "gateway", "kong", "envoy", "traefik"],
        "service-mesh": ["service mesh", "istio", "linkerd", "consul"],
        "kubernetes": ["kubernetes", "k8s", "helm", "kubectl"],
        "docker": ["docker", "container", "dockerfile", "docker-compose"],
        "database": ["database", "db", "sql", "postgres", "mysql", "mongodb"],
        "cache": ["cache", "redis", "memcached"],
        "queue": ["queue", "kafka", "rabbitmq", "message broker", "pub/sub"],
        "load-balancer": ["load balancer", "nginx", "haproxy", "alb", "elb"],
        "cdn": ["cdn", "cloudflare", "cloudfront", "akamai"],
    }

    found_patterns = []
    for pattern, keywords in architecture_keywords.items():
        if any(kw in readme_lower for kw in keywords):
            found_patterns.append(pattern)

    return {
        "has_readme": True,
        "length": len(readme),
        "architecture_hints": found_patterns,
        "summary": readme[:500] + "..." if len(readme) > 500 else readme,
    }


async def detect_architecture_pattern(repo_context: Dict[str, Any], tech_stack: Dict[str, Any]) -> Dict[str, Any]:
    readme_analysis = await analyze_readme(repo_context)
    hints = readme_analysis.get("architecture_hints", [])

    has_k8s = "kubernetes" in hints or "docker" in hints
    has_microservices = "microservice" in hints
    has_event_driven = "event-driven" in hints
    has_serverless = "serverless" in hints
    has_api_gateway = "api-gateway" in hints

    services_count = len([t for t in tech_stack.get("frameworks", [])])

    if has_serverless:
        return {"pattern": "serverless", "confidence": 0.85, "reasoning": "Serverless keywords found in README"}
    elif has_microservices and services_count > 2:
        return {"pattern": "microservices", "confidence": 0.9, "reasoning": "Microservices mentioned with multiple frameworks"}
    elif has_event_driven and tech_stack.get("message_queues"):
        return {"pattern": "event_driven", "confidence": 0.85, "reasoning": "Event-driven pattern with message queues detected"}
    elif has_k8s and services_count > 1:
        return {"pattern": "microservices", "confidence": 0.75, "reasoning": "Kubernetes with multiple services suggests microservices"}
    elif has_api_gateway:
        return {"pattern": "microservices", "confidence": 0.7, "reasoning": "API Gateway pattern detected"}
    elif services_count > 0:
        return {"pattern": "modular_monolith", "confidence": 0.6, "reasoning": "Multiple frameworks but no clear microservices indicators"}
    else:
        return {"pattern": "monolith", "confidence": 0.5, "reasoning": "Default assumption for single codebase"}


async def infer_components(repo_context: Dict[str, Any], tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
    components = []
    files = repo_context.get("files", [])
    detected = repo_context.get("detected_tech", [])

    # API/Gateway detection
    if any("gateway" in f.lower() or "nginx" in f.lower() or "envoy" in f.lower() or "kong" in f.lower() for f in files):
        components.append({
            "name": "API Gateway",
            "type": "gateway",
            "tech": "NGINX / Envoy / Kong",
            "description": "Traffic ingress, rate limiting, SSL termination",
            "config_hints": {"replication": "Active-Active", "scaling": "Horizontal"}
        })

    # Service detection from frameworks
    frameworks = tech_stack.get("frameworks", [])
    for fw in frameworks[:5]:
        components.append({
            "name": f"{fw} Service",
            "type": "service",
            "tech": fw,
            "description": f"Core business logic service built with {fw}",
            "config_hints": {"replication": "Auto-scaling", "scaling": "Horizontal"}
        })

    # Database detection
    databases = tech_stack.get("databases", [])
    for db in databases[:3]:
        components.append({
            "name": f"{db} Database",
            "type": "database",
            "tech": db,
            "description": f"Primary data store using {db}",
            "config_hints": {"replication": "Primary-Replica", "scaling": "Read replicas"}
        })

    # Cache detection
    caches = tech_stack.get("caches", [])
    for cache in caches[:2]:
        components.append({
            "name": f"{cache} Cache",
            "type": "cache",
            "tech": cache,
            "description": f"In-memory caching layer with {cache}",
            "config_hints": {"replication": "Cluster mode", "scaling": "Sharding"}
        })

    # Message queue detection
    queues = tech_stack.get("message_queues", [])
    for queue in queues[:2]:
        components.append({
            "name": f"{queue} Message Queue",
            "type": "queue",
            "tech": queue,
            "description": f"Async message processing with {queue}",
            "config_hints": {"replication": "Multi-broker", "scaling": "Partitioned"}
        })

    # If no components inferred, create defaults based on pattern
    if not components:
        pattern_result = await detect_architecture_pattern(repo_context, tech_stack)
        pattern = pattern_result.get("pattern", "monolith")

        if pattern == "microservices":
            components = [
                {"name": "API Gateway", "type": "gateway", "tech": "Kong/Envoy", "description": "Ingress gateway", "config_hints": {}},
                {"name": "Auth Service", "type": "service", "tech": "Go/Node.js", "description": "Authentication & authorization", "config_hints": {}},
                {"name": "Core API", "type": "service", "tech": "FastAPI/Spring", "description": "Business logic", "config_hints": {}},
                {"name": "PostgreSQL", "type": "database", "tech": "PostgreSQL", "description": "Primary database", "config_hints": {}},
                {"name": "Redis", "type": "cache", "tech": "Redis", "description": "Caching layer", "config_hints": {}},
                {"name": "Kafka", "type": "queue", "tech": "Kafka", "description": "Event streaming", "config_hints": {}},
            ]
        else:
            components = [
                {"name": "Web Application", "type": "api", "tech": "React/Vue", "description": "Frontend application", "config_hints": {}},
                {"name": "API Server", "type": "service", "tech": "FastAPI/Express", "description": "Backend API", "config_hints": {}},
                {"name": "Database", "type": "database", "tech": "PostgreSQL", "description": "Primary database", "config_hints": {}},
                {"name": "Cache", "type": "cache", "tech": "Redis", "description": "Caching layer", "config_hints": {}},
            ]

    return components