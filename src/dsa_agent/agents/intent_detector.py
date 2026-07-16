from __future__ import annotations

from ..llm_client import LlmClient
from ..models import Intent
from .json_tools import loads_json_object


class IntentDetectorAgent:
    """LLM-only intent detector.

    This agent intentionally avoids keyword routing. The model must infer the
    user's learning intent from the complete message and return a typed intent.
    """

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def detect(self, message: str) -> Intent:
        system_prompt = (
            "Bạn là Intent Detector Agent cho DSA Socratic Tutor. "
            "Chỉ trả về JSON hợp lệ, không markdown. "
            "Intent hợp lệ: ASK_THEORY, SUBMIT_PROBLEM, REQUEST_HINT, "
            "SUBMIT_APPROACH, SUBMIT_CODE, ASK_DIRECT_SOLUTION. "
            "Hãy phân loại theo ngữ nghĩa toàn bộ tin nhắn, không dựa vào danh sách keyword cố định."
        )
        user_prompt = (
            "Phân loại intent cho message sau. JSON schema bắt buộc:\n"
            '{"intent":"ASK_THEORY|SUBMIT_PROBLEM|REQUEST_HINT|SUBMIT_APPROACH|SUBMIT_CODE|ASK_DIRECT_SOLUTION"}\n\n'
            f"Message:\n{message}"
        )
        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        return _coerce_intent(str(data["intent"]))


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
