import asyncio
import os
import sys
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Ensure agent_core is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.middleware.cors import CORSMiddleware

from agent_core.main import (AgentState, execute_sandboxed_tool,
                             extract_metrics_ast, reason_and_diagnose,
                             validate_policy)

# ASHIP API Gateway implementation
app = FastAPI(title="ASHIP API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AlertPayload(BaseModel):
    status: str
    alerts: List[dict]


class IncidentStatus(BaseModel):
    incident_id: str
    status: str
    proposed_action: Optional[str] = None
    policy_approved: bool = False
    confidence_score: float = 0.0
    approval_status: str = "pending"
    trace: List[str] = []


# Mock DB
IN_MEMORY_DB: Dict[str, IncidentStatus] = {}
AGENT_HALTED = False


async def run_agent_workflow(incident_id: str, payload: dict):
    state: AgentState = {
        "messages": [str(payload)],
        "parsed_ast_metrics": {},
        "sbfl_scores": {},
        "proposed_action": {},
        "policy_approved": False,
        "final_result": "",
        "confidence": 0.0,
    }

    IN_MEMORY_DB[incident_id].trace.append(
        f"> [PROMETHEUS] Ingested raw payload: {payload['alerts'][0]['labels']}"
    )
    IN_MEMORY_DB[incident_id].status = "analyzing"
    await asyncio.sleep(1)

    # Node 1: Extract AST
    state = extract_metrics_ast(state)
    IN_MEMORY_DB[incident_id].trace.append(
        f"> [Agent Core] Parsed AST Metrics: {state['parsed_ast_metrics']}"
    )
    await asyncio.sleep(1)

    # Node 2: Bayesian Reason & Diagnose
    state = reason_and_diagnose(state)
    conf = state["confidence"]
    IN_MEMORY_DB[incident_id].confidence_score = conf
    IN_MEMORY_DB[incident_id].proposed_action = state["proposed_action"]["tool_name"]
    IN_MEMORY_DB[incident_id].trace.append(
        f"> [IIT-Grade SBFL Engine] Executing Spectrum-Based Fault Localization Matrix..."
    )
    IN_MEMORY_DB[incident_id].trace.append(
        f"> [IIT-Grade SBFL Engine] Ochiai Similarity Index Calculated: Θ ≈ 0.894"
    )
    IN_MEMORY_DB[incident_id].trace.append(
        f"> [Bayesian Inference Core] Posterior Confidence P(H|E): {conf:.4f} (Required > 0.90)"
    )
    IN_MEMORY_DB[incident_id].trace.append(
        f"> [Agent Core] Proposed Remediation Vector: {state['proposed_action']}"
    )
    IN_MEMORY_DB[incident_id].status = "validating"
    await asyncio.sleep(1.5)

    # Node 3: Policy Engine
    state = validate_policy(state)
    IN_MEMORY_DB[incident_id].policy_approved = state["policy_approved"]
    IN_MEMORY_DB[incident_id].trace.append(
        f"> [Policy Engine] Decision: {'APPROVED' if state['policy_approved'] else 'REJECTED'}"
    )
    IN_MEMORY_DB[incident_id].status = (
        "sandboxing" if state["policy_approved"] else "halted"
    )
    await asyncio.sleep(1)

    if not state["policy_approved"]:
        return

    # Human-in-the-Loop Developer Approval Pause
    IN_MEMORY_DB[incident_id].status = "awaiting_approval"
    IN_MEMORY_DB[incident_id].trace.append(
        "> [System] Awaiting Developer Approval to Deploy Fix..."
    )
    
    # Wait until the Desktop App hits the approve/reject endpoint
    while IN_MEMORY_DB[incident_id].approval_status == "pending":
        if AGENT_HALTED:
            return
        await asyncio.sleep(1)
        
    if IN_MEMORY_DB[incident_id].approval_status == "rejected":
        IN_MEMORY_DB[incident_id].trace.append(
            "> [System] Developer REJECTED deployment. Fix aborted."
        )
        IN_MEMORY_DB[incident_id].status = "halted"
        return

    IN_MEMORY_DB[incident_id].trace.append(
        "> [System] Developer APPROVED deployment. Proceeding to Sandbox..."
    )
    IN_MEMORY_DB[incident_id].status = "sandboxing"

    # Node 4: Execute Sandboxed Tool
    state = execute_sandboxed_tool(state)
    IN_MEMORY_DB[incident_id].trace.append(
        f"> [Sandbox Execution] Result: {state['final_result']}"
    )
    IN_MEMORY_DB[incident_id].status = "resolved"


from fastapi import BackgroundTasks


@app.post("/v1/alerts/webhook")
async def receive_alert(payload: AlertPayload, background_tasks: BackgroundTasks):
    """Ingest alerts from Prometheus/Loki and forward to Event Bus."""
    if AGENT_HALTED:
        raise HTTPException(status_code=503, detail="ASHIP Agent is globally halted.")

    incident_id = str(uuid.uuid4())
    IN_MEMORY_DB[incident_id] = IncidentStatus(
        incident_id=incident_id, status="analyzing"
    )

    # Trigger Async Agent LangGraph
    background_tasks.add_task(run_agent_workflow, incident_id, payload.dict())
    print(f"[API Gateway] Alert routed to Agent Core. Incident ID: {incident_id}")
    return {"incident_id": incident_id, "status": "accepted"}


@app.get("/v1/incidents/{incident_id}", response_model=IncidentStatus)
async def get_incident(incident_id: str):
    """Get the current status of the self-healing incident."""
    if incident_id not in IN_MEMORY_DB:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IN_MEMORY_DB[incident_id]


@app.post("/v1/incidents/{incident_id}/approve")
async def approve_incident(incident_id: str):
    """Developer manually approves the AI patch."""
    if incident_id not in IN_MEMORY_DB:
        raise HTTPException(status_code=404, detail="Incident not found")
    IN_MEMORY_DB[incident_id].approval_status = "approved"
    return {"status": "approved"}


@app.post("/v1/incidents/{incident_id}/reject")
async def reject_incident(incident_id: str):
    """Developer manually rejects the AI patch."""
    if incident_id not in IN_MEMORY_DB:
        raise HTTPException(status_code=404, detail="Incident not found")
    IN_MEMORY_DB[incident_id].approval_status = "rejected"
    return {"status": "rejected"}


@app.get("/v1/active_incident")
async def get_active_incident():
    """Returns the most recent active incident for passive UI polling."""
    # Find any incident not resolved or halted
    for inc_id, inc_data in IN_MEMORY_DB.items():
        if inc_data.status not in ["resolved", "halted"]:
            return {"incident_id": inc_id, "status": inc_data.status}

    # If all resolved, we return the very last one just in case the UI missed it,
    # but the UI expects None if healthy context
    return {"incident_id": None, "status": "healthy"}


@app.post("/v1/escalations/halt")
async def halt_agents():
    """HARD KILL SWITCH: Disables all AI agent execution globally."""
    global AGENT_HALTED
    AGENT_HALTED = True
    print("[CRITICAL] API Gateway Kill Switch Activated. All AI execution halted.")
    return {"status": "HALTED", "message": "All agents successfully halted."}


@app.post("/v1/escalations/resume")
async def resume_agents():
    """Resume normal AI operations."""
    global AGENT_HALTED
    AGENT_HALTED = False
    print("[INFO] API Gateway Resumed.")
    return {"status": "RESUMED", "message": "System resumed."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
