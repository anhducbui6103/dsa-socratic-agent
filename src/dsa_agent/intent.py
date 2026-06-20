from __future__ import annotations

import re

from .models import Intent


CODE_MARKERS = ("```", "#include", "def ", "class ", "public static", "function ", "for ", "while ")


def detect_intent(message: str) -> Intent:
    normalized = message.lower().strip()

    if any(marker in message for marker in CODE_MARKERS):
        return Intent.SUBMIT_CODE

    if re.search(r"\b(code mẫu|lời giải|đáp án|giải giúp|full code)\b", normalized):
        return Intent.ASK_DIRECT_SOLUTION

    if re.search(r"\b(gợi ý|hint|bị tắc|không biết làm|tiếp theo)\b", normalized):
        return Intent.REQUEST_HINT

    if re.search(r"\b(ý tưởng|em nghĩ|cách làm|thuật toán của em)\b", normalized):
        return Intent.SUBMIT_APPROACH

    if re.search(r"\b(là gì|khái niệm|độ phức tạp|big o|vì sao)\b", normalized):
        return Intent.ASK_THEORY

    return Intent.SUBMIT_PROBLEM
