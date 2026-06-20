from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Intent(str, Enum):
    ASK_THEORY = "ASK_THEORY"
    SUBMIT_PROBLEM = "SUBMIT_PROBLEM"
    REQUEST_HINT = "REQUEST_HINT"
    SUBMIT_APPROACH = "SUBMIT_APPROACH"
    SUBMIT_CODE = "SUBMIT_CODE"
    ASK_DIRECT_SOLUTION = "ASK_DIRECT_SOLUTION"


@dataclass
class Classification:
    topic: str
    pattern: str
    confidence: float
    key_signals: list[str]
    recommended_hint_path: list[str]


@dataclass
class LearningState:
    current_problem: str | None = None
    problem_type: str | None = None
    concepts: list[str] = field(default_factory=list)
    hint_level: int = 0
    student_attempts: list[str] = field(default_factory=list)
    misconceptions: list[str] = field(default_factory=list)
    next_action: str = "classify_or_ask"


@dataclass
class AgentTurn:
    intent: Intent
    response: str
    state: LearningState
    classification: Classification | None = None
