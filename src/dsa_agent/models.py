from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class Intent(str, Enum):
    ASK_THEORY = "ASK_THEORY"
    SUBMIT_PROBLEM = "SUBMIT_PROBLEM"
    REQUEST_HINT = "REQUEST_HINT"
    SUBMIT_APPROACH = "SUBMIT_APPROACH"
    SUBMIT_CODE = "SUBMIT_CODE"
    ASK_DIRECT_SOLUTION = "ASK_DIRECT_SOLUTION"


class TestCategory(str, Enum):
    BASIC = "basic"
    EDGE = "edge"
    ADVERSARIAL = "adversarial"
    STRESS = "stress"


class TestPurpose(str, Enum):
    VALIDATION = "validation"
    TRACE_ONLY = "trace_only"


class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"


@dataclass
class Classification:
    topic: str
    pattern: str
    difficulty: str
    confidence: float
    key_signals: list[str]
    recommended_hint_path: list[str]


@dataclass
class GeneratedTestCase:
    name: str
    input: str
    expected_output: str | None
    category: TestCategory
    rationale: str
    purpose: TestPurpose = TestPurpose.VALIDATION


@dataclass
class TestSuite:
    problem_id: str
    language: str
    tests: list[GeneratedTestCase]
    coverage_notes: list[str]


@dataclass
class FailedTest:
    name: str
    expected_output: str | None
    actual_output: str
    error: str | None = None


@dataclass
class ValidationResult:
    status: ValidationStatus
    passed_count: int
    failed_tests: list[FailedTest] = field(default_factory=list)
    runtime_errors: list[str] = field(default_factory=list)
    timeout: bool = False
    complexity_notes: list[str] = field(default_factory=list)


@dataclass
class PedagogyReview:
    safe_to_send: bool
    risk_level: str
    issues: list[str] = field(default_factory=list)
    revision_instruction: str | None = None


@dataclass
class AgentTraceItem:
    node_name: str
    status: str
    summary: str
    metadata: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass
class EvaluationScore:
    safe_socratic: bool
    hint_level_match: bool
    concise: bool
    uses_quality_signal: bool
    notes: list[str] = field(default_factory=list)


@dataclass
class LearningState:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    chat_title: str = "Phiên mới"
    current_problem: str | None = None
    problem_type: str | None = None
    concepts: list[str] = field(default_factory=list)
    hint_level: int = 0
    student_attempts: list[str] = field(default_factory=list)
    misconceptions: list[str] = field(default_factory=list)
    generated_tests: list[TestSuite] = field(default_factory=list)
    latest_validation: ValidationResult | None = None
    pedagogy_flags: list[PedagogyReview] = field(default_factory=list)
    agent_trace: list[AgentTraceItem] = field(default_factory=list)
    evaluation_scores: list[EvaluationScore] = field(default_factory=list)
    next_action: str = "classify_or_ask"


@dataclass
class AgentTurn:
    intent: Intent
    response: str
    state: LearningState
    classification: Classification | None = None
    test_suite: TestSuite | None = None
    validation: ValidationResult | None = None
    pedagogy_review: PedagogyReview | None = None
