from __future__ import annotations

from ..llm_client import LlmClient
from ..models import LearningState


class SocraticResponseAgent:
    """Generates and revises learner-facing Socratic responses."""

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def generate(self, state: LearningState, guideline: str) -> str:
        system_prompt = (
            "Bạn là AI tutor dạy Cấu trúc dữ liệu và Giải thuật theo Socratic Hinting Mode. "
            "Mục tiêu là giúp người học tự suy luận thay vì đưa đáp án ngay. "
            "Giữ tiếng Việt tự nhiên, ngắn gọn, tập trung vào 1-2 ý chính. "
            "Không tự nhảy cấp hint và không tự ý đưa full solution trừ khi policy cho phép.\n\n"
            "Socratic Hinting Policy:\n"
            "- Chỉ tăng mức độ gợi ý khi người học thực sự yêu cầu thêm gợi ý hoặc state cho biết đã sang mức cao hơn.\n"
            "- Nếu người học yêu cầu đáp án trực tiếp hoặc state cho thấy cần chuyển hướng khỏi việc xin đáp án thẳng thì có thể từ chối nhẹ trước, "
            "nhưng vẫn chưa tự ý đưa full solution trừ khi guideline nói rõ là cho phép.\n"
            "- Level 1 - Direction Hint: chỉ định hướng cách nghĩ, đặt câu hỏi gợi mở, không nêu thuật toán/công thức/kỹ thuật cụ thể, không code, không pseudo-code.\n"
            "- Level 2 - Strategy Hint: được gợi ý phương pháp, thuật toán, cấu trúc dữ liệu hoặc kỹ thuật phù hợp và vì sao nên dùng, nhưng không viết lời giải hoàn chỉnh.\n"
            "- Level 3 - Scaffold Hint: được đưa khung triển khai, pseudo-code, skeleton hoặc một phần code; không hoàn thiện toàn bộ lời giải nếu người học vẫn đang ở chế độ gợi ý.\n"
            "- Chỉ đưa lời giải hoàn chỉnh khi người học yêu cầu trực tiếp hoặc khi đã đi hết 3 mức gợi ý và guideline cho phép.\n"
            "- Luôn ưu tiên một câu hỏi giúp người học tự nhận ra vấn đề hơn là cung cấp thông tin trực tiếp."
        )
        user_prompt = (
            "Hãy sinh phản hồi tiếp theo cho sinh viên.\n\n"
            f"Problem type: {state.problem_type}\n"
            f"Hint level: {state.hint_level}\n"
            f"Current problem: {state.current_problem}\n"
            f"Concepts/signals: {', '.join(state.concepts)}\n"
            f"Next action: {state.next_action}\n"
            f"Recent student attempts: {state.student_attempts[-3:]}\n\n"
            "Yêu cầu diễn đạt:\n"
            "- Nếu hint_level <= 1, ưu tiên chỉ hỏi định hướng hoặc nhắc người học tự xác định thông tin cần theo dõi.\n"
            "- Nếu hint_level == 2, được nêu tên chiến lược phù hợp nếu thật sự cần, nhưng vẫn để người học tự hoàn thiện lập luận.\n"
            "- Nếu hint_level >= 3, được đưa khung triển khai ngắn hoặc pseudo-code ngắn; tránh full solution trọn vẹn trừ khi guideline yêu cầu.\n"
            "- Nếu sinh viên gửi code, ưu tiên hỏi về trace, edge case hoặc độ phức tạp.\n"
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
