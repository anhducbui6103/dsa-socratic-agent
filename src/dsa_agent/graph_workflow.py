from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from .models import AgentTurn, Intent
from .orchestrator import DsaLearningAgent


class TutorGraphState(TypedDict, total=False):
    message: str
    intent: Intent
    turn: AgentTurn
    final_response: str
    metadata: dict[str, Any]


@dataclass
class DsaTutorGraph:
    """LangGraph workflow for the DSA tutor.

    Each major tutor behavior is represented as a separate graph node so the
    workflow is visible and extendable instead of hiding every agent step in one
    monolithic orchestrator node.
    """

    agent: DsaLearningAgent

    def __post_init__(self) -> None:
        self._compiled_graph = self._build_graph()

    def run(self, message: str) -> AgentTurn:
        self.agent.state.agent_trace.clear()
        if self._compiled_graph is None:
            return self.agent.handle(message)

        result = self._compiled_graph.invoke({"message": message})
        return result["turn"]

    def _build_graph(self):
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError:
            return None

        graph = StateGraph(TutorGraphState)
        graph.add_node("detect_intent", self._detect_intent_node)
        graph.add_node("submit_problem", self._submit_problem_node)
        graph.add_node("request_hint", self._request_hint_node)
        graph.add_node("submit_code", self._submit_code_node)
        graph.add_node("direct_solution_guard", self._direct_solution_guard_node)
        graph.add_node("submit_approach", self._submit_approach_node)
        graph.add_node("ask_theory", self._ask_theory_node)
        graph.add_node("finalize", self._finalize_node)

        graph.add_edge(START, "detect_intent")
        graph.add_conditional_edges(
            "detect_intent",
            self._route_intent,
            {
                Intent.SUBMIT_PROBLEM.value: "submit_problem",
                Intent.REQUEST_HINT.value: "request_hint",
                Intent.SUBMIT_CODE.value: "submit_code",
                Intent.ASK_DIRECT_SOLUTION.value: "direct_solution_guard",
                Intent.SUBMIT_APPROACH.value: "submit_approach",
                Intent.ASK_THEORY.value: "ask_theory",
            },
        )
        for node in (
            "submit_problem",
            "request_hint",
            "submit_code",
            "direct_solution_guard",
            "submit_approach",
            "ask_theory",
        ):
            graph.add_edge(node, "finalize")
        graph.add_edge("finalize", END)
        return graph.compile()

    def _detect_intent_node(self, state: TutorGraphState) -> TutorGraphState:
        message = state["message"]
        self.agent._trace("LangGraph", "start", "Started workflow")
        intent = self.agent.detect_intent(message)
        self.agent.record_attempt(message)
        return {**state, "intent": intent}

    def _route_intent(self, state: TutorGraphState) -> str:
        self.agent._trace("LangGraph Router", "ok", f"Routing to {state['intent'].value}")
        return state["intent"].value

    def _submit_problem_node(self, state: TutorGraphState) -> TutorGraphState:
        return self._with_turn(state, self.agent.handle_submit_problem(state["message"]))

    def _request_hint_node(self, state: TutorGraphState) -> TutorGraphState:
        return self._with_turn(state, self.agent.handle_request_hint())

    def _submit_code_node(self, state: TutorGraphState) -> TutorGraphState:
        return self._with_turn(state, self.agent.handle_submit_code(state["message"]))

    def _direct_solution_guard_node(self, state: TutorGraphState) -> TutorGraphState:
        return self._with_turn(state, self.agent.handle_direct_solution_request())

    def _submit_approach_node(self, state: TutorGraphState) -> TutorGraphState:
        return self._with_turn(state, self.agent.handle_submit_approach())

    def _ask_theory_node(self, state: TutorGraphState) -> TutorGraphState:
        return self._with_turn(state, self.agent.handle_theory_question())

    def _with_turn(self, state: TutorGraphState, turn: AgentTurn) -> TutorGraphState:
        return {
            **state,
            "turn": turn,
            "metadata": {
                "intent": turn.intent.value,
                "problem_type": turn.state.problem_type,
                "hint_level": turn.state.hint_level,
                "validation_status": turn.validation.status.value if turn.validation else None,
            },
        }

    def _finalize_node(self, state: TutorGraphState) -> TutorGraphState:
        turn = state["turn"]
        self.agent._trace("LangGraph Finalize", "ok", "Finished workflow")
        return {**state, "final_response": turn.response}
