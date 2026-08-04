"""LangGraph assembly for the investigation path (PIPELINE.md #1-4;
ARCHITECTURE.md flowchart nodes A->B->{C,D,E}->F).

The hypothesis loop and everything downstream (Phase 2+) extend this graph
later; for now it ends at the Evidence Collector.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.deploy_agent import deploy_agent_node
from app.agents.evidence_collector import evidence_collector_node
from app.agents.log_agent import log_agent_node
from app.agents.metrics_agent import metrics_agent_node
from app.agents.supervisor import supervisor_node
from app.models.state import IncidentState


def route_after_supervisor(state: IncidentState) -> list[str]:
    """Dynamic parallel fan-out based on the Supervisor's agents_dispatched decision."""
    return state.agents_dispatched


def build_graph():
    graph = StateGraph(IncidentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("log_agent", log_agent_node)
    graph.add_node("metrics_agent", metrics_agent_node)
    graph.add_node("deploy_agent", deploy_agent_node)
    graph.add_node("evidence_collector", evidence_collector_node)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        ["log_agent", "metrics_agent", "deploy_agent"],
    )
    graph.add_edge("log_agent", "evidence_collector")
    graph.add_edge("metrics_agent", "evidence_collector")
    graph.add_edge("deploy_agent", "evidence_collector")
    graph.add_edge("evidence_collector", END)

    return graph.compile()
