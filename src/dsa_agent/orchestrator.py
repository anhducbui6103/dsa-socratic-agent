from __future__ import annotations

from .agents import (
    IntentDetectorAgent,
    PedagogyCriticAgent,
    ProblemClassifierAgent,
    SessionTitleAgent,
    SocraticResponseAgent,
    TestcaseGeneratorAgent,
)
from .code_analysis import analyze_code
from .hints import direct_solution_guard, next_hint
from .llm_client import GeminiLlmClient, LlmClient
from .models import AgentTraceItem, AgentTurn, Classification, Intent, LearningState, PedagogyReview, TestPurpose, TestSuite
from .quality import CodeExecutionValidatorAgent


class DsaLearningAgent:
    """Application service that coordinates state and specialist agents."""

    def __init__(self, enable_execution: bool = False, llm_client: LlmClient | None = None) -> None:
        self.state = LearningState()
        self._last_classification: Classification | None = None
        self.llm_client = llm_client or GeminiLlmClient.from_env()

        self.intent_detector = IntentDetectorAgent(self.llm_client)
        self.problem_classifier = ProblemClassifierAgent(self.llm_client)
        self.testcase_generator = TestcaseGeneratorAgent(self.llm_client)
        self.pedagogy_critic = PedagogyCriticAgent(self.llm_client)
        self.response_generator = SocraticResponseAgent(self.llm_client)
        self.session_title_agent = SessionTitleAgent(self.llm_client)
        self.execution_validator = CodeExecutionValidatorAgent(enable_execution=enable_execution)

    def handle(self, message: str) -> AgentTurn:
        intent = self.detect_intent(message)
        self.record_attempt(message)
        return self.run_intent(intent, message)

    def detect_intent(self, message: str) -> Intent:
        intent = self.intent_detector.detect(message)
        self._trace("Intent Detector", "ok", f"Detected {intent.value}", intent=intent.value)
        return intent

    def record_attempt(self, message: str) -> None:
        self.state.student_attempts.append(message)
        self._trace("State Update", "ok", "Recorded student attempt", attempts=len(self.state.student_attempts))

    def run_intent(self, intent: Intent, message: str) -> AgentTurn:
        handlers = {
            Intent.SUBMIT_PROBLEM: self.handle_submit_problem,
            Intent.REQUEST_HINT: lambda _: self.handle_request_hint(),
            Intent.SUBMIT_CODE: self.handle_submit_code,
            Intent.ASK_DIRECT_SOLUTION: lambda _: self.handle_direct_solution_request(),
            Intent.SUBMIT_APPROACH: lambda _: self.handle_submit_approach(),
            Intent.ASK_THEORY: lambda _: self.handle_theory_question(),
        }
        return handlers[intent](message)

    def handle_submit_problem(self, message: str) -> AgentTurn:
        classification = self.problem_classifier.classify(message)
        self._last_classification = classification
        self.state.current_problem = message
        self.state.problem_type = classification.topic
        self.state.concepts = classification.key_signals
        self.state.hint_level = 0
        self._trace(
            "Problem Classifier",
            "ok",
            f"Classified as {classification.topic}",
            topic=classification.topic,
            confidence=classification.confidence,
        )

        test_suite = self._generate_test_suite(message, classification)
        self.state.next_action = "ask_student_understanding"
        guideline = (
            f"Mình nghiêng về nhóm `{classification.topic}` "
            f"(độ tin cậy khoảng {classification.confidence:.0%}).\n\n"
            "Trước khi đi vào cách làm, em thử tự mô tả lại input/output và ràng buộc chính của bài. "
            "Nếu phải giải tay một ví dụ nhỏ, em sẽ theo dõi thông tin nào sau mỗi bước?\n\n"
            f"Case tự kiểm gợi ý: `{test_suite.tests[0].name}` - {test_suite.tests[0].rationale}"
        )
        response, review = self._generate_reviewed_response(guideline)
        return AgentTurn(Intent.SUBMIT_PROBLEM, response, self.state, classification, test_suite=test_suite, pedagogy_review=review)

    def handle_request_hint(self) -> AgentTurn:
        self.state.hint_level = min(self.state.hint_level + 1, 3)
        self.state.next_action = "wait_for_student_attempt"
        guideline = next_hint(self.state, self._last_classification)
        self._trace("Hint Generator", "ok", f"Generated hint level {self.state.hint_level}", hint_level=self.state.hint_level)
        response, review = self._generate_reviewed_response(guideline)
        return AgentTurn(Intent.REQUEST_HINT, response, self.state, self._last_classification, pedagogy_review=review)

    def handle_submit_code(self, message: str) -> AgentTurn:
        test_suite = self._ensure_test_suite()
        validation = self.execution_validator.validate(message, "python", test_suite)
        self.state.latest_validation = validation
        self.state.next_action = "review_trace_or_edge_case"
        self._trace(
            "Execution Validator",
            validation.status.value,
            f"Validation status {validation.status.value}",
            passed_count=validation.passed_count,
            failed_count=len(validation.failed_tests),
        )

        guideline = self._code_review_guideline(message, validation.status.value)
        response, review = self._generate_reviewed_response(guideline, trace_summary="Generated code-review response")
        return AgentTurn(
            Intent.SUBMIT_CODE,
            response,
            self.state,
            self._last_classification,
            test_suite=test_suite,
            validation=validation,
            pedagogy_review=review,
        )

    def handle_direct_solution_request(self) -> AgentTurn:
        self.state.next_action = "redirect_to_socratic_hint"
        self._trace("Direct Solution Guard", "ok", "Redirected direct solution request")
        response, review = self._generate_reviewed_response(direct_solution_guard(), trace_summary="Generated guarded response")
        return AgentTurn(Intent.ASK_DIRECT_SOLUTION, response, self.state, self._last_classification, pedagogy_review=review)

    def handle_submit_approach(self) -> AgentTurn:
        self.state.next_action = "probe_correctness"
        guideline = (
            "Ý tưởng của em đã có hướng rồi. Giờ mình kiểm tra bằng phản ví dụ nhỏ nhé: "
            "điều kiện nào có thể làm cách làm của em cập nhật sai hoặc bỏ sót trường hợp?\n\n"
            "Em thử nêu độ phức tạp dự kiến và một edge case mà em thấy đáng ngại nhất."
        )
        response, review = self._generate_reviewed_response(guideline, trace_summary="Reviewed student approach")
        self._trace("Approach Reviewer", "ok", "Reviewed student approach", safe_to_send=review.safe_to_send)
        return AgentTurn(Intent.SUBMIT_APPROACH, response, self.state, self._last_classification, pedagogy_review=review)

    def handle_theory_question(self) -> AgentTurn:
        self.state.next_action = "ask_for_concrete_problem"
        guideline = (
            "Mình giải thích ngắn trước, rồi em thử kiểm tra lại bằng ví dụ nhé. "
            "Trong DSA, khái niệm chỉ thật sự rõ khi em gắn nó với input, trạng thái cần lưu, "
            "và thao tác cập nhật sau mỗi bước.\n\n"
            "Em có thể đưa một bài cụ thể đang học để mình hỏi dẫn theo đúng ngữ cảnh không?"
        )
        response, review = self._generate_reviewed_response(guideline, trace_summary="Answered theory question")
        self._trace("Theory Explainer", "ok", "Answered theory question", safe_to_send=review.safe_to_send)
        return AgentTurn(Intent.ASK_THEORY, response, self.state, self._last_classification, pedagogy_review=review)

    def generate_session_title(self, messages: list[str]) -> str:
        title = self.session_title_agent.generate(messages)
        self.state.chat_title = title
        self._trace("Session Title Agent", "ok", f"Generated title: {title}")
        return title

    def _ensure_test_suite(self) -> TestSuite:
        if self.state.generated_tests:
            return self.state.generated_tests[-1]

        problem = self.state.current_problem or "Bài toán chưa được mô tả rõ"
        return self._generate_test_suite(problem, self._last_classification)

    def _generate_test_suite(self, problem: str, classification: Classification | None) -> TestSuite:
        test_suite = self.testcase_generator.generate(problem, classification)
        self.state.generated_tests.append(test_suite)
        validation_tests = sum(1 for test in test_suite.tests if test.purpose == TestPurpose.VALIDATION)
        trace_tests = len(test_suite.tests) - validation_tests
        self._trace(
            "Testcase Generator",
            "ok",
            f"Generated {len(test_suite.tests)} tests",
            validation_tests=validation_tests,
            trace_only_tests=trace_tests,
        )
        return test_suite

    def _generate_reviewed_response(self, guideline: str, trace_summary: str = "Generated Socratic response") -> tuple[str, PedagogyReview]:
        response = self.response_generator.generate(self.state, guideline)
        response, review = self._review_response(response)
        self._trace("Finalize", "ok", trace_summary, safe_to_send=review.safe_to_send)
        return response, review

    def _review_response(self, response: str) -> tuple[str, PedagogyReview]:
        review = self.pedagogy_critic.review(response, self.state)
        self.state.pedagogy_flags.append(review)
        if not review.safe_to_send and review.revision_instruction:
            response = self.response_generator.revise(response, review.revision_instruction)
            review = self.pedagogy_critic.review(response, self.state)
            self.state.pedagogy_flags.append(review)
        return response, review

    def _code_review_guideline(self, code: str, validation_status: str) -> str:
        validation_note = (
            "Mình đã chuẩn bị testcase nội bộ cho bài này. "
            f"Trạng thái chạy sandbox hiện tại: `{validation_status}`."
        )
        if validation_status == "SKIPPED":
            validation_note += " Nghĩa là bước chạy code chưa thực hiện được, nên ta sẽ kiểm bằng trace và edge case trước."
        elif validation_status != "PASSED":
            validation_note += " Có dấu hiệu cần soi lại bằng case nhỏ thay vì sửa vội toàn bộ code."

        return (
            f"{analyze_code(code)}\n\n"
            f"{validation_note}\n\n"
            "Em thử chọn một testcase nhỏ và ghi lại giá trị biến chính sau từng bước nhé?"
        )

    def _trace(self, node_name: str, status: str, summary: str, **metadata: str | int | float | bool | None) -> None:
        self.state.agent_trace.append(
            AgentTraceItem(
                node_name=node_name,
                status=status,
                summary=summary,
                metadata=metadata,
            )
        )
