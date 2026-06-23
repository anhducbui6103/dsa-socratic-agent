from __future__ import annotations

from dataclasses import dataclass
import re

from ..models import LearningState, PedagogyReview


@dataclass
class PedagogyCriticAgent:
    allow_direct_solution: bool = False

    def review(self, draft_response: str, state: LearningState, policy: str = "socratic") -> PedagogyReview:
        issues: list[str] = []
        normalized = draft_response.lower()

        if not self.allow_direct_solution and _looks_like_full_code(draft_response):
            issues.append("Phản hồi có dấu hiệu chứa full code hoặc code block.")

        if not self.allow_direct_solution and re.search(r"\b(lời giải là|đáp án là|công thức là)\b", normalized):
            issues.append("Phản hồi có thể tiết lộ lời giải quá trực tiếp.")

        question_count = draft_response.count("?")
        if question_count == 0 and policy == "socratic":
            issues.append("Phản hồi chưa có câu hỏi gợi mở.")
        elif question_count > 3:
            issues.append("Phản hồi hỏi quá nhiều câu trong một lượt.")

        risk_level = "low"
        if issues:
            risk_level = "medium"
        if any("full code" in issue or "trực tiếp" in issue for issue in issues):
            risk_level = "high"

        return PedagogyReview(
            safe_to_send=not issues or risk_level == "low",
            risk_level=risk_level,
            issues=issues,
            revision_instruction=_revision_instruction(issues),
        )


def review_pedagogy(draft_response: str, state: LearningState, policy: str = "socratic") -> PedagogyReview:
    return PedagogyCriticAgent().review(draft_response, state, policy)


def _looks_like_full_code(text: str) -> bool:
    code_markers = ("```", "def ", "class ", "#include", "public static", "function ")
    return any(marker in text for marker in code_markers)


def _revision_instruction(issues: list[str]) -> str | None:
    if not issues:
        return None
    return (
        "Viết lại phản hồi theo kiểu Socratic: bỏ code/lời giải trực tiếp, giữ 1-2 câu hỏi chính, "
        "và gợi ý đúng mức hiện tại của sinh viên."
    )
