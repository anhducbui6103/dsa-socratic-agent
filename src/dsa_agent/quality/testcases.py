from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1

from ..models import Classification, GeneratedTestCase, TestCategory, TestSuite


@dataclass
class TestcaseGeneratorAgent:
    language: str = "python"

    def generate(
        self,
        problem: str,
        classification: Classification | None = None,
        constraints: list[str] | None = None,
    ) -> TestSuite:
        topic = classification.topic if classification else "array_string"
        problem_id = sha1(problem.encode("utf-8")).hexdigest()[:12]
        tests = _topic_tests(topic)
        coverage_notes = [
            "Bao phủ case nhỏ để sinh viên trace tay.",
            "Bao phủ ít nhất một edge case dễ làm lộ giả định sai.",
        ]
        if constraints:
            coverage_notes.append("Ràng buộc đã ghi nhận: " + "; ".join(constraints))

        return TestSuite(problem_id=problem_id, language=self.language, tests=tests, coverage_notes=coverage_notes)


def generate_testcases(
    problem: str,
    classification: Classification | None = None,
    constraints: list[str] | None = None,
) -> TestSuite:
    return TestcaseGeneratorAgent().generate(problem, classification, constraints)


def _topic_tests(topic: str) -> list[GeneratedTestCase]:
    if topic == "dynamic_programming":
        return [
            GeneratedTestCase(
                name="dp_small_trace",
                input="n = 4",
                expected_output=None,
                category=TestCategory.BASIC,
                rationale="Case nhỏ để nhìn bài toán con và base case.",
            ),
            GeneratedTestCase(
                name="dp_base_case",
                input="n = 0 hoặc n = 1",
                expected_output=None,
                category=TestCategory.EDGE,
                rationale="Kiểm tra trạng thái khởi tạo có đủ không.",
            ),
        ]

    if topic == "sliding_window":
        return [
            GeneratedTestCase(
                name="window_basic",
                input="a = [1, 2, 1, 3], target/constraint nhỏ",
                expected_output=None,
                category=TestCategory.BASIC,
                rationale="Case ngắn để quan sát khi nào mở rộng và thu hẹp cửa sổ.",
            ),
            GeneratedTestCase(
                name="window_empty_or_single",
                input="a = [] hoặc a = [5]",
                expected_output=None,
                category=TestCategory.EDGE,
                rationale="Kiểm tra điều kiện dừng và kết quả khởi tạo.",
            ),
        ]

    if topic == "hash_map":
        return [
            GeneratedTestCase(
                name="duplicate_values",
                input="a = [2, 2, 3, 3]",
                expected_output=None,
                category=TestCategory.EDGE,
                rationale="Làm rõ cách cập nhật tần suất hoặc kiểm tra tồn tại.",
            ),
            GeneratedTestCase(
                name="missing_key",
                input="a = [1, 4, 9]",
                expected_output=None,
                category=TestCategory.BASIC,
                rationale="Kiểm tra nhánh không tìm thấy trong bảng băm.",
            ),
        ]

    if topic in {"queue_bfs", "graph"}:
        return [
            GeneratedTestCase(
                name="connected_small_graph",
                input="3 đỉnh, cạnh: 1-2, 2-3",
                expected_output=None,
                category=TestCategory.BASIC,
                rationale="Case nhỏ để kiểm tra thứ tự duyệt và visited.",
            ),
            GeneratedTestCase(
                name="disconnected_graph",
                input="4 đỉnh, cạnh: 1-2, 3-4",
                expected_output=None,
                category=TestCategory.EDGE,
                rationale="Kiểm tra thuật toán có bỏ sót thành phần liên thông không.",
            ),
        ]

    return [
        GeneratedTestCase(
            name="small_trace",
            input="input nhỏ 3-5 phần tử",
            expected_output=None,
            category=TestCategory.BASIC,
            rationale="Dùng để ghi lại trạng thái sau từng bước.",
        ),
        GeneratedTestCase(
            name="boundary_case",
            input="input rỗng, một phần tử, hoặc toàn giá trị giống nhau",
            expected_output=None,
            category=TestCategory.EDGE,
            rationale="Kiểm tra điều kiện biên và biến khởi tạo.",
        ),
    ]
