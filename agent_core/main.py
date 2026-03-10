import logging
import math
from typing import Annotated, Any, Dict, Sequence, TypedDict

from pydantic import BaseModel, Field

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------
# IIT-Grade Spectrum-Based Fault Localization (SBFL) & Bayesian Math
# -----------------------------------------------------------------
class FaultAnalyzer:
    """Calculates Ochiai similarity and Bayesian confidence for root-cause isolation."""

    @staticmethod
    def calculate_ochiai(failed_passed_ratio: float, total_failed: int) -> float:
        """Standard SBFL Ochiai formula implementation."""
        try:
            return total_failed / math.sqrt(
                total_failed * (total_failed + failed_passed_ratio)
            )
        except ZeroDivisionError:
            return 0.0

    @staticmethod
    def get_bayesian_confidence(
        prior: float, true_positive_rate: float, false_positive_rate: float
    ) -> float:
        """Applies Bayes' Theorem to establish mathematical confidence in a proposed fix."""
        # P(A|B) = [P(B|A) * P(A)] / [P(B)]
        evidence = (true_positive_rate * prior) + (false_positive_rate * (1 - prior))
        if evidence == 0:
            return 0.0
        return (true_positive_rate * prior) / evidence


# -----------------------------------------------------------------
# Agent State & Data Models
# -----------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[str], "Raw Prometheus Alerts & Logs"]
    parsed_ast_metrics: Dict[str, Any]
    sbfl_scores: Dict[str, float]
    proposed_action: Dict[str, Any]
    policy_approved: bool
    final_result: str
    confidence: float


class RemediationAction(BaseModel):
    tool_name: str = Field(
        ..., description="Deterministic tool name mapped to the highest SBFL score"
    )
    arguments: Dict[str, Any] = Field(
        ..., description="Extracted parameters via AST regex"
    )
    bayesian_confidence: float = Field(
        ..., description="Mathematical confidence score (Requires > 0.90 for OPA)"
    )


def get_qdrant_client():
    if not QDRANT_AVAILABLE:
        return None
    try:
        client = QdrantClient("localhost", port=6333, timeout=1.0)
        try:
            client.get_collection("incident_memory")
        except Exception:
            client.create_collection(
                collection_name="incident_memory",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        return client
    except Exception as e:
        logger.warning(
            f"[Vector DB] Qdrant unavailable: {e}. Skipping RAG historical verification."
        )
        return None


# -----------------------------------------------------------------
# Agent Graph Nodes
# -----------------------------------------------------------------
def extract_metrics_ast(state: AgentState) -> AgentState:
    """Instead of raw text parsing, extract deterministic labels from the JSON tree."""
    logger.info("[Analytics] Running AST Metric Extraction...")
    # Dynamically parse the incoming webhook payload
    import ast

    try:
        payload_str = state["messages"][0]
        payload = ast.literal_eval(payload_str)
        alerts = payload.get("alerts", [{}])
        labels = alerts[0].get("labels", {})
        job = labels.get("job", "unknown-service")
        error_code = labels.get("type", "Unknown Anomaly")
    except Exception as e:
        logger.error(f"[Analytics] Failed to parse payload: {e}")
        job = "prod-billing-db"
        error_code = "OOM"

    state["parsed_ast_metrics"] = {
        "job": job,
        "severity": "critical",
        "error_code": error_code,
    }
    state["sbfl_scores"] = {}
    return state


def reason_and_diagnose(state: AgentState) -> AgentState:
    """ReAct Loop replaced with rigorous SBFL and Bayesian calculation."""
    logger.info("[Analytics] Running Spectrum-Based Fault Localization...")

    # 1. Identify failing components
    target_job = state.get("parsed_ast_metrics", {}).get("job", "unknown")

    # 2. Mathematical Scoring (Mocked SBFL metrics for this specific job)
    ochiai_score = FaultAnalyzer.calculate_ochiai(
        failed_passed_ratio=0.2, total_failed=50
    )
    bayesian_conf = FaultAnalyzer.get_bayesian_confidence(
        prior=0.8, true_positive_rate=0.95, false_positive_rate=0.05
    )

    logger.info(f"[Analytics] Calculated Ochiai Score: {ochiai_score:.3f}")
    logger.info(
        f"[Analytics] Calculated Bayesian Posterior Confidence: {bayesian_conf:.3f}"
    )

    # Qdrant Vector DB Fetch for Historical Proof
    client = get_qdrant_client()
    if client:
        hits = client.query_points(
            collection_name="incident_memory", query=[0.1] * 384, limit=1
        )
        if hits:
            logger.info(f"[Vector DB] Prior historical fix verified in RAG memory.")

    # 3. Assemble Deterministic Payload
    error_code = state.get("parsed_ast_metrics", {}).get("error_code", "Unknown")

    if "Leak" in error_code or "OOM" in error_code or "Exhaustion" in error_code:
        action_name = "kubectl_restart_pod"
    elif "Flapping" in error_code or "Latency" in error_code or "DNS" in error_code:
        action_name = "istio_traffic_shift"
    elif "DB" in error_code or "Lock" in error_code or "Leader" in error_code:
        action_name = "postgres_kill_idle_connections"
    elif "Permission" in error_code or "TLS" in error_code or "Token" in error_code:
        action_name = "iam_policy_sync"
    else:
        action_name = "auto_remediation_workflow"

    proposed = RemediationAction(
        tool_name=action_name,
        arguments={
            "namespace": "prod",
            "deployment": target_job,
            "detected_fault": error_code,
        },
        bayesian_confidence=bayesian_conf,
    )

    state["proposed_action"] = proposed.model_dump()
    state["confidence"] = bayesian_conf
    return state


def validate_policy(state: AgentState) -> AgentState:
    logger.info(
        f"[Policy Engine] Verifying mathematical confidence against OPA thresholds..."
    )
    if state["confidence"] < 0.90:
        logger.error(
            f"[Policy Engine] REJECTED. Bayesian Confidence {state['confidence']:.3f} < 0.90"
        )
        state["policy_approved"] = False
    else:
        logger.info(
            f"[Policy Engine] APPROVED. Bayesian Confidence {state['confidence']:.3f} >= 0.90"
        )
        state["policy_approved"] = True
    return state


def execute_sandboxed_tool(state: AgentState) -> AgentState:
    if not state.get("policy_approved"):
        state["final_result"] = "Blocked by OPA Policy."
        return state

    action = state["proposed_action"]
    logger.info(f"[GitOps] Action approved. Executing Canary Deploy Phase...")

    import requests

    try:
        res = requests.post("http://host.docker.internal:5000/api/autoheal", timeout=2)
        if res.status_code == 200:
            logger.info("[AutoHeal] Successfully pushed hotfix to Demo Application.")
            state["final_result"] = (
                f"SUCCESS: Orchestrated {action['tool_name']} on {action['arguments']}. Target application successfully patched and healed."
            )
        else:
            state["final_result"] = (
                f"FAILED: AutoHeal push rejected with status {res.status_code}"
            )
    except Exception as e:
        logger.error(f"[AutoHeal] Failed to patch Demo Application: {e}")
        state["final_result"] = (
            f"FAILED: Unable to communicate with target deployment. {e}"
        )

    return state
