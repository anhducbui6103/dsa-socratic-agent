from __future__ import annotations

from ..llm_client import LlmClient
from ..models import Classification, GeneratedTestCase, TestCategory, TestPurpose, TestSuite
from .json_tools import loads_json_object


class TestcaseGeneratorAgent:
    """Generates learning-oriented test cases with the LLM."""

    def __init__(self, llm_client: LlmClient, language: str = "python") -> None:
        self.llm_client = llm_client
        self.language = language

    def generate(self, problem: str, classification: Classification | None = None) -> TestSuite:
        topic = classification.topic if classification else "unknown"
        system_prompt = (
            "Bạn là Testcase Generator Agent cho bài DSA. "
            "Chỉ trả về JSON hợp lệ, không markdown. "
            "Nhiệm vụ là sinh testcase phục vụ học tập, trace tay và kiểm edge case, "
            "không giải thích dài dòng. "
            "Ưu tiên testcase nhỏ nhưng giàu tín hiệu. "
            "Nếu chưa chắc expected output thì đặt null."
        )
        user_prompt = (
            "Sinh testcase cho bài dưới đây. JSON schema bắt buộc:\n"
            '{"problem_id":"string","language":"python","coverage_notes":["string"],'
            '"tests":[{"name":"string","input":"string","expected_output":"string|null",'
            '"purpose":"validation|trace_only","category":"basic|edge|adversarial|stress",'
            '"rationale":"string"}]}\n\n'
            "Yêu cầu:\n"
            "- Với lời giải dạng hàm, đặt input là Python assignments khớp tên tham số.\n"
            "- Chỉ đặt expected_output khi kết quả chắc chắn rõ.\n"
            "- Bao phủ ít nhất case cơ bản và edge case nếu có thể.\n"
            "- `recommended_hint_path` hoặc hướng học không cần lặp lại ở đây; chỉ tập trung vào testcase.\n\n"
            "Ví dụ input cho function-style:\n"
            "nums = [2, 7, 11, 15]\ntarget = 9\n"
            f"Topic: {topic}\n"
            f"Đề bài:\n{problem}"
        )
        data = loads_json_object(self.llm_client.generate(system_prompt, user_prompt))
        tests = [_coerce_test(item) for item in data.get("tests", [])]
        if not tests:
            raise ValueError("LLM testcase generator returned no tests.")

        return TestSuite(
            problem_id=str(data.get("problem_id", "llm-generated")),
            language=str(data.get("language", self.language)),
            tests=tests,
            coverage_notes=[str(item) for item in data.get("coverage_notes", [])],
        )


def _coerce_test(item: dict) -> GeneratedTestCase:
    try:
        category = TestCategory(str(item.get("category", "basic")))
    except ValueError:
        category = TestCategory.BASIC

    expected_output = item.get("expected_output")
    purpose_value = str(item.get("purpose") or ("validation" if expected_output is not None else "trace_only"))
    try:
        purpose = TestPurpose(purpose_value)
    except ValueError:
        purpose = TestPurpose.TRACE_ONLY

    return GeneratedTestCase(
        name=str(item.get("name", "llm_case")),
        input=str(item.get("input", "")),
        expected_output=expected_output,
        category=category,
        rationale=str(item.get("rationale", "")),
        purpose=purpose,
    )
