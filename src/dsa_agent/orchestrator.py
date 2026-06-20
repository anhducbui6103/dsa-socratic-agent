from __future__ import annotations

from .classifier import classify_problem
from .code_analysis import analyze_code
from .hints import direct_solution_guard, next_hint
from .intent import detect_intent
from .models import AgentTurn, Intent, LearningState


class DsaLearningAgent:
    def __init__(self) -> None:
        self.state = LearningState()
        self._last_classification = None

    def handle(self, message: str) -> AgentTurn:
        intent = detect_intent(message)
        self.state.student_attempts.append(message)

        if intent == Intent.SUBMIT_PROBLEM:
            classification = classify_problem(message)
            self._last_classification = classification
            self.state.current_problem = message
            self.state.problem_type = classification.topic
            self.state.concepts = classification.key_signals
            self.state.hint_level = 0
            self.state.next_action = "ask_student_understanding"
            response = (
                f"Mình nghiêng về nhóm `{classification.topic}` "
                f"(độ tin cậy khoảng {classification.confidence:.0%}).\n\n"
                "Trước khi đi vào cách làm, em thử tự mô tả lại input/output và ràng buộc chính của bài. "
                "Nếu phải giải tay một ví dụ nhỏ, em sẽ theo dõi thông tin nào sau mỗi bước?"
            )
            return AgentTurn(intent, response, self.state, classification)

        if intent == Intent.REQUEST_HINT:
            self.state.hint_level = min(self.state.hint_level + 1, 3)
            self.state.next_action = "wait_for_student_attempt"
            return AgentTurn(intent, next_hint(self.state, self._last_classification), self.state, self._last_classification)

        if intent == Intent.SUBMIT_CODE:
            self.state.next_action = "review_trace_or_edge_case"
            return AgentTurn(intent, analyze_code(message), self.state, self._last_classification)

        if intent == Intent.ASK_DIRECT_SOLUTION:
            self.state.next_action = "redirect_to_socratic_hint"
            return AgentTurn(intent, direct_solution_guard(), self.state, self._last_classification)

        if intent == Intent.SUBMIT_APPROACH:
            self.state.next_action = "probe_correctness"
            response = (
                "Ý tưởng của em đã có hướng rồi. Giờ mình kiểm tra bằng phản ví dụ nhỏ nhé: "
                "điều kiện nào làm cách làm của em cập nhật sai hoặc bỏ sót trường hợp?\n\n"
                "Em thử nêu độ phức tạp dự kiến và một edge case mà em thấy đáng ngại nhất."
            )
            return AgentTurn(intent, response, self.state, self._last_classification)

        response = (
            "Mình giải thích ngắn trước, rồi em thử kiểm tra lại bằng ví dụ nhé. "
            "Trong DSA, khái niệm chỉ thật sự rõ khi em gắn nó với input, trạng thái cần lưu, "
            "và thao tác cập nhật sau mỗi bước.\n\n"
            "Em có thể đưa một bài cụ thể đang học để mình hỏi dẫn theo đúng ngữ cảnh không?"
        )
        self.state.next_action = "ask_for_concrete_problem"
        return AgentTurn(intent, response, self.state, self._last_classification)
