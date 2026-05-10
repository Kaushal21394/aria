from __future__ import annotations

from langgraph.graph import END, StateGraph

from .state import ARIAState
from .planner import planner_node
from .trial_agent import trial_agent_node
from .intel_agent import intel_agent_node
from .fit_scorer import fit_scorer_node
from .synthesizer import synthesizer_node


def build_aria_graph():
    """
    Compile the ARIA research graph.

    Flow:
        planner → trial_agent → intel_agent → fit_scorer → synthesizer → END

    The planner runs first and writes an ExecutionPlan to state. Each
    downstream node reads execution_plan.agents and self-skips if it is
    not listed — so the graph topology stays simple while the actual work
    adapts to the user's goal.

    The synthesizer reads execution_plan.output_format and produces
    whatever format the planner decided (outreach_email, competitive_brief,
    pipeline_summary, or account_snapshot).

    The 'errors' and 'total_usage' fields use operator.add reducers so
    every node's contribution is accumulated rather than overwritten.
    """
    graph = StateGraph(ARIAState)

    graph.add_node("planner",      planner_node)
    graph.add_node("trial_agent",  trial_agent_node)
    graph.add_node("intel_agent",  intel_agent_node)
    graph.add_node("fit_scorer",   fit_scorer_node)
    graph.add_node("synthesizer",  synthesizer_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner",     "trial_agent")
    graph.add_edge("trial_agent", "intel_agent")
    graph.add_edge("intel_agent", "fit_scorer")
    graph.add_edge("fit_scorer",  "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()
