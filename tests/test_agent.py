import unittest

from dsa_agent import DsaLearningAgent
from dsa_agent.agents import PedagogyCriticAgent, TestcaseGeneratorAgent
from dsa_agent.graph_workflow import DsaTutorGraph
from dsa_agent.llm_client import GeminiLlmClient, MissingApiKeyError
from dsa_agent.models import Classification, GeneratedTestCase, Intent, TestCategory, ValidationStatus
from dsa_agent.quality import CodeExecutionValidatorAgent, validate_code


class FakeLlmClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if "Intent Detector" in system_prompt:
            text = user_prompt.split("Message:\n", 1)[-1].lower()
            if "full code" in text or "lời giải" in text:
                return '{"intent":"ASK_DIRECT_SOLUTION"}'
            if "def solve" in text or "```" in text:
                return '{"intent":"SUBMIT_CODE"}'
            if "gợi ý" in text or "hint" in text:
                return '{"intent":"REQUEST_HINT"}'
            if "ý tưởng" in text:
                return '{"intent":"SUBMIT_APPROACH"}'
            if "cho mảng" in text or "tìm" in text:
                return '{"intent":"SUBMIT_PROBLEM"}'
            return '{"intent":"ASK_THEORY"}'
        if "DSA Problem Classifier" in system_prompt:
            return (
                '{"topic":"sliding_window","pattern":"window_trace","confidence":0.82,'
                '"key_signals":["đoạn con liên tiếp","mảng"],'
                '"recommended_hint_path":["input_output","valid_window"]}'
            )
        if "Testcase Generator Agent" in system_prompt:
            return (
                '{"problem_id":"fake-problem","language":"python",'
                '"coverage_notes":["case nhỏ để trace","edge case để kiểm biến khởi tạo"],'
                '"tests":['
                '{"name":"small_trace","input":"a = [1, 2, 1]","expected_output":null,'
                '"category":"basic","rationale":"Trace trạng thái qua từng phần tử."},'
                '{"name":"empty_case","input":"a = []","expected_output":null,'
                '"category":"edge","rationale":"Kiểm tra điều kiện biên."}'
                ']}'
            )
        if "Pedagogy Critic Agent" in system_prompt:
            return '{"safe_to_send":true,"risk_level":"low","issues":[],"revision_instruction":null}'
        if "Session Title Agent" in system_prompt:
            return '{"title":"Maximum Subarray"}'
        if "sửa phản hồi" in system_prompt or "Instruction từ Pedagogy Critic" in user_prompt:
            return "Em thử tự kiểm lại bằng một ví dụ nhỏ trước nhé?"
        if "review_trace_or_edge_case" in user_prompt:
            return "Mỗi phần tử đang được xử lý thế nào? Em thử trace một testcase nhỏ trước nhé?"
        if "redirect_to_socratic_hint" in user_prompt:
            return "Mình chưa đưa lời giải hoàn chỉnh. Em thử mô tả input/output và ràng buộc trước nhé?"
        if "wait_for_student_attempt" in user_prompt:
            return "Đây là gợi ý theo mức hiện tại: em thử xét một ví dụ nhỏ và nêu trạng thái cần lưu?"
        return "Em thử mô tả input/output và ràng buộc chính của bài trước nhé?"


class TypoIntentLlmClient(FakeLlmClient):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if "Intent Detector" in system_prompt:
            return '{"intent":"SUBMITS_PROBLEM"}'
        return super().generate(system_prompt, user_prompt)


class UnsafePedagogyLlmClient(FakeLlmClient):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if "Pedagogy Critic Agent" in system_prompt:
            return (
                '{"safe_to_send":false,"risk_level":"high",'
                '"issues":["Phản hồi có dấu hiệu chứa full code."],'
                '"revision_instruction":"Bỏ code và hỏi theo kiểu Socratic."}'
            )
        return super().generate(system_prompt, user_prompt)


class AgentTests(unittest.TestCase):
    def test_problem_then_hint_updates_state(self) -> None:
        agent = DsaLearningAgent(llm_client=FakeLlmClient())

        first = agent.handle("Cho mảng, tìm đoạn con liên tiếp có tổng lớn nhất")
        second = agent.handle("Cho em gợi ý")

        self.assertEqual(first.intent, Intent.SUBMIT_PROBLEM)
        self.assertEqual(second.intent, Intent.REQUEST_HINT)
        self.assertEqual(second.state.hint_level, 1)
        self.assertIn("gợi ý", second.response.lower())
        self.assertTrue(first.state.generated_tests)
        self.assertIsNotNone(second.pedagogy_review)
        self.assertTrue(second.state.agent_trace)

    def test_problem_classification_uses_llm_agent_output(self) -> None:
        agent = DsaLearningAgent(llm_client=FakeLlmClient())

        turn = agent.handle("Cho mảng, tìm đoạn con liên tiếp có tổng lớn nhất")

        self.assertEqual(turn.classification.topic, "sliding_window")
        self.assertEqual(turn.classification.pattern, "window_trace")
        self.assertTrue(any(item.node_name == "Problem Classifier" for item in turn.state.agent_trace))

    def test_direct_solution_is_redirected(self) -> None:
        agent = DsaLearningAgent(llm_client=FakeLlmClient())

        turn = agent.handle("Cho em full code lời giải")

        self.assertEqual(turn.intent, Intent.ASK_DIRECT_SOLUTION)
        self.assertNotIn("```", turn.response)
        self.assertIn("chưa đưa lời giải hoàn chỉnh", turn.response)

    def test_code_analysis_asks_for_reasoning(self) -> None:
        agent = DsaLearningAgent(llm_client=FakeLlmClient())

        turn = agent.handle("def solve(a):\n    for x in a:\n        print(x)")

        self.assertEqual(turn.intent, Intent.SUBMIT_CODE)
        self.assertIn("Mỗi phần tử", turn.response)
        self.assertIsNotNone(turn.validation)
        self.assertEqual(turn.validation.status, ValidationStatus.SKIPPED)

    def test_graph_runs_agent_workflow(self) -> None:
        graph = DsaTutorGraph(DsaLearningAgent(llm_client=FakeLlmClient()))

        turn = graph.run("Cho mảng, tìm đoạn con liên tiếp có tổng lớn nhất")

        self.assertEqual(turn.intent, Intent.SUBMIT_PROBLEM)
        self.assertTrue(turn.state.generated_tests)
        self.assertTrue(any(item.node_name == "LangGraph Router" for item in turn.state.agent_trace))

    def test_session_title_agent_updates_state(self) -> None:
        agent = DsaLearningAgent(llm_client=FakeLlmClient())

        title = agent.generate_session_title(["Maximum subarray problem"])

        self.assertEqual(title, "Maximum Subarray")
        self.assertEqual(agent.state.chat_title, "Maximum Subarray")
        self.assertTrue(any(item.node_name == "Session Title Agent" for item in agent.state.agent_trace))

    def test_normalizes_typo_intent_from_llm(self) -> None:
        agent = DsaLearningAgent(llm_client=TypoIntentLlmClient())

        turn = agent.handle("giúp t với bài toán two sum")

        self.assertEqual(turn.intent, Intent.SUBMIT_PROBLEM)

    def test_gemini_client_requires_api_key(self) -> None:
        import os

        old_key = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            with self.assertRaises(MissingApiKeyError):
                GeminiLlmClient.from_env()
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key


class QualityAgentTests(unittest.TestCase):
    def test_testcase_generator_creates_basic_and_edge_cases(self) -> None:
        classification = Classification(
            topic="dynamic_programming",
            pattern="state_transition",
            confidence=0.9,
            key_signals=["bài toán con", "base case"],
            recommended_hint_path=["state_definition", "transition_question"],
        )
        suite = TestcaseGeneratorAgent(FakeLlmClient()).generate("Tìm số cách leo cầu thang", classification)

        categories = {test.category for test in suite.tests}
        self.assertIn(TestCategory.BASIC, categories)
        self.assertIn(TestCategory.EDGE, categories)
        self.assertTrue(suite.coverage_notes)

    def test_pedagogy_critic_flags_full_code(self) -> None:
        agent = DsaLearningAgent(llm_client=FakeLlmClient())
        review = PedagogyCriticAgent(UnsafePedagogyLlmClient()).review("```python\ndef solve():\n    pass\n```", agent.state)

        self.assertFalse(review.safe_to_send)
        self.assertEqual(review.risk_level, "high")
        self.assertTrue(review.revision_instruction)

    def test_validator_skips_when_execution_is_disabled(self) -> None:
        test = GeneratedTestCase("echo", "hello", "hello", TestCategory.BASIC, "Echo test")

        result = CodeExecutionValidatorAgent(enable_execution=False).validate("print('hello')", "python", [test])

        self.assertEqual(result.status, ValidationStatus.SKIPPED)

    def test_validator_passes_python_code(self) -> None:
        test = GeneratedTestCase("echo", "hello", "hello", TestCategory.BASIC, "Echo test")
        code = "import sys\nprint(sys.stdin.read().strip())"

        result = CodeExecutionValidatorAgent(enable_execution=True).validate(code, "python", [test])

        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.passed_count, 1)

    def test_validate_code_helper_runs_python_by_default(self) -> None:
        test = GeneratedTestCase("echo", "hello", "hello", TestCategory.BASIC, "Echo test")

        result = validate_code("print(input())", "python", [test])

        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.passed_count, 1)

    def test_validator_calls_function_style_submission(self) -> None:
        test = GeneratedTestCase(
            "two_sum",
            "nums = [2, 7, 11, 15]\ntarget = 9",
            "[0, 1]",
            TestCategory.BASIC,
            "LeetCode-style function call.",
        )
        code = (
            "def twoSum(nums, target):\n"
            "    n = len(nums)\n"
            "    for i in range(n):\n"
            "        for j in range(i + 1, n):\n"
            "            if nums[i] + nums[j] == target:\n"
            "                return [i, j]\n"
        )

        result = CodeExecutionValidatorAgent(enable_execution=True).validate(code, "python", [test])

        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.passed_count, 1)

    def test_validator_calls_function_style_submission_with_json_input(self) -> None:
        test = GeneratedTestCase(
            "two_sum_json",
            '{"nums":[3,2,4],"target":6}',
            "[1, 2]",
            TestCategory.BASIC,
            "JSON arguments for function call.",
        )
        code = (
            "def twoSum(nums, target):\n"
            "    seen = {}\n"
            "    for i, value in enumerate(nums):\n"
            "        if target - value in seen:\n"
            "            return [seen[target - value], i]\n"
            "        seen[value] = i\n"
        )

        result = CodeExecutionValidatorAgent(enable_execution=True).validate(code, "python", [test])

        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.passed_count, 1)

    def test_validator_skips_trace_only_cases(self) -> None:
        from dsa_agent.models import TestPurpose

        test = GeneratedTestCase("trace", "hello", None, TestCategory.BASIC, "Trace only", TestPurpose.TRACE_ONLY)

        result = CodeExecutionValidatorAgent(enable_execution=True).validate("print('hello')", "python", [test])

        self.assertEqual(result.status, ValidationStatus.SKIPPED)

    def test_validator_fails_wrong_output(self) -> None:
        test = GeneratedTestCase("echo", "hello", "hello", TestCategory.BASIC, "Echo test")

        result = CodeExecutionValidatorAgent(enable_execution=True).validate("print('bye')", "python", [test])

        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.failed_tests[0].actual_output, "bye")

    def test_validator_reports_runtime_error(self) -> None:
        test = GeneratedTestCase("runtime", "", "ok", TestCategory.BASIC, "Runtime test")

        result = CodeExecutionValidatorAgent(enable_execution=True).validate("raise ValueError('boom')", "python", [test])

        self.assertEqual(result.status, ValidationStatus.RUNTIME_ERROR)
        self.assertTrue(result.runtime_errors)

    def test_validator_blocks_unsafe_imports_before_execution(self) -> None:
        test = GeneratedTestCase("unsafe", "", "ok", TestCategory.BASIC, "Unsafe import test")

        result = CodeExecutionValidatorAgent(enable_execution=True).validate(
            "import os\nprint(os.getcwd())",
            "python",
            [test],
        )

        self.assertEqual(result.status, ValidationStatus.RUNTIME_ERROR)
        self.assertIn("blocked import", result.runtime_errors[0])

    def test_validator_reports_timeout(self) -> None:
        test = GeneratedTestCase("timeout", "", "ok", TestCategory.BASIC, "Timeout test")

        result = CodeExecutionValidatorAgent(enable_execution=True, timeout_ms=100).validate(
            "while True:\n    pass",
            "python",
            [test],
        )

        self.assertEqual(result.status, ValidationStatus.TIMEOUT)
        self.assertTrue(result.timeout)


if __name__ == "__main__":
    unittest.main()
