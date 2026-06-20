import unittest

from dsa_agent import DsaLearningAgent
from dsa_agent.classifier import classify_problem
from dsa_agent.models import Intent


class ClassifierTests(unittest.TestCase):
    def test_classifies_dynamic_programming_problem(self) -> None:
        result = classify_problem("Tìm số cách leo cầu thang bằng quy hoạch động")

        self.assertEqual(result.topic, "dynamic_programming")
        self.assertGreater(result.confidence, 0.5)

    def test_classifies_sliding_window_problem(self) -> None:
        result = classify_problem("Tìm độ dài đoạn con liên tiếp có tổng lớn nhất")

        self.assertEqual(result.topic, "sliding_window")


class AgentTests(unittest.TestCase):
    def test_problem_then_hint_updates_state(self) -> None:
        agent = DsaLearningAgent()

        first = agent.handle("Cho mảng, tìm đoạn con liên tiếp có tổng lớn nhất")
        second = agent.handle("Cho em gợi ý")

        self.assertEqual(first.intent, Intent.SUBMIT_PROBLEM)
        self.assertEqual(second.intent, Intent.REQUEST_HINT)
        self.assertEqual(second.state.hint_level, 1)
        self.assertIn("gợi ý", second.response.lower())

    def test_direct_solution_is_redirected(self) -> None:
        agent = DsaLearningAgent()

        turn = agent.handle("Cho em full code lời giải")

        self.assertEqual(turn.intent, Intent.ASK_DIRECT_SOLUTION)
        self.assertNotIn("```", turn.response)
        self.assertIn("chưa đưa lời giải hoàn chỉnh", turn.response)

    def test_code_analysis_asks_for_reasoning(self) -> None:
        agent = DsaLearningAgent()

        turn = agent.handle("def solve(a):\n    for x in a:\n        print(x)")

        self.assertEqual(turn.intent, Intent.SUBMIT_CODE)
        self.assertIn("Mỗi phần tử", turn.response)


if __name__ == "__main__":
    unittest.main()
