from __future__ import annotations

from dataclasses import dataclass
import subprocess
import sys
import tempfile
from pathlib import Path

from ..models import FailedTest, GeneratedTestCase, TestPurpose, TestSuite, ValidationResult, ValidationStatus


@dataclass
class CodeExecutionValidatorAgent:
    enable_execution: bool = False
    timeout_ms: int = 2000
    max_output_chars: int = 4000

    def validate(self, code: str, language: str, tests: TestSuite | list[GeneratedTestCase]) -> ValidationResult:
        if not self.enable_execution:
            return ValidationResult(
                status=ValidationStatus.SKIPPED,
                passed_count=0,
                complexity_notes=["Sandbox execution chưa được bật; bỏ qua bước chạy code."],
            )

        normalized_language = language.lower()
        if normalized_language != "python":
            return ValidationResult(
                status=ValidationStatus.SKIPPED,
                passed_count=0,
                complexity_notes=["Sandbox v1 chỉ hỗ trợ Python."],
            )

        test_items = tests.tests if isinstance(tests, TestSuite) else tests
        return self._validate_python(code, test_items)

    def _validate_python(self, code: str, tests: list[GeneratedTestCase]) -> ValidationResult:
        passed = 0
        executed = 0
        failed_tests: list[FailedTest] = []
        runtime_errors: list[str] = []
        timeout = False

        with tempfile.TemporaryDirectory() as tmp_dir:
            script_path = Path(tmp_dir) / "submission.py"
            script_path.write_text(code, encoding="utf-8")

            for test in tests:
                if test.purpose != TestPurpose.VALIDATION or test.expected_output is None:
                    continue

                executed += 1
                try:
                    completed = subprocess.run(
                        [sys.executable, "-I", str(script_path)],
                        input=test.input,
                        text=True,
                        capture_output=True,
                        cwd=tmp_dir,
                        timeout=self.timeout_ms / 1000,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    timeout = True
                    failed_tests.append(
                        FailedTest(
                            name=test.name,
                            expected_output=test.expected_output,
                            actual_output="",
                            error="Timeout",
                        )
                    )
                    continue

                stdout = completed.stdout[: self.max_output_chars].strip()
                stderr = completed.stderr[: self.max_output_chars].strip()
                expected = test.expected_output.strip()

                if completed.returncode != 0:
                    runtime_errors.append(stderr or f"Process exited with code {completed.returncode}")
                    failed_tests.append(
                        FailedTest(
                            name=test.name,
                            expected_output=test.expected_output,
                            actual_output=stdout,
                            error=stderr,
                        )
                    )
                elif stdout == expected:
                    passed += 1
                else:
                    failed_tests.append(
                        FailedTest(
                            name=test.name,
                            expected_output=test.expected_output,
                            actual_output=stdout,
                        )
                    )

        if executed == 0:
            status = ValidationStatus.SKIPPED
        elif timeout:
            status = ValidationStatus.TIMEOUT
        elif runtime_errors:
            status = ValidationStatus.RUNTIME_ERROR
        elif failed_tests:
            status = ValidationStatus.FAILED
        else:
            status = ValidationStatus.PASSED

        return ValidationResult(
            status=status,
            passed_count=passed,
            failed_tests=failed_tests,
            runtime_errors=runtime_errors,
            timeout=timeout,
            complexity_notes=[
                "Python sandbox v1 dùng timeout theo từng test.",
                "Trace-only testcase không được chạy tự động.",
            ],
        )


def validate_code(
    code: str,
    language: str,
    tests: TestSuite | list[GeneratedTestCase],
    timeout_ms: int = 2000,
) -> ValidationResult:
    return CodeExecutionValidatorAgent(enable_execution=False, timeout_ms=timeout_ms).validate(code, language, tests)
