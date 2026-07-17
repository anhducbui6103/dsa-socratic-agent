from __future__ import annotations

from ..llm_client import LlmClient
from ..models import LearningState, PedagogyReview
from .json_tools import loads_json_object


class PedagogyCriticAgent:
    """Reviews a tutor response before it reaches the learner.

    The critic evaluates the response from a pedagogical perspective rather than
    simply checking for unsafe content. Its primary goal is to ensure the tutor
    follows the Socratic teaching strategy.
    """

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def review(self, response: str, state: LearningState) -> PedagogyReview:
        system_prompt = (
            "Bạn là Pedagogy Critic Agent cho DSA Socratic Tutor. "
            "Chỉ trả về JSON hợp lệ, không markdown. "
            "Nhiệm vụ là review phản hồi của tutor theo góc nhìn sư phạm Socratic, "
            "không giải bài và không viết lại câu trả lời hoàn chỉnh.\n\n"
            "Tiêu chí đánh giá:\n"
            "- Ưu tiên Socratic: phản hồi nên giúp người học tự suy luận thay vì giải thay.\n"
            "- Tôn trọng learning state hiện tại, đặc biệt là `hint_level`, `next_action`, `problem_type`.\n"
            "- Không tự nhảy lên hint level cao hơn.\n"
            "- Level 1: chỉ nên định hướng, hỏi mở, gợi ý nhỏ; không thuật toán cụ thể, pseudo-code, code.\n"
            "- Level 2: được gợi ý thuật toán, cấu trúc dữ liệu hoặc chiến lược; không full algorithm, pseudo-code hoàn chỉnh, code.\n"
            "- Level 3: được pseudo-code, skeleton hoặc partial code; chưa nên là full solution nếu người học chưa xin đáp án trực tiếp.\n"
            "- Nếu người học chưa yêu cầu đáp án trực tiếp thì tránh full code, lời giải hoàn chỉnh, hoặc mô tả trọn thuật toán từng bước.\n"
            "- Một phản hồi tốt thường tạo cơ hội cho người học trả lời tiếp: câu hỏi phản biện, trace, dự đoán, hoặc edge case.\n"
            "- Nếu state cho thấy đang xử lý yêu cầu đáp án trực tiếp thì phản hồi đầy đủ hơn có thể chấp nhận được."
        )

        user_prompt = (
            "Hãy review phản hồi sau. JSON schema bắt buộc:\n"
            '{"safe_to_send":true,"risk_level":"low|medium|high","issues":["string"],"revision_instruction":null}\n\n'
            "Quy tắc output:\n"
            "- `issues`: liệt kê ngắn gọn các vấn đề nếu có.\n"
            "- `revision_instruction`: nếu `safe_to_send=false`, mô tả tutor nên sửa theo hướng nào; không viết lại response, không giải bài; nếu không cần sửa thì trả `null`.\n\n"
            f"Current problem: {state.current_problem}\n"
            f"Problem type: {state.problem_type}\n"
            f"Hint level: {state.hint_level}\n"
            f"Next action: {state.next_action}\n"
            f"Student attempts: {state.student_attempts[-5:]}\n\n"
            f"Tutor response:\n{response}"
        )

        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))

        return PedagogyReview(
            safe_to_send=bool(data.get("safe_to_send", False)),
            risk_level=str(data.get("risk_level", "medium")),
            issues=[str(item) for item in data.get("issues", [])],
            revision_instruction=data.get("revision_instruction"),
        )
