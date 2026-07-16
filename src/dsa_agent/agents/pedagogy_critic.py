from __future__ import annotations

from ..llm_client import LlmClient
from ..models import LearningState, PedagogyReview
from .json_tools import loads_json_object


class PedagogyCriticAgent:
    """Reviews a draft tutor response before it reaches the learner."""

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def review(self, response: str, state: LearningState) -> PedagogyReview:
        system_prompt = (
            "Bạn là Pedagogy Critic Agent cho DSA Socratic Tutor. "
            "Chỉ trả về JSON hợp lệ, không markdown. "
            "Kiểm tra xem phản hồi có lộ full code/lời giải, thiếu câu hỏi gợi mở, "
            "sai hint level, hoặc quá trực tiếp không."
        )
        user_prompt = (
            "Review phản hồi sau. JSON schema bắt buộc:\n"
            '{"safe_to_send":true,"risk_level":"low|medium|high","issues":["string"],'
            '"revision_instruction":null}\n\n'
            f"Hint level: {state.hint_level}\n"
            f"Problem type: {state.problem_type}\n"
            f"Next action: {state.next_action}\n"
            f"Response:\n{response}"
        )
        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        return PedagogyReview(
            safe_to_send=bool(data.get("safe_to_send", False)),
            risk_level=str(data.get("risk_level", "medium")),
            issues=[str(item) for item in data.get("issues", [])],
            revision_instruction=data.get("revision_instruction"),
        )
