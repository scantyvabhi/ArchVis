"""TypeSafe AI client wrapper for ArchVis AI."""
from typesafe_sdk import TypeSafeClient, Noul, Choice, Score
from typing import Dict, Any, List, Optional
import os


class ArchVisTypeSafeClient:
    """TypeSafe client tailored for architecture evaluation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY")
        if not self.api_key:
            raise ValueError("TYPESAFE_API_KEY not configured")
        self.client = TypeSafeClient(api_key=self.api_key)
        self.model = "jev-latest"
    
    def evaluate_architecture(self, architecture_json: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive architecture evaluation using TypeSafe AI."""
        state = {
            "architecture": architecture_json,
            "components": architecture_json.get("nodes", []),
            "data_flows": architecture_json.get("edges", []),
            "metadata": architecture_json.get("metadata", {}),
            "summary": architecture_json.get("summary", ""),
        }
        
        questions = self._build_architecture_questions()
        response = self.client.system_one(state=state, model=self.model, questions=questions)
        return self._parse_answers(response.answers)
    
    def _build_architecture_questions(self) -> Dict[str, Any]:
        """Build the complete set of architecture evaluation questions."""
        return {
            # Noul: Pass/Fail gates (binary yes/no with probability)
            "has_no_circular_dependencies": Noul(
                instructions="Does this architecture have any circular dependencies between components?",
                criteria={
                    "true": "At least one circular dependency exists in the data flows",
                    "false": "No circular dependencies detected"
                }
            ),
            "has_no_single_point_of_failure": Noul(
                instructions="Does this architecture have a single point of failure?",
                criteria={
                    "true": "At least one component whose failure brings down the system",
                    "false": "All critical paths have redundancy and failover"
                }
            ),
            "follows_best_practices": Noul(
                instructions="Does this architecture follow cloud-native best practices?",
                criteria={
                    "true": "Follows 12-factor, stateless services, observability, circuit breakers",
                    "false": "Missing key cloud-native best practices"
                }
            ),
            "is_production_ready": Noul(
                instructions="Is this architecture ready for production deployment?",
                criteria={
                    "true": "Has monitoring, auto-scaling, security, disaster recovery, runbooks",
                    "false": "Missing production requirements"
                }
            ),
            
            # Choice: Classification with probabilities
            "architecture_pattern": Choice(
                instructions="What architectural pattern does this follow?",
                criteria={
                    "microservices": "Decoupled services with independent deployability",
                    "modular_monolith": "Modular but single deployment unit",
                    "serverless": "Function-based, event-driven",
                    "event_driven": "Async messaging as primary communication",
                    "layered": "Traditional n-tier architecture",
                    "custom": "Doesn't fit standard patterns"
                }
            ),
            "primary_bottleneck_type": Choice(
                instructions="What is the primary bottleneck type?",
                criteria={
                    "database": "DB write throughput, connection pooling, query performance",
                    "network": "Cross-service latency, bandwidth, serialization",
                    "compute": "CPU/memory saturation, inefficient algorithms",
                    "cache": "Cache hit ratio, invalidation, cold starts",
                    "none": "No significant bottlenecks identified"
                }
            ),
            "security_posture": Choice(
                instructions="What is the overall security posture?",
                criteria={
                    "hardened": "mTLS, WAF, secrets management, least privilege, zero trust",
                    "standard": "TLS, authentication, basic RBAC, input validation",
                    "basic": "Minimal security controls, some gaps",
                    "weak": "Missing critical security controls"
                }
            ),
            
            # Score: Quality ratings on 0-4 scale
            "scalability_score": Score(
                instructions="Rate the architecture's ability to scale horizontally",
                criteria=[
                    "Cannot scale (single instance only)",
                    "Limited scaling (vertical only, <10x)",
                    "Moderate scaling (horizontal, 10-100x)",
                    "Good scaling (horizontal, 100-1000x, some limits)",
                    "Excellent scaling (unlimited horizontal, stateless)"
                ]
            ),
            "observability_score": Score(
                instructions="Rate observability: logging, metrics, tracing, alerting, dashboards",
                criteria=[
                    "No observability",
                    "Logs only",
                    "Logs + basic metrics",
                    "Logs + metrics + distributed tracing",
                    "Full observability with SLIs/SLOs, alerting, dashboards"
                ]
            ),
            "cost_efficiency_score": Score(
                instructions="Rate cost efficiency for expected workload",
                criteria=[
                    "Very inefficient (>50% waste)",
                    "Inefficient (20-50% waste)",
                    "Moderate (10-20% waste)",
                    "Efficient (5-10% waste)",
                    "Highly optimized (<5% waste)"
                ]
            ),
            "maintainability_score": Score(
                instructions="Rate how maintainable this architecture is",
                criteria=[
                    "Unmaintainable (spaghetti, no boundaries)",
                    "Difficult (tight coupling, unclear ownership)",
                    "Moderate (some coupling, defined modules)",
                    "Good (loose coupling, clear boundaries, docs)",
                    "Excellent (clean architecture, self-documenting)"
                ]
            ),
            "reliability_score": Score(
                instructions="Rate reliability: fault tolerance, recovery, SLA potential",
                criteria=[
                    "Fragile (no redundancy, manual recovery)",
                    "Basic (some redundancy, slow recovery)",
                    "Resilient (auto-failover, <5min recovery)",
                    "Highly available (multi-AZ, <1min recovery)",
                    "Fault tolerant (multi-region, zero-downtime)"
                ]
            )
        }
    
    def _parse_answers(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Parse TypeSafe answers into ArchVis format."""
        parsed = {}
        for key, answer in answers.items():
            if answer["type"] == "noul":
                parsed[key] = {
                    "value": answer["noul"],
                    "passed": answer["noul"] >= 0.5,
                    "confidence": abs(answer["noul"] - 0.5) * 2
                }
            elif answer["type"] == "choice":
                parsed[key] = {
                    "value": answer["choice"],
                    "probabilities": answer["probabilities"],
                    "confidence": answer["confidence"]
                }
            elif answer["type"] == "score":
                parsed[key] = {
                    "value": answer["score"],
                    "level": round(answer["score"]),
                    "legend": answer["legend"],
                    "probabilities": answer["probabilities"],
                    "confidence": answer["confidence"]
                }
        return parsed
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary from TypeSafe results."""
        gates = {k: v for k, v in results.items() 
                if k.startswith("has_") or k.startswith("is_") or k.startswith("follows_")}
        scores = {k: v for k, v in results.items() if k.endswith("_score")}
        classifications = {k: v for k, v in results.items() 
                          if k in ["architecture_pattern", "primary_bottleneck_type", "security_posture"]}
        
        gates_passed = sum(1 for v in gates.values() if v.get("passed", False))
        total_gates = len(gates)
        avg_score = sum(v["value"] for v in scores.values()) / len(scores) if scores else 0
        
        return {
            "gates": gates,
            "classifications": classifications,
            "scores": scores,
            "gates_passed": gates_passed,
            "total_gates": total_gates,
            "avg_quality_score": avg_score,
            "summary": f"{gates_passed}/{total_gates} gates passed, avg quality score: {avg_score:.1f}/4.0"
        }
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[Dict]:
        """Convert TypeSafe results to actionable recommendations."""
        recs = []
        
        # Failed gates -> critical recommendations
        for gate, data in results.items():
            if gate.startswith("has_") or gate.startswith("is_") or gate.startswith("follows_"):
                if not data.get("passed", True):
                    recs.append({
                        "priority": "critical",
                        "category": "architecture",
                        "action": f"Fix: {gate.replace('_', ' ').title()}",
                        "rationale": f"TypeSafe validation failed with {data['value']:.0%} probability"
                    })
        
        # Low scores -> improvement recommendations
        for score_key, data in results.items():
            if score_key.endswith("_score") and data["value"] < 2.5:
                recs.append({
                    "priority": "high",
                    "category": score_key.replace("_score", ""),
                    "action": f"Improve {score_key.replace('_score', '').replace('_', ' ')}",
                    "rationale": f"Scored {data['value']:.1f}/4.0 ({data['legend'][str(data['level'])]}"
                })
        
        return recs


def create_typesafe_client() -> Optional[ArchVisTypeSafeClient]:
    """Factory function to create TypeSafe client if API key is available."""
    try:
        return ArchVisTypeSafeClient()
    except ValueError:
        return None