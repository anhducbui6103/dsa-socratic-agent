from __future__ import annotations

import ast
from dataclasses import dataclass
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from ..models import FailedTest, GeneratedTestCase, TestPurpose, TestSuite, ValidationResult, ValidationStatus


BLOCKED_IMPORT_ROOTS = {
    "ctypes",
    "multiprocessing",
    "os",
    "pathlib",
    "shutil",
    "socket",
    "subprocess",
    "threading",
}
BLOCKED_CALLS = {"__import__", "compile", "eval", "exec", "open"}
BLOCKED_ATTRIBUTE_ROOTS = {"os", "pathlib", "shutil", "socket", "subprocess"}


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

        sandbox_error = _find_sandbox_policy_error(code)
        if sandbox_error:
            return ValidationResult(
                status=ValidationStatus.RUNTIME_ERROR,
                passed_count=0,
                runtime_errors=[sandbox_error],
                complexity_notes=[
                    "Sandbox rejected code before execution.",
                    "Python sandbox v1 only allows single-file, stdin/stdout style solutions.",
                ],
            )

        function_spec = _find_submitted_function(code)

        with tempfile.TemporaryDirectory() as tmp_dir:
            script_path = Path(tmp_dir) / "submission.py"
            script_path.write_text(code, encoding="utf-8")
            env = {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }

            for test in tests:
                if test.purpose != TestPurpose.VALIDATION or test.expected_output is None:
                    continue

                executed += 1
                run_path = script_path
                run_input = test.input
                function_runner = _build_function_runner(code, function_spec, test.input)
                if function_runner:
                    run_path = Path(tmp_dir) / f"runner_{executed}.py"
                    run_path.write_text(function_runner, encoding="utf-8")
                    run_input = ""

                try:
                    completed = subprocess.run(
                        [sys.executable, "-I", "-B", str(run_path)],
                        input=run_input,
                        text=True,
                        capture_output=True,
                        cwd=tmp_dir,
                        env=env,
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
                elif _outputs_equal(stdout, expected):
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
    enable_execution: bool = True,
) -> ValidationResult:
    return CodeExecutionValidatorAgent(enable_execution=enable_execution, timeout_ms=timeout_ms).validate(code, language, tests)


def _find_sandbox_policy_error(code: str) -> str | None:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in BLOCKED_IMPORT_ROOTS:
                    return f"Sandbox blocked import `{root}`."

        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in BLOCKED_IMPORT_ROOTS:
                return f"Sandbox blocked import `{root}`."

        if isinstance(node, ast.Call):
            function_name = _call_name(node.func)
            if function_name in BLOCKED_CALLS:
                return f"Sandbox blocked call `{function_name}`."
            root_name = function_name.split(".", 1)[0]
            if root_name in BLOCKED_ATTRIBUTE_ROOTS:
                return f"Sandbox blocked call `{function_name}`."

    return None


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _find_submitted_function(code: str) -> tuple[str, list[str]] | None:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name, [arg.arg for arg in node.args.args]
    return None


def _build_function_runner(code: str, function_spec: tuple[str, list[str]] | None, raw_input: str) -> str | None:
    if function_spec is None:
        return None

    function_name, param_names = function_spec
    arguments = _parse_function_arguments(raw_input)
    if not arguments or any(name not in arguments for name in param_names):
        return None

    selected_arguments = {name: arguments[name] for name in param_names}
    return (
        "namespace = {'__name__': 'submission'}\n"
        f"exec({code!r}, namespace)\n"
        f"result = namespace[{function_name!r}](**{selected_arguments!r})\n"
        "print(repr(result))\n"
    )


def _parse_function_arguments(raw_input: str) -> dict[str, object]:
    stripped = raw_input.strip()
    if not stripped:
        return {}

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        return parsed

    try:
        tree = ast.parse(stripped)
    except SyntaxError:
        return {}

    arguments: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                arguments[target.id] = value
    return arguments


def _outputs_equal(actual: str, expected: str) -> bool:
    if actual == expected:
        return True

    actual_value = _parse_output_value(actual)
    expected_value = _parse_output_value(expected)
    if actual_value is not None and expected_value is not None:
        return actual_value == expected_value

    return False


def _parse_output_value(output: str) -> object | None:
    try:
        return ast.literal_eval(output)
    except (ValueError, SyntaxError):
        pass

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None
