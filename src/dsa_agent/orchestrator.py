from __future__ import annotations

import json

from .code_analysis import analyze_code
from .hints import direct_solution_guard, next_hint
from .llm_client import GeminiLlmClient, LlmClient
from .models import (
    AgentTurn,
    AgentTraceItem,
    Classification,
    GeneratedTestCase,
    Intent,
    LearningState,
    PedagogyReview,
    TestCategory,
    TestPurpose,
    TestSuite,
)
from .quality import CodeExecutionValidatorAgent


class DsaLearningAgent:
    def __init__(self, enable_execution: bool = False, llm_client: LlmClient | None = None) -> None:
        self.state = LearningState()
        self._last_classification: Classification | None = None
        self.llm_client = llm_client or GeminiLlmClient.from_env()
        self.execution_validator = CodeExecutionValidatorAgent(enable_execution=enable_execution)

    def handle(self, message: str) -> AgentTurn:
        intent = self.detect_intent(message)
        self.record_attempt(message)
        return self.run_intent(intent, message)

    def detect_intent(self, message: str) -> Intent:
        intent = self._detect_intent_with_llm(message)
        self._trace(
            "Intent Detector",
            "ok",
            f"Detected {intent.value}",
            intent=intent.value,
        )
        return intent

    def record_attempt(self, message: str) -> None:
        self.state.student_attempts.append(message)
        self._trace("State Update", "ok", "Recorded student attempt", attempts=len(self.state.student_attempts))

    def run_intent(self, intent: Intent, message: str) -> AgentTurn:
        if intent == Intent.SUBMIT_PROBLEM:
            return self.handle_submit_problem(message)
        if intent == Intent.REQUEST_HINT:
            return self.handle_request_hint()
        if intent == Intent.SUBMIT_CODE:
            return self.handle_submit_code(message)
        if intent == Intent.ASK_DIRECT_SOLUTION:
            return self.handle_direct_solution_request()
        if intent == Intent.SUBMIT_APPROACH:
            return self.handle_submit_approach()
        return self.handle_theory_question()

    def handle_submit_problem(self, message: str) -> AgentTurn:
        classification = self._classify_with_llm(message)
        self._trace(
            "Problem Classifier",
            "ok",
            f"Classified as {classification.topic}",
            topic=classification.topic,
            confidence=classification.confidence,
        )
        self._last_classification = classification
        self.state.current_problem = message
        self.state.problem_type = classification.topic
        self.state.concepts = classification.key_signals
        self.state.hint_level = 0

        test_suite = self._generate_testcases_with_llm(message, classification)
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
        self.state.next_action = "ask_student_understanding"

        guideline = (
            f"Mình nghiêng về nhóm `{classification.topic}` "
            f"(độ tin cậy khoảng {classification.confidence:.0%}).\n\n"
            "Trước khi đi vào cách làm, em thử tự mô tả lại input/output và ràng buộc chính của bài. "
            "Nếu phải giải tay một ví dụ nhỏ, em sẽ theo dõi thông tin nào sau mỗi bước?\n\n"
            f"Case tự kiểm gợi ý: `{test_suite.tests[0].name}` - {test_suite.tests[0].rationale}"
        )
        response = self._generate_with_llm(guideline)
        response, review = self._review_response(response)
        self._trace("Finalize", "ok", "Generated Socratic response", safe_to_send=review.safe_to_send)
        return AgentTurn(Intent.SUBMIT_PROBLEM, response, self.state, classification, test_suite=test_suite, pedagogy_review=review)

    def handle_request_hint(self) -> AgentTurn:
        self.state.hint_level = min(self.state.hint_level + 1, 3)
        self.state.next_action = "wait_for_student_attempt"
        guideline = next_hint(self.state, self._last_classification)
        self._trace("Hint Generator", "ok", f"Generated hint level {self.state.hint_level}", hint_level=self.state.hint_level)
        response = self._generate_with_llm(guideline)
        response, review = self._review_response(response)
        self._trace("Finalize", "ok", "Generated Socratic response", safe_to_send=review.safe_to_send)
        return AgentTurn(Intent.REQUEST_HINT, response, self.state, self._last_classification, pedagogy_review=review)

    def handle_submit_code(self, message: str) -> AgentTurn:
        test_suite = self._ensure_test_suite()
        validation = self.execution_validator.validate(message, "python", test_suite)
        self.state.latest_validation = validation
        self._trace(
            "Execution Validator",
            validation.status.value,
            f"Validation status {validation.status.value}",
            passed_count=validation.passed_count,
            failed_count=len(validation.failed_tests),
        )
        self.state.next_action = "review_trace_or_edge_case"
        guideline = self._code_review_response(message, validation.status.value)
        response = self._generate_with_llm(guideline)
        response, review = self._review_response(response)
        self._trace("Finalize", "ok", "Generated code-review response", safe_to_send=review.safe_to_send)
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
        guideline = direct_solution_guard()
        self._trace("Direct Solution Guard", "ok", "Redirected direct solution request")
        response = self._generate_with_llm(guideline)
        response, review = self._review_response(response)
        self._trace("Finalize", "ok", "Generated guarded response", safe_to_send=review.safe_to_send)
        return AgentTurn(Intent.ASK_DIRECT_SOLUTION, response, self.state, self._last_classification, pedagogy_review=review)

    def handle_submit_approach(self) -> AgentTurn:
        self.state.next_action = "probe_correctness"
        guideline = (
            "Ý tưởng của em đã có hướng rồi. Giờ mình kiểm tra bằng phản ví dụ nhỏ nhé: "
            "điều kiện nào có thể làm cách làm của em cập nhật sai hoặc bỏ sót trường hợp?\n\n"
            "Em thử nêu độ phức tạp dự kiến và một edge case mà em thấy đáng ngại nhất."
        )
        response = self._generate_with_llm(guideline)
        response, review = self._review_response(response)
        self._trace("Approach Reviewer", "ok", "Reviewed student approach", safe_to_send=review.safe_to_send)
        return AgentTurn(Intent.SUBMIT_APPROACH, response, self.state, self._last_classification, pedagogy_review=review)

    def handle_theory_question(self) -> AgentTurn:
        guideline = (
            "Mình giải thích ngắn trước, rồi em thử kiểm tra lại bằng ví dụ nhé. "
            "Trong DSA, khái niệm chỉ thật sự rõ khi em gắn nó với input, trạng thái cần lưu, "
            "và thao tác cập nhật sau mỗi bước.\n\n"
            "Em có thể đưa một bài cụ thể đang học để mình hỏi dẫn theo đúng ngữ cảnh không?"
        )
        self.state.next_action = "ask_for_concrete_problem"
        response = self._generate_with_llm(guideline)
        response, review = self._review_response(response)
        self._trace("Theory Explainer", "ok", "Answered theory question", safe_to_send=review.safe_to_send)
        return AgentTurn(Intent.ASK_THEORY, response, self.state, self._last_classification, pedagogy_review=review)

    def generate_session_title(self, messages: list[str]) -> str:
        title = self._generate_session_title_with_llm(messages)
        self.state.chat_title = title
        self._trace("Session Title Agent", "ok", f"Generated title: {title}")
        return title

    def _detect_intent_with_llm(self, message: str) -> Intent:
        system_prompt = (
            "Bạn là Intent Detector cho DSA Socratic Tutor. Chỉ trả về JSON hợp lệ, không markdown. "
            "Intent hợp lệ: ASK_THEORY, SUBMIT_PROBLEM, REQUEST_HINT, SUBMIT_APPROACH, SUBMIT_CODE, ASK_DIRECT_SOLUTION. "
            "Nếu người học xin full code, đáp án, lời giải hoàn chỉnh thì chọn ASK_DIRECT_SOLUTION. "
            "Nếu input chứa code, def, class, hoặc code block thì chọn SUBMIT_CODE."
        )
        user_prompt = (
            "Phân loại intent cho message sau. JSON schema bắt buộc:\n"
            '{"intent":"ASK_THEORY|SUBMIT_PROBLEM|REQUEST_HINT|SUBMIT_APPROACH|SUBMIT_CODE|ASK_DIRECT_SOLUTION"}\n\n'
            f"Message:\n{message}"
        )
        data = _loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        return _coerce_intent(str(data["intent"]))

    def _ensure_test_suite(self) -> TestSuite:
        if self.state.generated_tests:
            return self.state.generated_tests[-1]

        problem = self.state.current_problem or "Bài toán chưa được mô tả rõ"
        test_suite = self._generate_testcases_with_llm(problem, self._last_classification)
        self.state.generated_tests.append(test_suite)
        return test_suite

    def _trace(self, node_name: str, status: str, summary: str, **metadata: str | int | float | bool | None) -> None:
        self.state.agent_trace.append(
            AgentTraceItem(
                node_name=node_name,
                status=status,
                summary=summary,
                metadata=metadata,
            )
        )

    def _review_response(self, response: str) -> tuple[str, PedagogyReview]:
        review = self._review_pedagogy_with_llm(response)
        self.state.pedagogy_flags.append(review)
        if not review.safe_to_send and review.revision_instruction:
            response = self._revise_with_llm(response, review.revision_instruction)
            review = self._review_pedagogy_with_llm(response)
            self.state.pedagogy_flags.append(review)
        return response, review

    def _classify_with_llm(self, problem: str) -> Classification:
        system_prompt = (
            "Bạn là DSA Problem Classifier. Chỉ trả về JSON hợp lệ, không markdown. "
            "Các topic hợp lệ: array_string, two_pointers, sliding_window, hash_map, stack, "
            "queue_bfs, tree_dfs, graph, greedy, dynamic_programming, sorting_searching."
        )
        user_prompt = (
            "Phân loại bài toán DSA sau. JSON schema bắt buộc:\n"
            '{"topic":"string","pattern":"string","confidence":0.0,'
            '"key_signals":["string"],"recommended_hint_path":["string"]}\n\n'
            f"Đề bài:\n{problem}"
        )
        data = _loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        return Classification(
            topic=str(data["topic"]),
            pattern=str(data.get("pattern", "general")),
            confidence=float(data.get("confidence", 0.7)),
            key_signals=[str(item) for item in data.get("key_signals", [])],
            recommended_hint_path=[str(item) for item in data.get("recommended_hint_path", [])],
        )

    def _generate_testcases_with_llm(self, problem: str, classification: Classification | None) -> TestSuite:
        topic = classification.topic if classification else "unknown"
        system_prompt = (
            "Bạn là Testcase Generator Agent cho bài DSA. Chỉ trả về JSON hợp lệ, không markdown. "
            "Testcase ưu tiên hỗ trợ học tập, trace tay và kiểm edge case. "
            "Nếu chưa chắc expected output, đặt null."
        )
        user_prompt = (
            "Sinh testcase cho bài dưới đây. JSON schema bắt buộc:\n"
            '{"problem_id":"string","language":"python","coverage_notes":["string"],'
            '"tests":[{"name":"string","input":"string","expected_output":"string|null",'
            '"purpose":"validation|trace_only","category":"basic|edge|adversarial|stress",'
            '"rationale":"string"}]}\n\n'
            "For function-style solutions, set input as Python assignments matching parameter names, for example: nums = [2, 7, 11, 15]\\ntarget = 9.\n"
            "Set expected_output when the expected result is clear, for example: [0, 1].\n\n"
            f"Topic: {topic}\n"
            f"Đề bài:\n{problem}"
        )
        data = _loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        tests = []
        for item in data.get("tests", []):
            category_value = str(item.get("category", "basic"))
            try:
                category = TestCategory(category_value)
            except ValueError:
                category = TestCategory.BASIC
            expected_output = item.get("expected_output")
            purpose_value = str(item.get("purpose") or ("validation" if expected_output is not None else "trace_only"))
            try:
                purpose = TestPurpose(purpose_value)
            except ValueError:
                purpose = TestPurpose.TRACE_ONLY
            tests.append(
                GeneratedTestCase(
                    name=str(item.get("name", "llm_case")),
                    input=str(item.get("input", "")),
                    expected_output=expected_output,
                    category=category,
                    rationale=str(item.get("rationale", "")),
                    purpose=purpose,
                )
            )
        if not tests:
            raise ValueError("LLM testcase generator returned no tests.")

        return TestSuite(
            problem_id=str(data.get("problem_id", "llm-generated")),
            language=str(data.get("language", "python")),
            tests=tests,
            coverage_notes=[str(item) for item in data.get("coverage_notes", [])],
        )

    def _review_pedagogy_with_llm(self, response: str) -> PedagogyReview:
        system_prompt = (
            "Bạn là Pedagogy Critic Agent cho DSA Socratic Tutor. Chỉ trả về JSON hợp lệ, không markdown. "
            "Kiểm tra xem phản hồi có lộ full code/lời giải, thiếu câu hỏi gợi mở, "
            "sai hint level, hoặc quá trực tiếp không."
        )
        user_prompt = (
            "Review phản hồi sau. JSON schema bắt buộc:\n"
            '{"safe_to_send":true,"risk_level":"low|medium|high","issues":["string"],'
            '"revision_instruction":null}\n\n'
            f"Hint level: {self.state.hint_level}\n"
            f"Problem type: {self.state.problem_type}\n"
            f"Response:\n{response}"
        )
        data = _loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        return PedagogyReview(
            safe_to_send=bool(data.get("safe_to_send", False)),
            risk_level=str(data.get("risk_level", "medium")),
            issues=[str(item) for item in data.get("issues", [])],
            revision_instruction=data.get("revision_instruction"),
        )

    def _generate_session_title_with_llm(self, messages: list[str]) -> str:
        joined = "\n".join(message.strip() for message in messages if message.strip())[:2000]
        if not joined:
            return "Phiên mới"

        system_prompt = (
            "Bạn là Session Title Agent cho DSA Tutor. "
            "Chỉ trả về JSON hợp lệ, không markdown. Tiêu đề 3-6 từ, ngắn, không chứa code dài hoặc dữ liệu nhạy cảm."
        )
        user_prompt = (
            "Hãy đặt tiêu đề ngắn cho phiên chat học DSA sau. JSON schema bắt buộc:\n"
            '{"title":"string"}\n\n'
            f"Nội dung đầu phiên:\n{joined}"
        )
        try:
            data = _loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
            title = str(data.get("title", "")).strip()
        except Exception:
            title = ""

        return _fallback_title(joined) if not title else title[:48]

    def _revise_with_llm(self, response: str, revision_instruction: str) -> str:
        system_prompt = (
            "Bạn là AI Tutor DSA viết theo phương pháp Socratic. "
            "Hãy sửa phản hồi để an toàn sư phạm. Không đưa full code hoặc lời giải hoàn chỉnh."
        )
        user_prompt = (
            f"Instruction từ Pedagogy Critic:\n{revision_instruction}\n\n"
            f"Phản hồi cần sửa:\n{response}"
        )
        return self.llm_client.generate(system_prompt, user_prompt)

    def _generate_with_llm(self, guideline: str) -> str:
        system_prompt = (
            "Bạn là AI Tutor dạy Cấu trúc dữ liệu và Giải thuật bằng phương pháp Socratic. "
            "Bạn phải tự sinh phản hồi/gợi ý phù hợp với trạng thái học tập hiện tại. "
            "Không đưa full code hoặc lời giải hoàn chỉnh. Không nói thẳng đáp án cuối. "
            "Giữ tiếng Việt tự nhiên, ngắn gọn, tập trung 1-2 câu hỏi/gợi ý chính."
        )
        user_prompt = (
            "Hãy sinh phản hồi tiếp theo cho sinh viên dựa trên state và policy dưới đây.\n\n"
            f"Problem type: {self.state.problem_type}\n"
            f"Hint level: {self.state.hint_level}\n"
            f"Current problem: {self.state.current_problem}\n"
            f"Concepts/signals: {', '.join(self.state.concepts)}\n"
            f"Next action: {self.state.next_action}\n"
            f"Recent student attempts: {self.state.student_attempts[-3:]}\n\n"
            "Policy:\n"
            "- Không đưa code hoàn chỉnh.\n"
            "- Không nói thẳng đáp án cuối.\n"
            "- Nếu là hint level thấp, hãy hỏi định hướng thay vì nêu công thức.\n"
            "- Nếu sinh viên gửi code, hãy hỏi về trace, edge case hoặc độ phức tạp.\n"
            "- Có thể dùng guideline nội bộ dưới đây để hiểu ý định sư phạm, nhưng không copy máy móc.\n\n"
            f"Internal guideline:\n{guideline}"
        )
        return self.llm_client.generate(system_prompt, user_prompt)

    def _code_review_response(self, code: str, validation_status: str) -> str:
        analysis = analyze_code(code)
        validation_note = (
            "Mình đã chuẩn bị testcase nội bộ cho bài này. "
            f"Trạng thái chạy sandbox hiện tại: `{validation_status}`."
        )

        if validation_status == "SKIPPED":
            validation_note += " Nghĩa là bước chạy code chưa thực hiện được, nên ta sẽ kiểm bằng trace và edge case trước."
        elif validation_status != "PASSED":
            validation_note += " Có dấu hiệu cần soi lại bằng case nhỏ thay vì sửa vội toàn bộ code."

        return f"{analysis}\n\n{validation_note}\n\nEm thử chọn một testcase nhỏ và ghi lại giá trị biến chính sau từng bước nhé?"


def _loads_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("Expected LLM to return a JSON object.")
    return data


def _fallback_title(text: str) -> str:
    normalized = text.lower()
    if "def " in normalized or "class " in normalized or "```" in text:
        return "Phân tích code"
    if "maximum subarray" in normalized or "đoạn con" in normalized:
        return "Maximum Subarray"
    if "bfs" in normalized or "dfs" in normalized or "đồ thị" in normalized or "graph" in normalized:
        return "Bài đồ thị"
    if "dp" in normalized or "quy hoạch động" in normalized:
        return "Bài quy hoạch động"
    if "sliding" in normalized or "cửa sổ" in normalized:
        return "Sliding Window"
    words = " ".join(text.split()[:5])
    return words or "Phiên học DSA"


def _coerce_intent(raw_intent: str) -> Intent:
    normalized = raw_intent.strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "SUBMITS_PROBLEM": Intent.SUBMIT_PROBLEM,
        "SUBMIT_PROBLEMS": Intent.SUBMIT_PROBLEM,
        "PROBLEM_SUBMIT": Intent.SUBMIT_PROBLEM,
        "PROBLEM": Intent.SUBMIT_PROBLEM,
        "REQUEST_HINTS": Intent.REQUEST_HINT,
        "HINT": Intent.REQUEST_HINT,
        "SUBMITS_CODE": Intent.SUBMIT_CODE,
        "CODE": Intent.SUBMIT_CODE,
        "DIRECT_SOLUTION": Intent.ASK_DIRECT_SOLUTION,
        "ASK_SOLUTION": Intent.ASK_DIRECT_SOLUTION,
        "SOLUTION_REQUEST": Intent.ASK_DIRECT_SOLUTION,
        "APPROACH": Intent.SUBMIT_APPROACH,
        "THEORY": Intent.ASK_THEORY,
    }
    if normalized in aliases:
        return aliases[normalized]
    return Intent(normalized)
