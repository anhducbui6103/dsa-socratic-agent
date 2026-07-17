from __future__ import annotations

from ..llm_client import LlmClient
from .json_tools import loads_json_object


class SessionTitleAgent:
    """Creates a concise title from conversation context through the LLM."""

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def generate(self, messages: list[str]) -> str:
        joined = "\n".join(message.strip() for message in messages if message.strip())[:2000]
        if not joined:
            return "Phiên mới"

        system_prompt = (
            "Bạn là Session Title Agent cho DSA Tutor. "
            "Chỉ trả về JSON hợp lệ, không markdown. "
            "Nhiệm vụ là tạo tiêu đề ngắn cho phiên học. "
            "Tiêu đề nên dài 3-6 từ, súc tích, phản ánh chủ đề chính, "
            "và không chứa code dài hoặc dữ liệu nhạy cảm."
        )
        user_prompt = (
            "Hãy đặt tiêu đề ngắn cho phiên chat học DSA sau. JSON schema bắt buộc:\n"
            '{"title":"string"}\n\n'
            f"Nội dung đầu phiên:\n{joined}"
        )
        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        title = str(data.get("title", "")).strip()
        return title[:48] if title else "Phiên học DSA"
