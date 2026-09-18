import os
import json
import re
from typing import Dict, Any, List, Optional
import httpx

try:
    import google.generativeai as genai
    GENAI_INSTALLED = True
except ImportError:
    GENAI_INSTALLED = False

class AIAgent:
    """ArchVis AI system design architect using Gemini 1.5 Flash with fallback intelligence."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-1.5-flash"
        if self.api_key and GENAI_INSTALLED:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to configure genai: {e}")

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    async def generate_architecture(self, prompt: str, mode: str = "pro") -> Dict[str, Any]:
        """Generates nodes and edges JSON compatible with React Flow."""
        if self.is_available():
            try:
                return await self._call_gemini_architecture(prompt, mode)
            except Exception as e:
                print(f"Gemini API call failed, falling back to heuristic synthesizer: {e}")

        return self._generate_fallback_architecture(prompt, mode)

    async def parse_repo_architecture(self, repo_context: Dict[str, Any], mode: str = "pro") -> Dict[str, Any]:
        """Generates architecture from extracted repo context."""
        repo_name = repo_context.get("repo", "Repository")
        detected_tech = ", ".join(repo_context.get("detected_tech", []))
        readme = repo_context.get("readme_excerpt", "")[:1500]

        prompt = (
            f"Reverse-engineer an end-to-end system architecture diagram for the GitHub repository '{repo_name}'.\n"
            f"Detected Technologies: {detected_tech}\n"
            f"README Excerpt:\n{readme}\n"
            f"Target Mode: {mode.upper()}."
        )

        arch = await self.generate_architecture(prompt, mode)
        arch["repo_info"] = {
            "repo_url": repo_context.get("repo_url", ""),
            "detected_tech": repo_context.get("detected_tech", []),
            "primary_language": repo_context.get("detected_tech", [None])[0],
        }
        return arch

    async def chat(self, message: str, canvas_state: Dict[str, Any], mode: str = "pro") -> str:
        """Contextual Q&A based on the current canvas diagram state."""
        nodes = canvas_state.get("nodes", [])
        edges = canvas_state.get("edges", [])

        if self.is_available():
            try:
                return await self._call_gemini_chat(message, nodes, edges, mode)
            except Exception as e:
                print(f"Gemini Chat call failed: {e}")

        return self._generate_fallback_chat(message, nodes, edges, mode)

    # -------------------------------------------------------------
    # Gemini API Implementation
    # -------------------------------------------------------------
    async def _call_gemini_architecture(self, prompt: str, mode: str) -> Dict[str, Any]:
        system_instructions = (
            "You are an expert Principal Cloud Architect and System Design Interviewer.\n"
            "Generate a complete, high-fidelity system design graph in strict JSON format.\n"
            "Nodes must follow this schema:\n"
            "{\n"
            '  "nodes": [\n'
            '    {\n'
            '      "id": "node-1",\n'
            '      "type": "architectureNode",\n'
            '      "position": { "x": 100, "y": 200 },\n'
            '      "data": {\n'
            '        "label": "Component Name",\n'
            '        "category": "api" | "gateway" | "service" | "cache" | "database" | "queue" | "storage",\n'
            '        "tech": "e.g. FastAPI / Redis / Kafka / Postgres",\n'
            '        "latency": 20,\n'
            '        "rps": 2000,\n'
            '        "capacity": 5000,\n'
            '        "failureRate": 0.1,\n'
            '        "replication": "e.g. Primary + 2 Replicas",\n'
            '        "description": "Short summary of role",\n'
            '        "explanation": "Why this component was chosen (crucial for Learner Mode)"\n'
            "      }\n"
            "    }\n"
            "  ],\n"
            '  "edges": [\n'
            '    {\n'
            '      "id": "e1",\n'
            '      "source": "node-1",\n'
            '      "target": "node-2",\n'
            '      "label": "Protocol / Action",\n'
            '      "animated": true,\n'
            '      "data": { "protocol": "HTTP/REST" | "gRPC" | "Kafka Topic" | "SQL" | "TCP" }\n'
            "    }\n"
            "  ],\n"
            '  "summary": "Brief executive architecture summary",\n'
            '  "recommendations": ["Recommendation 1", "Recommendation 2"]\n'
            "}\n"
        )

        mode_instruction = (
            "In LEARNER MODE: Include intuitive, educational explanations for each node explaining *what* it is and *why* it was selected.\n"
            if mode == "learner"
            else "In PROFESSIONAL MODE: Design complete enterprise HLD/LLD with load balancing, caching, read-replicas, and queue decoupling.\n"
        )

        full_prompt = f"{system_instructions}\n{mode_instruction}\nUSER REQUEST: {prompt}\n\nRespond ONLY with valid JSON."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            res_json = res.json()

        text = res_json["candidates"][0]["content"]["parts"][0]["text"]
        return self._clean_and_parse_json(text)

    async def _call_gemini_chat(self, message: str, nodes: List[Any], edges: List[Any], mode: str) -> str:
        canvas_summary = f"Current canvas contains {len(nodes)} nodes:\n"
        for n in nodes:
            nd = n.get("data", {})
            canvas_summary += f"- [{n.get('id')}] {nd.get('label')} ({nd.get('tech')}): capacity={nd.get('capacity')} rps, latency={nd.get('latency')}ms\n"

        canvas_summary += f"\nEdges ({len(edges)}):\n"
        for e in edges:
            canvas_summary += f"- {e.get('source')} -> {e.get('target')} [{e.get('label') or ''}]\n"

        prompt = (
            f"You are the ArchVis AI assistant. The user is asking a system design question.\n"
            f"Active Canvas State:\n{canvas_summary}\n\n"
            f"Mode: {mode.upper()}\n"
            f"User Question: {message}\n\n"
            f"Provide a concise, highly insightful system design response. Reference specific components and bottlenecks from the active canvas."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            res_json = res.json()

        return res_json["candidates"][0]["content"]["parts"][0]["text"]

    def _clean_and_parse_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        parsed = json.loads(cleaned.strip())
        if "nodes" not in parsed or "edges" not in parsed:
            raise ValueError("Invalid architecture structure from AI")
        return parsed

    # -------------------------------------------------------------
    # Intelligent Heuristic Fallback (Zero-crash resilience)
    # -------------------------------------------------------------
    def _generate_fallback_architecture(self, prompt: str, mode: str) -> Dict[str, Any]:
        p = prompt.lower()

        if "video" in p or "stream" in p or "youtube" in p or "netflix" in p:
            nodes = [
                {
                    "id": "node-client",
                    "type": "architectureNode",
                    "position": {"x": 50, "y": 200},
                    "data": {
                        "label": "Video Clients",
                        "category": "api",
                        "tech": "HLS / Web Player",
                        "latency": 50,
                        "rps": 10000,
                        "capacity": 50000,
                        "failureRate": 0.2,
                        "replication": "Global Clients",
                        "description": "Web browsers and Smart TVs playing video chunks.",
                        "explanation": "Entry point: Requests chunk playlists and media files.",
                    },
                },
                {
                    "id": "node-cdn",
                    "type": "architectureNode",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "label": "Edge CDN",
                        "category": "gateway",
                        "tech": "Cloudflare / Akamai",
                        "latency": 8,
                        "rps": 8500,
                        "capacity": 40000,
                        "failureRate": 0.02,
                        "replication": "Global Edge PoPs",
                        "description": "Caches video segments at the edge closest to viewers.",
                        "explanation": "Absorbs 90% of video bandwidth without hitting origins.",
                    },
                },
                {
                    "id": "node-gateway",
                    "type": "architectureNode",
                    "position": {"x": 300, "y": 300},
                    "data": {
                        "label": "API Gateway",
                        "category": "gateway",
                        "tech": "Kong / Envoy",
                        "latency": 6,
                        "rps": 2000,
                        "capacity": 15000,
                        "failureRate": 0.05,
                        "replication": "Active-Active Cluster",
                        "description": "Authenticates requests and routes metadata vs transcoding.",
                        "explanation": "Single secure ingress managing rate limits and auth.",
                    },
                },
                {
                    "id": "node-transcode-queue",
                    "type": "architectureNode",
                    "position": {"x": 580, "y": 180},
                    "data": {
                        "label": "Transcoding Queue",
                        "category": "queue",
                        "tech": "Apache Kafka / AWS SQS",
                        "latency": 12,
                        "rps": 500,
                        "capacity": 10000,
                        "failureRate": 0.05,
                        "replication": "3x Replication Factor",
                        "description": "Buffers video encoding jobs asynchronously.",
                        "explanation": "Protects CPU encoders from being overwhelmed during upload spikes.",
                    },
                },
                {
                    "id": "node-transcoder",
                    "type": "architectureNode",
                    "position": {"x": 860, "y": 180},
                    "data": {
                        "label": "Transcoder Farm",
                        "category": "service",
                        "tech": "FFmpeg GPU Cluster",
                        "latency": 350,
                        "rps": 500,
                        "capacity": 1000,
                        "failureRate": 1.0,
                        "replication": "Auto-scaling GPU Pods",
                        "description": "Encodes master video into 1080p, 720p, 480p bitrates.",
                        "explanation": "Compute-heavy tier producing adaptive bitrate streams.",
                    },
                },
                {
                    "id": "node-storage",
                    "type": "architectureNode",
                    "position": {"x": 1140, "y": 240},
                    "data": {
                        "label": "Blob Storage",
                        "category": "storage",
                        "tech": "Amazon S3",
                        "latency": 30,
                        "rps": 1200,
                        "capacity": 20000,
                        "failureRate": 0.01,
                        "replication": "11 9s Durability across 3 AZs",
                        "description": "Stores raw uploads and transcoded chunk files.",
                        "explanation": "Infinite durability origin storage serving cache misses to CDN.",
                    },
                },
            ]
            edges = [
                {"id": "e1", "source": "node-client", "target": "node-cdn", "label": "Stream Chunks", "animated": True, "data": {"protocol": "HTTP/REST"}},
                {"id": "e2", "source": "node-client", "target": "node-gateway", "label": "API / Upload", "animated": True, "data": {"protocol": "HTTP/REST"}},
                {"id": "e3", "source": "node-cdn", "target": "node-storage", "label": "Origin Miss", "animated": True, "data": {"protocol": "HTTP/REST"}},
                {"id": "e4", "source": "node-gateway", "target": "node-transcode-queue", "label": "Queue Video", "animated": True, "data": {"protocol": "Kafka Topic"}},
                {"id": "e5", "source": "node-transcode-queue", "target": "node-transcoder", "label": "Consume Job", "animated": True, "data": {"protocol": "TCP"}},
                {"id": "e6", "source": "node-transcoder", "target": "node-storage", "label": "Write Segments", "animated": True, "data": {"protocol": "HTTP/REST"}},
            ]
            summary = "Designed a scalable video streaming architecture with edge CDN caching, asynchronous worker queueing, and distributed S3 storage."
            recommendations = [
                "Use adaptive bitrate streaming (HLS/DASH) to dynamically adjust quality based on viewer network conditions.",
                "Ensure CDN cache hit ratio remains above 90% to avoid overloading object storage origins.",
            ]
        elif "chat" in p or "messaging" in p or "realtime" in p or "whatsapp" in p:
            nodes = [
                {
                    "id": "c-client",
                    "type": "architectureNode",
                    "position": {"x": 50, "y": 200},
                    "data": {
                        "label": "Chat Mobile & Web",
                        "category": "api",
                        "tech": "React Native & WebSockets",
                        "latency": 45,
                        "rps": 5000,
                        "capacity": 25000,
                        "failureRate": 0.1,
                        "replication": "Multi-Client",
                        "description": "Persistent duplex connection for instant messaging.",
                        "explanation": "Connects over WebSocket for two-way event push.",
                    },
                },
                {
                    "id": "c-ws-gateway",
                    "type": "architectureNode",
                    "position": {"x": 320, "y": 200},
                    "data": {
                        "label": "WebSocket Gateway",
                        "category": "gateway",
                        "tech": "Go / Gorilla WS Cluster",
                        "latency": 5,
                        "rps": 5000,
                        "capacity": 15000,
                        "failureRate": 0.05,
                        "replication": "Stateful Connection Fleet",
                        "description": "Maintains 500k+ concurrent open TCP socket connections.",
                        "explanation": "Terminates TLS and manages heartbeat keep-alives.",
                    },
                },
                {
                    "id": "c-pubsub",
                    "type": "architectureNode",
                    "position": {"x": 600, "y": 140},
                    "data": {
                        "label": "Redis Pub/Sub",
                        "category": "cache",
                        "tech": "Redis 7.2 Cluster",
                        "latency": 2,
                        "rps": 4800,
                        "capacity": 30000,
                        "failureRate": 0.02,
                        "replication": "Primary-Replica with Sentinel",
                        "description": "Distributes messages to the specific gateway holding user connection.",
                        "explanation": "Sub-millisecond fanout routing messages across distributed nodes.",
                    },
                },
                {
                    "id": "c-db",
                    "type": "architectureNode",
                    "position": {"x": 600, "y": 300},
                    "data": {
                        "label": "Message History Store",
                        "category": "database",
                        "tech": "Cassandra / ScyllaDB",
                        "latency": 14,
                        "rps": 3000,
                        "capacity": 8000,
                        "failureRate": 0.1,
                        "replication": "Peer-to-Peer RF=3",
                        "description": "High-write throughput persistent chat log storage.",
                        "explanation": "Optimized for append-only sequential writes ordered by timestamp.",
                    },
                },
            ]
            edges = [
                {"id": "ce1", "source": "c-client", "target": "c-ws-gateway", "label": "WebSocket WSS", "animated": True, "data": {"protocol": "WebSocket"}},
                {"id": "ce2", "source": "c-ws-gateway", "target": "c-pubsub", "label": "Publish Message", "animated": True, "data": {"protocol": "TCP"}},
                {"id": "ce3", "source": "c-ws-gateway", "target": "c-db", "label": "Archive Message", "animated": True, "data": {"protocol": "TCP"}},
            ]
            summary = "Real-time bidirectional chat engine featuring stateful WebSocket gateway cluster, in-memory Redis Pub/Sub routing, and NoSQL message history."
            recommendations = [
                "Implement connection stickiness and connection draining during deployments.",
                "Store ephemeral presence (online/offline) in Redis with automatic TTL key expiration.",
            ]
        else:
            # Default Scalable Microservices Architecture
            nodes = [
                {
                    "id": "app-client",
                    "type": "architectureNode",
                    "position": {"x": 50, "y": 200},
                    "data": {
                        "label": "Client Applications",
                        "category": "api",
                        "tech": "Web & Mobile Clients",
                        "latency": 60,
                        "rps": 3500,
                        "capacity": 20000,
                        "failureRate": 0.1,
                        "replication": "Global Users",
                        "description": "User requests initiating API and business interactions.",
                        "explanation": "Initiates user operations across HTTP/REST and WebSockets.",
                    },
                },
                {
                    "id": "app-gateway",
                    "type": "architectureNode",
                    "position": {"x": 300, "y": 200},
                    "data": {
                        "label": "Load Balancer & Gateway",
                        "category": "gateway",
                        "tech": "NGINX / Envoy Proxy",
                        "latency": 5,
                        "rps": 3500,
                        "capacity": 15000,
                        "failureRate": 0.05,
                        "replication": "Active-Passive Redundancy",
                        "description": "Traffic distribution, rate limiting, and SSL termination.",
                        "explanation": "Protects internal microservices from direct public exposure.",
                    },
                },
                {
                    "id": "app-service",
                    "type": "architectureNode",
                    "position": {"x": 580, "y": 200},
                    "data": {
                        "label": "Core API Service",
                        "category": "service",
                        "tech": "FastAPI / Python",
                        "latency": 25,
                        "rps": 3500,
                        "capacity": 5000,
                        "failureRate": 0.2,
                        "replication": "Auto-scaling ECS Tasks",
                        "description": "Executes domain logic, validation, and orchestrates data access.",
                        "explanation": "Stateless containerized service that horizontally auto-scales with demand.",
                    },
                },
                {
                    "id": "app-cache",
                    "type": "architectureNode",
                    "position": {"x": 860, "y": 120},
                    "data": {
                        "label": "In-Memory Cache",
                        "category": "cache",
                        "tech": "Redis 7.2",
                        "latency": 2,
                        "rps": 2800,
                        "capacity": 25000,
                        "failureRate": 0.05,
                        "replication": "Primary-Replica",
                        "description": "High-speed key-value cache for hot query results.",
                        "explanation": "Serves 80%+ of read requests in <2ms, shielding the primary database.",
                    },
                },
                {
                    "id": "app-db",
                    "type": "architectureNode",
                    "position": {"x": 860, "y": 300},
                    "data": {
                        "label": "Relational DB",
                        "category": "database",
                        "tech": "PostgreSQL 16",
                        "latency": 22,
                        "rps": 700,
                        "capacity": 2500,
                        "failureRate": 0.1,
                        "replication": "Primary + 2 Read Replicas",
                        "description": "ACID transactional database with write-ahead logging.",
                        "explanation": "Durable system of record for structured business data.",
                    },
                },
            ]
            edges = [
                {"id": "ae1", "source": "app-client", "target": "app-gateway", "label": "HTTPS Traffic", "animated": True, "data": {"protocol": "HTTP/REST"}},
                {"id": "ae2", "source": "app-gateway", "target": "app-service", "label": "Route Request", "animated": True, "data": {"protocol": "HTTP/REST"}},
                {"id": "ae3", "source": "app-service", "target": "app-cache", "label": "Cache Check", "animated": True, "data": {"protocol": "TCP"}},
                {"id": "ae4", "source": "app-service", "target": "app-db", "label": "DB Query", "animated": True, "data": {"protocol": "SQL"}},
            ]
            summary = f"Synthesized a resilient cloud system design for '{prompt}' featuring reverse proxy ingress, containerized core compute, Redis caching, and replicated PostgreSQL storage."
            recommendations = [
                "Configure connection pooling (e.g. PgBouncer) between the core service and PostgreSQL database.",
                "Set cache-control headers and short TTLs with cache invalidation on write.",
            ]

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": summary,
            "recommendations": recommendations,
        }

    def _generate_fallback_chat(self, message: str, nodes: List[Any], edges: List[Any], mode: str) -> str:
        msg_lower = message.lower()
        if "bottleneck" in msg_lower or "capacity" in msg_lower:
            return (
                f"📊 **Bottleneck Analysis for Current Canvas:**\n\n"
                f"You currently have {len(nodes)} active components.\n"
                f"• Any component where incoming RPS > Capacity will suffer latency spikes and dropped requests.\n"
                f"• **Recommended Action**: If your database or service shows high utilization, introduce a **Redis Cache** in front of reads, or buffer writes through an **Apache Kafka** queue."
            )
        elif "explain" in msg_lower or "learn" in msg_lower:
            return (
                f"🎓 **System Design Breakdown ({mode.capitalize()} Mode):**\n\n"
                f"1. **Ingress Layer**: Traffic enters through clients and is routed by the Gateway/Load Balancer.\n"
                f"2. **Compute Tier**: Stateless microservices handle business logic and coordinate dependencies.\n"
                f"3. **Data Tier**: Hot data is kept in sub-millisecond RAM caches, while durable records reside in the replicated ACID database."
            )
        else:
            return (
                f"💡 **Architectural Feedback:**\n\n"
                f"Your canvas contains {len(nodes)} nodes and {len(edges)} connections. "
                f"To optimize throughput, consider:\n"
                f"• Horizontal auto-scaling on compute services\n"
                f"• Asynchronous message queue decoupling for non-blocking operations\n"
                f"• Multi-AZ database read replicas to distribute query loads"
            )
