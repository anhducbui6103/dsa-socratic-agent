from __future__ import annotations

from ..llm_client import LlmClient
from ..models import Classification
from .json_tools import loads_json_object


class ProblemClassifierAgent:
    """Classifies a DSA problem through the LLM, not taxonomy keyword rules."""

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def classify(self, problem: str) -> Classification:
        system_prompt = (
            "Bạn là DSA Problem Classifier Agent. Chỉ trả về JSON hợp lệ, không markdown. "
            "Hãy đọc đề bài theo ngữ cảnh và suy luận topic/pattern phù hợp. "
            "Topic hợp lệ: array_string, two_pointers, sliding_window, hash_map, stack, "
            "queue_bfs, tree_dfs, graph, greedy, dynamic_programming, sorting_searching."
        )
        user_prompt = (
            "Phân loại bài toán DSA sau. JSON schema bắt buộc:\n"
            '{"topic":"string","pattern":"string","confidence":0.0,'
            '"key_signals":["string"],"recommended_hint_path":["string"]}\n\n'
            f"Đề bài:\n{problem}"
        )
        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        return Classification(
            topic=str(data["topic"]),
            pattern=str(data.get("pattern", "general")),
            confidence=float(data.get("confidence", 0.7)),
            key_signals=[str(item) for item in data.get("key_signals", [])],
            recommended_hint_path=[str(item) for item in data.get("recommended_hint_path", [])],
        )
