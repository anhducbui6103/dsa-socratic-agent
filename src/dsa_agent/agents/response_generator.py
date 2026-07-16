from __future__ import annotations

from ..llm_client import LlmClient
from ..models import LearningState


class SocraticResponseAgent:
    """Generates and revises learner-facing Socratic responses."""

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def generate(self, state: LearningState, guideline: str) -> str:
        system_prompt = (
            "Bạn là AI Tutor dạy Cấu trúc dữ liệu và Giải thuật bằng phương pháp Socratic. "
            "Bạn phải tự sinh phản hồi/gợi ý phù hợp với trạng thái học tập hiện tại. "
            "Không đưa full code hoặc lời giải hoàn chỉnh. Không nói thẳng đáp án cuối. "
            "Giữ tiếng Việt tự nhiên, ngắn gọn, tập trung 1-2 câu hỏi/gợi ý chính."
        )
        user_prompt = (
            "Hãy sinh phản hồi tiếp theo cho sinh viên dựa trên state và policy dưới đây.\n\n"
            f"Problem type: {state.problem_type}\n"
            f"Hint level: {state.hint_level}\n"
            f"Current problem: {state.current_problem}\n"
            f"Concepts/signals: {', '.join(state.concepts)}\n"
            f"Next action: {state.next_action}\n"
            f"Recent student attempts: {state.student_attempts[-3:]}\n\n"
            "Policy:\n"
            "- Không đưa code hoàn chỉnh.\n"
            "- Không nói thẳng đáp án cuối.\n"
            "- Nếu là hint level thấp, hãy hỏi định hướng thay vì nêu công thức.\n"
            "- Nếu sinh viên gửi code, hãy hỏi về trace, edge case hoặc độ phức tạp.\n"
            "- Có thể dùng guideline nội bộ dưới đây để hiểu ý định sư phạm, nhưng không copy máy móc.\n\n"
            f"Internal guideline:\n{guideline}"
        )
        return self.llm_client.generate(system_prompt, user_prompt)

    def revise(self, response: str, revision_instruction: str) -> str:
        system_prompt = (
            "Bạn là AI Tutor DSA viết theo phương pháp Socratic. "
            "Hãy sửa phản hồi để an toàn sư phạm. Không đưa full code hoặc lời giải hoàn chỉnh."
        )
        user_prompt = (
            f"Instruction từ Pedagogy Critic:\n{revision_instruction}\n\n"
            f"Phản hồi cần sửa:\n{response}"
        )
        return self.llm_client.generate(system_prompt, user_prompt)
