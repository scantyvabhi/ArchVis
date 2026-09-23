import json
from typing import Dict, Any, List, Optional
import uuid

from .base import BaseAgent, AgentRole, AgentContext, AgentResult, AgentStatus, ToolResult


class DiagramBuilderAgent(BaseAgent):
    def __init__(self, model_client, sandbox, tools: Dict, config: Dict):
        super().__init__(AgentRole.DIAGRAM_BUILDER, model_client, sandbox, tools, config)

    def get_system_prompt(self) -> str:
        return """You are the **Diagram Builder Agent** for ArchVis AI.

Your role is to:
1. Convert architectural analysis into React Flow compatible diagram specifications
2. Generate nodes with proper positions, categories, and configuration
3. Create edges representing data flows with protocols and animations
4. Apply semantic zoom levels (macro/normal/micro) with appropriate detail
5. Generate both HLD (High-Level Design) and LLD (Low-Level Design) views
6. Ensure diagram matches the validated architecture from Architecture Analyst
7. Export diagram as JSON spec for frontend rendering

You work in a SANDBOXED environment - you can only use the provided tools.
Your output must be valid React Flow JSON that the frontend can directly render.

Key outputs:
- nodes: Array of ArchitectureNode objects with id, type, position, data
- edges: Array of ArchitectureEdge objects with id, source, target, label, data
- viewport: Suggested initial viewport (x, y, zoom)
- metadata: Diagram metadata (title, description, mode, version)
- hld_view: Simplified HLD diagram (macro view)
- lld_view: Detailed LLD diagram (micro view)"""

    def get_available_tools(self) -> List[str]:
        return [
            "generate_hld_diagram",
            "generate_lld_diagram",
            "layout_components",
            "apply_semantic_zoom",
            "validate_diagram",
            "export_diagram_spec",
        ]

    async def execute(self, context: AgentContext) -> AgentResult:
        import time
        start_time = time.time()

        self.status = AgentStatus.RUNNING
        reasoning_parts = []
        tool_calls = []

        try:
            # Get analysis from previous agents
            architecture_analysis = context.shared_memory.get("architecture_analysis", {})
            repo_analysis = context.shared_memory.get("repo_analysis", {})
            canvas_state = context.canvas_state
            mode = context.mode
            user_prompt = context.user_prompt

            reasoning_parts.append(f"Building diagram for: {user_prompt[:100]}...")
            reasoning_parts.append(f"Mode: {mode}, Has architecture analysis: {bool(architecture_analysis)}")

            # Get TypeSafe validation from Architecture Analyst
            typesafe_validation = context.shared_memory.get("typesafe_validation", {})
            if typesafe_validation:
                reasoning_parts.append(f"TypeSafe validation available: {typesafe_validation.get('summary', 'N/A')}")

            # Generate HLD diagram
            hld_result = await self._call_tool("generate_hld_diagram",
                architecture_analysis=architecture_analysis, repo_analysis=repo_analysis, mode=mode)
            tool_calls.append({"tool": "generate_hld_diagram", "result": hld_result.success})

            # Generate LLD diagram
            lld_result = await self._call_tool("generate_lld_diagram",
                architecture_analysis=architecture_analysis, repo_analysis=repo_analysis, mode=mode)
            tool_calls.append({"tool": "generate_lld_diagram", "result": lld_result.success})

            # Layout components
            layout_result = await self._call_tool("layout_components",
                nodes=hld_result.data.get("nodes", []) if hld_result.data else [],
                edges=hld_result.data.get("edges", []) if hld_result.data else [])
            tool_calls.append({"tool": "layout_components", "result": layout_result.success})

            # Apply semantic zoom
            zoom_result = await self._call_tool("apply_semantic_zoom",
                hld_nodes=hld_result.data.get("nodes", []) if hld_result.data else [],
                lld_nodes=lld_result.data.get("nodes", []) if lld_result.data else [],
                mode=mode)
            tool_calls.append({"tool": "apply_semantic_zoom", "result": zoom_result.success})

            # Validate diagram
            validate_result = await self._call_tool("validate_diagram",
                nodes=layout_result.data.get("nodes", []) if layout_result.data else [],
                edges=layout_result.data.get("edges", []) if layout_result.data else [])
            tool_calls.append({"tool": "validate_diagram", "result": validate_result.success})

            # Export final spec
            export_result = await self._call_tool("export_diagram_spec",
                hld_data=hld_result.data, lld_data=lld_result.data,
                layout_data=layout_result.data, zoom_data=zoom_result.data,
                architecture_analysis=architecture_analysis, mode=mode, user_prompt=user_prompt)
            tool_calls.append({"tool": "export_diagram_spec", "result": export_result.success})

            final_diagram = export_result.data

            # Add TypeSafe validation to diagram metadata
            if typesafe_validation:
                final_diagram.setdefault("metadata", {})["typesafe_validation"] = typesafe_validation

            context.shared_memory["diagram_spec"] = final_diagram
            context.agent_outputs[self.role.value] = final_diagram

            reasoning_parts.append(f"Generated diagram: {len(final_diagram.get('nodes', []))} nodes, {len(final_diagram.get('edges', []))} edges")
            reasoning_parts.append(f"HLD view: {bool(final_diagram.get('hld_view'))}, LLD view: {bool(final_diagram.get('lld_view'))}")

            return AgentResult(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output=final_diagram,
                reasoning="\n".join(reasoning_parts),
                confidence=0.95,
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
CATEGORY_COLORS = {
    "api": "#3B82F6",       # Blue
    "gateway": "#8B5CF6",   # Purple
    "service": "#10B981",   # Green
    "cache": "#F59E0B",     # Amber
    "database": "#EF4444",  # Red
    "queue": "#EC4899",     # Pink
    "storage": "#6B7280",   # Gray
}

CATEGORY_ICONS = {
    "api": "Globe",
    "gateway": "Shield",
    "service": "Server",
    "cache": "Zap",
    "database": "Database",
    "queue": "MessageSquare",
    "storage": "HardDrive",
}


def generate_node_id(prefix: str = "node") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# Smart connection logic - defines standard architectural patterns
CONNECTION_RULES = {
    # Source type -> list of target types it typically connects to
    "api": ["gateway", "service"],
    "gateway": ["service", "cache", "queue", "database"],
    "service": ["database", "cache", "queue", "service", "storage"],
    "cache": ["database"],
    "queue": ["service", "database", "storage"],
    "storage": [],
    "database": [],
    "load_balancer": ["gateway", "service", "api"],
    "cdn": ["api", "storage"],
}

# Protocol mapping for connections
CONNECTION_PROTOCOLS = {
    ("api", "gateway"): "HTTPS",
    ("api", "service"): "HTTPS/REST",
    ("api", "load_balancer"): "HTTPS",
    ("gateway", "service"): "gRPC",
    ("gateway", "cache"): "TCP/Redis",
    ("gateway", "queue"): "AMQP/Kafka",
    ("gateway", "database"): "SQL",
    ("gateway", "load_balancer"): "HTTP",
    ("service", "database"): "SQL",
    ("service", "cache"): "TCP/Redis",
    ("service", "queue"): "Kafka/AMQP",
    ("service", "service"): "gRPC/REST",
    ("service", "storage"): "S3/API",
    ("cache", "database"): "SQL",
    ("queue", "service"): "Kafka/AMQP",
    ("queue", "database"): "SQL",
    ("queue", "storage"): "S3/API",
    ("load_balancer", "gateway"): "HTTP",
    ("load_balancer", "service"): "HTTP/REST",
    ("load_balancer", "api"): "HTTPS",
    ("cdn", "api"): "HTTPS",
    ("cdn", "storage"): "HTTPS",
}

# Traffic estimation rules
TRAFFIC_MULTIPLIERS = {
    ("api", "gateway"): 1.0,
    ("gateway", "service"): 0.8,
    ("service", "database"): 0.6,
    ("service", "cache"): 0.4,
    ("service", "queue"): 0.3,
    ("gateway", "queue"): 0.2,
}


def infer_connections(components: List[Dict], existing_flows: List[Dict] = None) -> List[Dict]:
    """
    Automatically infer data flows between components based on architectural patterns.
    Creates edges where they don't exist based on standard component relationships.
    """
    existing_flows = existing_flows or []
    existing_pairs = {(f.get("from"), f.get("to")) for f in existing_flows}
    
    # Group components by type
    components_by_type = {}
    for comp in components:
        comp_type = comp.get("type", "service")
        if comp_type not in components_by_type:
            components_by_type[comp_type] = []
        components_by_type[comp_type].append(comp)
    
    inferred_flows = []
    
    # For each source type, connect to target types
    for source_type, target_types in CONNECTION_RULES.items():
        source_components = components_by_type.get(source_type, [])
        if not source_components:
            continue
            
        for target_type in target_types:
            target_components = components_by_type.get(target_type, [])
            if not target_components:
                continue
            
            # Connect each source to relevant targets
            for source_comp in source_components:
                source_name = source_comp.get("name", source_type.title())
                
                # Smart targeting: prefer first target, or distribute
                for i, target_comp in enumerate(target_components):
                    target_name = target_comp.get("name", target_type.title())
                    
                    # Skip if already exists
                    if (source_name, target_name) in existing_pairs:
                        continue
                    
                    # Determine protocol
                    protocol = CONNECTION_PROTOCOLS.get((source_type, target_type), "HTTP/REST")
                    
                    # Estimate traffic based on component configs
                    source_rps = source_comp.get("config", {}).get("rps", 1000)
                    target_rps = target_comp.get("config", {}).get("rps", 1000)
                    traffic_rps = min(source_rps, target_rps)
                    
                    inferred_flows.append({
                        "from": source_name,
                        "to": target_name,
                        "protocol": protocol,
                        "traffic_estimate_rps": traffic_rps,
                        "description": f"Auto-inferred: {source_name} -> {target_name}",
                        "auto_inferred": True
                    })
    
    return inferred_flows


async def generate_hld_diagram(architecture_analysis: Dict, repo_analysis: Dict, mode: str) -> Dict[str, Any]:
    """Generate High-Level Design diagram - simplified, architectural overview"""
    validated = architecture_analysis.get("validated_architecture", {})
    components = validated.get("components", [])
    data_flows = validated.get("data_flows", [])

    # If no validated architecture, fall back to repo analysis
    if not components:
        components = repo_analysis.get("components", [])
    if not data_flows:
        data_flows = repo_analysis.get("data_flows", [])

    nodes = []
    edges = []

    # Position nodes in a logical flow (left to right)
    layer_positions = {
        "api": (100, 200),
        "gateway": (300, 200),
        "service": (550, 200),
        "cache": (800, 100),
        "database": (800, 300),
        "queue": (550, 400),
        "storage": (1050, 200),
    }

    layer_counters = {k: 0 for k in layer_positions}

    for comp in components:
        comp_type = comp.get("type", "service")
        base_x, base_y = layer_positions.get(comp_type, (550, 200))
        offset = layer_counters.get(comp_type, 0) * 120
        layer_counters[comp_type] = layer_counters.get(comp_type, 0) + 1

        node_id = generate_node_id(comp_type)

        # HLD nodes have simplified data
        node_data = {
            "label": comp.get("name", comp_type.title()),
            "category": comp_type,
            "tech": comp.get("tech", "TBD"),
            "latency": comp.get("config", {}).get("latency", 20),
            "rps": comp.get("config", {}).get("rps", 1000),
            "capacity": comp.get("config", {}).get("capacity", 5000),
            "failureRate": comp.get("config", {}).get("failureRate", 0.1),
            "replication": comp.get("config", {}).get("replication", "N/A"),
            "description": comp.get("description", ""),
            "explanation": comp.get("explanation", f"{comp_type.title()} component using {comp.get('tech', 'TBD')}"),
            "status": "healthy",
            # HLD-specific: simplified view
            "zoom_level": "macro",
            "show_metrics": False,
            "show_config": False,
        }

        nodes.append({
            "id": node_id,
            "type": "architectureNode",
            "position": {"x": base_x, "y": base_y + offset},
            "data": node_data,
        })

    # Create edges from data flows + inferred connections
    node_name_to_id = {n["data"]["label"]: n["id"] for n in nodes}

    # Combine explicit flows with inferred connections
    all_flows = list(data_flows)
    inferred_flows = infer_connections(components, data_flows)
    all_flows.extend(inferred_flows)

    for i, flow in enumerate(all_flows):
        source_name = flow.get("from", "")
        target_name = flow.get("to", "")
        source_id = node_name_to_id.get(source_name)
        target_id = node_name_to_id.get(target_name)

        if source_id and target_id:
            is_inferred = flow.get("auto_inferred", False)
            edges.append({
                "id": f"edge-{i}",
                "source": source_id,
                "target": target_id,
                "label": flow.get("protocol", "HTTP/REST"),
                "animated": True,
                "data": {
                    "protocol": flow.get("protocol", "HTTP/REST"),
                    "trafficRps": flow.get("traffic_estimate_rps", 1000),
                    "latency": flow.get("latency", 10),
                    "auto_inferred": is_inferred,
                },
            })

    return {"nodes": nodes, "edges": edges}


async def generate_lld_diagram(architecture_analysis: Dict, repo_analysis: Dict, mode: str) -> Dict[str, Any]:
    """Generate Low-Level Design diagram - detailed, implementation-ready"""
    validated = architecture_analysis.get("validated_architecture", {})
    components = validated.get("components", [])
    data_flows = validated.get("data_flows", [])

    lld_spec = architecture_analysis.get("lld_spec", {})
    lld_components = lld_spec.get("component_details", [])

    nodes = []
    edges = []

    # More detailed positioning for LLD
    layer_positions = {
        "api": (50, 150),
        "gateway": (250, 150),
        "service": (500, 150),
        "cache": (750, 50),
        "database": (750, 250),
        "queue": (500, 450),
        "storage": (1000, 150),
    }

    layer_counters = {k: 0 for k in layer_positions}

    # Merge validated components with LLD details
    lld_by_name = {c.get("name"): c for c in lld_components}

    for comp in components:
        comp_type = comp.get("type", "service")
        base_x, base_y = layer_positions.get(comp_type, (500, 150))
        offset = layer_counters.get(comp_type, 0) * 150
        layer_counters[comp_type] = layer_counters.get(comp_type, 0) + 1

        node_id = generate_node_id(comp_type)
        lld_detail = lld_by_name.get(comp.get("name"), {})

        # LLD nodes have full configuration detail
        config = comp.get("config", {})
        lld_config = lld_detail.get("configuration", {})

        node_data = {
            "label": comp.get("name", comp_type.title()),
            "category": comp_type,
            "tech": comp.get("tech", "TBD"),
            "latency": config.get("latency", lld_config.get("latency_ms", 20)),
            "rps": config.get("rps", lld_config.get("target_rps", 1000)),
            "capacity": config.get("capacity", lld_config.get("max_capacity_rps", 5000)),
            "failureRate": config.get("failureRate", lld_config.get("failure_rate_percent", 0.1)),
            "replication": config.get("replication", lld_config.get("replication", "N/A")),
            "description": comp.get("description", ""),
            "explanation": lld_detail.get("runbook", comp.get("explanation", "")),
            "status": "healthy",
            # LLD-specific: full detail
            "zoom_level": "micro",
            "show_metrics": True,
            "show_config": True,
            # Extended LLD fields
            "api_contract": lld_detail.get("api_contract", ""),
            "data_model": lld_detail.get("data_model", ""),
            "scaling_strategy": lld_detail.get("scaling_strategy", ""),
            "failure_modes": lld_detail.get("failure_modes", []),
            "runbook": lld_detail.get("runbook", ""),
        }

        nodes.append({
            "id": node_id,
            "type": "architectureNode",
            "position": {"x": base_x, "y": base_y + offset},
            "data": node_data,
        })

    # Create detailed edges + inferred connections
    node_name_to_id = {n["data"]["label"]: n["id"] for n in nodes}

    # Combine explicit flows with inferred connections for LLD too
    all_flows = list(data_flows)
    inferred_flows = infer_connections(components, data_flows)
    all_flows.extend(inferred_flows)

    for i, flow in enumerate(all_flows):
        source_name = flow.get("from", "")
        target_name = flow.get("to", "")
        source_id = node_name_to_id.get(source_name)
        target_id = node_name_to_id.get(target_name)

        if source_id and target_id:
            is_inferred = flow.get("auto_inferred", False)
            edges.append({
                "id": f"edge-lld-{i}",
                "source": source_id,
                "target": target_id,
                "label": f"{flow.get('protocol', 'HTTP/REST')} • {flow.get('traffic_estimate_rps', 1000)} RPS",
                "animated": True,
                "data": {
                    "protocol": flow.get("protocol", "HTTP/REST"),
                    "trafficRps": flow.get("traffic_estimate_rps", 1000),
                    "latency": flow.get("latency", 10),
                    "description": flow.get("description", ""),
                    "auto_inferred": is_inferred,
                },
            })

    return {"nodes": nodes, "edges": edges}


async def layout_components(nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
    """Apply Dagre-like layout algorithm for clean diagram arrangement"""
    if not nodes:
        return {"nodes": nodes, "edges": edges}

    # Simple topological layout (left-to-right)
    # Group by category
    category_order = ["api", "gateway", "service", "queue", "cache", "database", "storage"]
    category_layers = {cat: [] for cat in category_order}

    for node in nodes:
        cat = node.get("data", {}).get("category", "service")
        if cat in category_layers:
            category_layers[cat].append(node)
        else:
            category_layers["service"].append(node)

    # Position each layer
    x_positions = {cat: 100 + i * 280 for i, cat in enumerate(category_order)}
    y_spacing = 140

    positioned_nodes = []
    for cat in category_order:
        layer_nodes = category_layers[cat]
        for i, node in enumerate(layer_nodes):
            node_copy = dict(node)
            node_copy["position"] = {
                "x": x_positions[cat],
                "y": 100 + i * y_spacing
            }
            positioned_nodes.append(node_copy)

    # Adjust edges to avoid overlap (simple approach)
    positioned_edges = edges

    return {"nodes": positioned_nodes, "edges": positioned_edges}


async def apply_semantic_zoom(hld_nodes: List[Dict], lld_nodes: List[Dict], mode: str) -> Dict[str, Any]:
    """Apply semantic zoom configurations for different view levels"""
    
    # Macro view (< 0.5x): Compact cards with badges
    macro_nodes = []
    for node in hld_nodes:
        data = node.get("data", {})
        macro_nodes.append({
            **node,
            "data": {
                **data,
                "zoom_level": "macro",
                "show_metrics": False,
                "show_config": False,
                "badge_only": True,
                "compact_label": data.get("label", "")[:15] + "…" if len(data.get("label", "")) > 15 else data.get("label", ""),
            }
        })

    # Normal view (0.5x - 0.8x): Standard cards with gauges
    normal_nodes = []
    for node in hld_nodes:
        data = node.get("data", {})
        normal_nodes.append({
            **node,
            "data": {
                **data,
                "zoom_level": "normal",
                "show_metrics": True,
                "show_config": False,
                "badge_only": False,
            }
        })

    # Micro view (> 0.8x): Full detail with config specs
    micro_nodes = []
    lld_by_label = {n.get("data", {}).get("label"): n for n in lld_nodes}
    
    for node in hld_nodes:
        data = node.get("data", {})
        label = data.get("label", "")
        lld_node = lld_by_label.get(label, {})
        lld_data = lld_node.get("data", {})
        
        micro_nodes.append({
            **node,
            "data": {
                **data,
                **lld_data,  # Merge LLD details
                "zoom_level": "micro",
                "show_metrics": True,
                "show_config": True,
                "badge_only": False,
            }
        })

    return {
        "macro_view": {"nodes": macro_nodes},
        "normal_view": {"nodes": normal_nodes},
        "micro_view": {"nodes": micro_nodes},
    }


async def validate_diagram(nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
    """Validate diagram structure and connectivity"""
    issues = []
    warnings = []

    node_ids = {n.get("id") for n in nodes}

    # Check for orphan nodes
    connected_nodes = set()
    for edge in edges:
        connected_nodes.add(edge.get("source"))
        connected_nodes.add(edge.get("target"))

    for node_id in node_ids:
        if node_id not in connected_nodes:
            warnings.append(f"Node {node_id} is not connected to any edge")

    # Check for edges referencing non-existent nodes
    for edge in edges:
        if edge.get("source") not in node_ids:
            issues.append(f"Edge {edge.get('id')} references non-existent source: {edge.get('source')}")
        if edge.get("target") not in node_ids:
            issues.append(f"Edge {edge.get('id')} references non-existent target: {edge.get('target')}")

    # Check for duplicate IDs
    seen = set()
    for node in nodes:
        if node.get("id") in seen:
            issues.append(f"Duplicate node ID: {node.get('id')}")
        seen.add(node.get("id"))

    seen.clear()
    for edge in edges:
        if edge.get("id") in seen:
            issues.append(f"Duplicate edge ID: {edge.get('id')}")
        seen.add(edge.get("id"))

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "connected_components": len(node_ids - connected_nodes) if node_ids else 0,
    }


async def export_diagram_spec(
    hld_data: Dict, lld_data: Dict, layout_data: Dict, zoom_data: Dict,
    architecture_analysis: Dict, mode: str, user_prompt: str
) -> Dict[str, Any]:
    """Export final diagram specification for frontend"""
    
    # Handle None inputs
    if architecture_analysis is None:
        architecture_analysis = {}
    if hld_data is None:
        hld_data = {}
    if lld_data is None:
        lld_data = {}
    if layout_data is None:
        layout_data = {}
    if zoom_data is None:
        zoom_data = {}
    
    hld_nodes = layout_data.get("nodes", hld_data.get("nodes", [])) if layout_data else hld_data.get("nodes", [])
    hld_edges = layout_data.get("edges", hld_data.get("edges", [])) if layout_data else hld_data.get("edges", [])
    lld_nodes = lld_data.get("nodes", [])
    lld_edges = lld_data.get("edges", [])

    macro_view = zoom_data.get("macro_view", {}).get("nodes", [])
    normal_view = zoom_data.get("normal_view", {}).get("nodes", [])
    micro_view = zoom_data.get("micro_view", {}).get("nodes", [])

    # Build summary
    validated = architecture_analysis.get("validated_architecture", {})
    bottlenecks = architecture_analysis.get("bottlenecks", [])
    recommendations = architecture_analysis.get("recommendations", [])

    return {
        "nodes": hld_nodes,
        "edges": hld_edges,
        "viewport": {"x": 0, "y": 0, "zoom": 0.7},
        "metadata": {
            "title": f"Architecture: {user_prompt[:80]}",
            "description": architecture_analysis.get("validated_architecture", {}).get("overview", ""),
            "mode": mode,
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00Z",
        },
        "summary": architecture_analysis.get("validated_architecture", {}).get("overview", ""),
        "recommendations": [r.get("action", "") for r in recommendations if r.get("action")],
        # Semantic zoom views
        "hld_view": {
            "nodes": macro_view,
            "edges": hld_edges,
            "description": "High-Level Design - Architectural overview with component badges",
        },
        "lld_view": {
            "nodes": micro_view,
            "edges": lld_edges,
            "description": "Low-Level Design - Detailed implementation specifications",
        },
        "semantic_zoom": {
            "macro": {"nodes": macro_view, "zoom_range": [0.1, 0.5]},
            "normal": {"nodes": normal_view, "zoom_range": [0.5, 0.8]},
            "micro": {"nodes": micro_view, "zoom_range": [0.8, 3.0]},
        },
        "analysis": {
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "hld_spec": architecture_analysis.get("hld_spec", {}),
            "lld_spec": architecture_analysis.get("lld_spec", {}),
            "consistency_check": architecture_analysis.get("consistency_check", {}),
        },
    }