from __future__ import annotations

from dataclasses import dataclass

from ..llm_client import LlmClient
from ..models import Intent, LearningState
from .json_tools import loads_json_object


@dataclass
class IntentDetectionResult:
    intent: Intent
    confidence: float
    reasoning_summary: str


class IntentDetectorAgent:
    """LLM-only intent detector.

    This agent intentionally avoids keyword routing. The model must infer the
    user's learning intent from the complete message and return a typed intent.
    """

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def detect(self, message: str, state: LearningState | None = None) -> Intent:
        return self.detect_with_metadata(message, state).intent

    def detect_with_metadata(self, message: str, state: LearningState | None = None) -> IntentDetectionResult:
        system_prompt = (
            "Bạn là Intent Detector Agent cho một DSA Socratic Tutor. "
            "Nhiệm vụ là phân loại ý định học tập của sinh viên theo NGỮ NGHĨA của lượt nhắn hiện tại, "
            "có tham chiếu LearningState nếu được cung cấp. "
            "Không dùng luật keyword cứng. Không giải bài. Không trả lời sư phạm. "
            "Hãy suy luận thầm, rồi chỉ xuất JSON hợp lệ.\n\n"
            "Intent taxonomy:\n"
            "1. ASK_THEORY: sinh viên đang hỏi khái niệm, định nghĩa, cách hoạt động, hoặc so sánh kiến thức DSA; "
            "trọng tâm là hiểu lý thuyết, chưa đưa ra hướng giải riêng cho một bài cụ thể.\n"
            "2. SUBMIT_PROBLEM: sinh viên đang nêu một bài toán, mô tả đề, input/output, ràng buộc, hoặc muốn bắt đầu giải một bài mới.\n"
            "3. REQUEST_HINT: sinh viên đang xin THÊM gợi ý hoặc tăng mức hỗ trợ. Đây là yêu cầu meta về mức độ trợ giúp, "
            "không phải nội dung lời giải của riêng họ.\n"
            "4. SUBMIT_APPROACH: sinh viên đang đưa ra ý tưởng, giả thuyết, hướng đi, phân tích, trace, hoặc trả lời câu hỏi Socratic. "
            "Dù ý tưởng đúng hay sai, nếu họ đang đóng góp reasoning của họ thì chọn intent này.\n"
            "5. SUBMIT_CODE: sinh viên gửi code, pseudo-code có dạng triển khai, hoặc yêu cầu review/debug một đoạn cài đặt cụ thể.\n"
            "6. ASK_DIRECT_SOLUTION: sinh viên muốn có đáp án hoàn chỉnh, lời giải luôn, full code, hoặc muốn bỏ qua chế độ gợi ý.\n\n"
            "Decision rules:\n"
            "- Ưu tiên hành động giao tiếp chính của lượt hiện tại, không phải chủ đề bề mặt.\n"
            "- REQUEST_HINT chỉ dùng khi sinh viên muốn tutor tăng mức hỗ trợ. "
            "Nếu họ đang mô tả suy nghĩ của mình, kể cả rất ngắn như 'em nghĩ dùng DFS', thì là SUBMIT_APPROACH.\n"
            "- Nếu vừa có lý thuyết vừa có hướng giải cá nhân, ưu tiên SUBMIT_APPROACH vì đó là đóng góp reasoning.\n"
            "- Nếu có code thực sự hoặc block code, ưu tiên SUBMIT_CODE hơn SUBMIT_APPROACH.\n"
            "- Nếu sinh viên yêu cầu giải luôn hoặc full đáp án, ưu tiên ASK_DIRECT_SOLUTION.\n"
            "- Dùng LearningState để phân biệt: khi next_action cho thấy tutor đang chờ student attempt, "
            "một câu trả lời ngắn nêu hướng nghĩ thường là SUBMIT_APPROACH, không phải REQUEST_HINT.\n"
            "- Không tự tạo intent mới. Nếu mơ hồ, chọn intent gần nhất với hành động học tập có xác suất cao nhất.\n\n"
            "Đặc biệt để tách REQUEST_HINT vs SUBMIT_APPROACH:\n"
            "- REQUEST_HINT = xin thêm trợ giúp từ tutor.\n"
            "- SUBMIT_APPROACH = tự đưa nội dung suy luận của bản thân.\n"
            "- Câu như 'em nghĩ sort rồi binary search', 'chắc là DFS', 'em sẽ lưu prefix sum' đều là SUBMIT_APPROACH.\n"
            "- Câu như 'hint tiếp', 'gợi ý thêm', 'nâng mức hint', 'em vẫn bí, cho thêm hướng' là REQUEST_HINT.\n"
            "- Nếu message vừa ngắn vừa mơ hồ, hãy dựa vào việc nó có đang đóng góp reasoning hay không.\n\n"
            "Output schema cố định:\n"
            '{"intent":"ASK_THEORY|SUBMIT_PROBLEM|REQUEST_HINT|SUBMIT_APPROACH|SUBMIT_CODE|ASK_DIRECT_SOLUTION","confidence":0.0,"reasoning_summary":"string"}'
        )
        state_context = _render_state_context(state)
        user_prompt = (
            "Phân loại intent cho message sau.\n"
            "Không in ra chain-of-thought chi tiết; chỉ trả summary ngắn.\n\n"
            "Few-shot examples:\n"
            '- Message: "Em nghĩ nên dùng DFS trước."\n'
            '  Output: {"intent":"SUBMIT_APPROACH","confidence":0.92,"reasoning_summary":"Student proposes a solving direction, not asking for more help."}\n'
            '- Message: "Cho em hint tiếp."\n'
            '  Output: {"intent":"REQUEST_HINT","confidence":0.98,"reasoning_summary":"Student explicitly asks for a higher hint level."}\n'
            '- Message: "Em chưa hiểu DP là gì."\n'
            '  Output: {"intent":"ASK_THEORY","confidence":0.97,"reasoning_summary":"Student asks for a concept explanation."}\n'
            '- Message: "Đây là code của em: def solve(nums): return nums[0]"\n'
            '  Output: {"intent":"SUBMIT_CODE","confidence":0.99,"reasoning_summary":"Student submits implementation for review."}\n'
            '- Message: "Em nghĩ có thể sort rồi binary search."\n'
            '  Output: {"intent":"SUBMIT_APPROACH","confidence":0.95,"reasoning_summary":"Student shares a candidate strategy."}\n'
            '- Message: "Làm luôn giúp em."\n'
            '  Output: {"intent":"ASK_DIRECT_SOLUTION","confidence":0.98,"reasoning_summary":"Student requests the full solution directly."}\n'
            '- Message: "Nếu em lưu tổng tiền tố thì có ổn không?"\n'
            '  Output: {"intent":"SUBMIT_APPROACH","confidence":0.88,"reasoning_summary":"Student tests an idea and seeks feedback on their reasoning."}\n'
            '- Message: "Em vẫn chưa hiểu, cho em thêm một gợi ý nữa."\n'
            '  Output: {"intent":"REQUEST_HINT","confidence":0.96,"reasoning_summary":"Student asks the tutor to escalate support."}\n\n'
            "Negative contrast reminders:\n"
            "- Đừng gán REQUEST_HINT chỉ vì message ngắn.\n"
            "- Đừng gán REQUEST_HINT nếu student đang đề xuất thuật toán hoặc cách lưu state.\n"
            "- Đừng gán ASK_THEORY nếu student đang bàn cách giải cho bài hiện tại.\n"
            "- Đừng gán SUBMIT_APPROACH nếu student thực chất muốn full answer.\n\n"
            f"{state_context}"
            f"Message:\n{message}"
        )
        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        intent = _coerce_intent(str(data["intent"]))
        confidence = _coerce_confidence(data.get("confidence"))
        reasoning_summary = str(data.get("reasoning_summary", "")).strip() or "No summary provided."
        return IntentDetectionResult(intent=intent, confidence=confidence, reasoning_summary=reasoning_summary)


def _render_state_context(state: LearningState | None) -> str:
    if state is None:
        return "LearningState:\n- unavailable\n\n"
    return (
        "LearningState:\n"
        f"- Current problem: {state.current_problem}\n"
        f"- Problem type: {state.problem_type}\n"
        f"- Hint level: {state.hint_level}\n"
        f"- Next action: {state.next_action}\n"
        f"- Recent student attempts: {state.student_attempts[-3:]}\n\n"
    )


def _coerce_confidence(raw_confidence: object) -> float:
    try:
        value = float(raw_confidence)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, value))


def _coerce_intent(raw_intent: str) -> Intent:
    normalized = raw_intent.strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "SUBMITS_PROBLEM": Intent.SUBMIT_PROBLEM,
        "SUBMIT_PROBLEMS": Intent.SUBMIT_PROBLEM,
        "PROBLEM_SUBMIT": Intent.SUBMIT_PROBLEM,
        "REQUEST_HINTS": Intent.REQUEST_HINT,
        "SUBMITS_CODE": Intent.SUBMIT_CODE,
        "DIRECT_SOLUTION": Intent.ASK_DIRECT_SOLUTION,
        "ASK_SOLUTION": Intent.ASK_DIRECT_SOLUTION,
        "SOLUTION_REQUEST": Intent.ASK_DIRECT_SOLUTION,
    }
    if normalized in aliases:
        return aliases[normalized]
    return Intent(normalized)
