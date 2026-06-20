from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "report-assets"


def font(size: int = 24, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/courbd.ttf" if bold else "C:/Windows/Fonts/cour.ttf",
    ]
    for item in candidates:
        if Path(item).exists():
            return ImageFont.truetype(item, size)
    return ImageFont.load_default()


def render_code(path: Path, title: str, code: str) -> None:
    lines = code.strip("\n").splitlines()
    line_h = 31
    width = 1800
    height = 125 + line_h * len(lines) + 55
    img = Image.new("RGB", (width, height), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    title_font = font(30, True)
    mono = font(22)
    small = font(18)

    draw.rounded_rectangle((40, 35, width - 40, height - 35), radius=24, fill="#0F172A", outline="#CBD5E1", width=2)
    draw.ellipse((75, 70, 95, 90), fill="#EF4444")
    draw.ellipse((105, 70, 125, 90), fill="#F59E0B")
    draw.ellipse((135, 70, 155, 90), fill="#22C55E")
    draw.text((185, 62), title, font=title_font, fill="#E2E8F0")

    y = 125
    for index, line in enumerate(lines, start=1):
        draw.text((70, y), f"{index:02d}", font=small, fill="#64748B")
        color = "#E2E8F0"
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("class "):
            color = "#93C5FD"
        elif stripped.startswith("graph.") or stripped.startswith("return"):
            color = "#A7F3D0"
        elif stripped.startswith("@dataclass") or stripped.startswith("if "):
            color = "#FDE68A"
        draw.text((130, y), line, font=mono, fill=color)
        y += line_h

    draw.text((70, height - 70), "Trích đoạn code minh họa từ project", font=small, fill="#94A3B8")
    img.save(path)


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    render_code(
        ASSET_DIR / "code-langgraph-nodes.png",
        "src/dsa_agent/graph_workflow.py",
        """
graph = StateGraph(TutorGraphState)
graph.add_node("detect_intent", self._detect_intent_node)
graph.add_node("submit_problem", self._submit_problem_node)
graph.add_node("request_hint", self._request_hint_node)
graph.add_node("submit_code", self._submit_code_node)
graph.add_node("direct_solution_guard", self._direct_solution_guard_node)
graph.add_node("submit_approach", self._submit_approach_node)
graph.add_node("ask_theory", self._ask_theory_node)
graph.add_node("finalize", self._finalize_node)

graph.add_edge(START, "detect_intent")
graph.add_conditional_edges("detect_intent", self._route_intent, {...})
graph.add_edge("finalize", END)
        """,
    )

    render_code(
        ASSET_DIR / "code-state-schema.png",
        "src/dsa_agent/models.py",
        """
@dataclass
class LearningState:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    current_problem: str | None = None
    problem_type: str | None = None
    concepts: list[str] = field(default_factory=list)
    hint_level: int = 0
    student_attempts: list[str] = field(default_factory=list)
    misconceptions: list[str] = field(default_factory=list)
    generated_tests: list[TestSuite] = field(default_factory=list)
    latest_validation: ValidationResult | None = None
    pedagogy_flags: list[PedagogyReview] = field(default_factory=list)
    next_action: str = "classify_or_ask"
        """,
    )

    render_code(
        ASSET_DIR / "code-quality-review.png",
        "src/dsa_agent/orchestrator.py",
        """
def _review_response(self, response: str) -> tuple[str, PedagogyReview]:
    review = self._review_pedagogy_with_llm(response)
    self.state.pedagogy_flags.append(review)

    if not review.safe_to_send and review.revision_instruction:
        response = self._revise_with_llm(response, review.revision_instruction)
        review = self._review_pedagogy_with_llm(response)
        self.state.pedagogy_flags.append(review)

    return response, review
        """,
    )


if __name__ == "__main__":
    main()
