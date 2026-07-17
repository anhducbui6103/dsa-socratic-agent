from __future__ import annotations

from ..llm_client import LlmClient
from ..models import Classification
from .json_tools import loads_json_object


class ProblemClassifierAgent:
    """Analyzes a DSA problem and extracts pedagogically useful metadata."""

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def classify(self, problem: str) -> Classification:
        system_prompt = (
            "Bạn là DSA Problem Classifier Agent. "
            "Chỉ trả về JSON hợp lệ, không markdown. "
            "Nhiệm vụ là phân tích bài toán để hỗ trợ các agent dạy học phía sau, "
            "không giải bài và không dựa vào keyword đơn giản.\n\n"
            "Quy tắc phân loại:\n"
            "- Chọn đúng 1 `topic` chính đại diện cho kỹ thuật quan trọng nhất để giải bài.\n"
            "- `pattern` phải cụ thể hơn `topic`.\n"
            "- `difficulty` chỉ được là `easy`, `medium`, hoặc `hard`, theo góc nhìn người học DSA.\n"
            "- `confidence` là độ chắc chắn của phân loại trong khoảng [0,1].\n"
            "- `key_signals` là các tín hiệu ngữ nghĩa khiến bạn đi tới kết luận; không chép nguyên văn đề bài.\n"
            "- `recommended_hint_path` là roadmap sư phạm ngắn, không phải lời giải.\n"
            "- Hãy suy luận trên toàn bộ ngữ cảnh bài toán, không dùng matching từ khóa hời hợt.\n\n"
            "Topic hợp lệ:\n"
            "- array_string\n"
            "- two_pointers\n"
            "- sliding_window\n"
            "- hash_map\n"
            "- stack\n"
            "- queue_bfs\n"
            "- tree_dfs\n"
            "- graph\n"
            "- greedy\n"
            "- dynamic_programming\n"
            "- sorting_searching\n\n"
            "Gợi ý cho `difficulty`:\n"
            "- easy: pattern quen thuộc, triển khai ngắn, ít edge case, ít tầng suy luận.\n"
            "- medium: cần nhận ra pattern hoặc cần 1-2 ý tối ưu, state, hay cấu trúc dữ liệu quan trọng.\n"
            "- hard: cần kỹ thuật nâng cao, nhiều lớp suy luận, hoặc pattern khó nhận ra và dễ cài đặt sai.\n"
            "- Không dùng `difficulty` như proxy cho `confidence`.\n\n"
            "Ví dụ `pattern`:\n"
            "- two_pointers: opposite pointers, fast slow pointers, merge, partition\n"
            "- dynamic_programming: knapsack, LIS, interval DP, digit DP, tree DP\n"
            "- graph: shortest path, topological sort, union find, mst, connected components"
        )

        user_prompt = (
            "Hãy phân tích bài toán DSA sau. JSON schema bắt buộc:\n"
            '{"topic":"string","pattern":"string","difficulty":"easy|medium|hard","confidence":0.0,"key_signals":["string"],"recommended_hint_path":["string"]}\n\n'
            "Ví dụ `recommended_hint_path`:\n"
            '- ["understand constraints", "identify brute force", "optimize observations", "choose data structure", "derive algorithm", "implement"]\n'
            '- ["identify state", "define transition", "optimize memory"]\n\n'
            f"Problem:\n{problem}"
        )

        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))

        return Classification(
            topic=str(data["topic"]),
            pattern=str(data.get("pattern", "general")),
            difficulty=_coerce_difficulty(data.get("difficulty")),
            confidence=float(data.get("confidence", 0.7)),
            key_signals=[str(item) for item in data.get("key_signals", [])],
            recommended_hint_path=[str(item) for item in data.get("recommended_hint_path", [])],
        )


def _coerce_difficulty(raw_difficulty: object) -> str:
    normalized = str(raw_difficulty or "medium").strip().lower()
    if normalized in {"easy", "medium", "hard"}:
        return normalized
    return "medium"
