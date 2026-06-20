from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "report-assets"


def font(size: int = 24, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for item in candidates:
        if Path(item).exists():
            return ImageFont.truetype(item, size)
    return ImageFont.load_default()


def box(draw, xy, text, fill="#FFFFFF", outline="#2E74B5", text_fill=(20, 20, 20), radius=18):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=2)
    f = font(19, True if "\n" not in text else False)
    lines = text.split("\n")
    metrics = [draw.textbbox((0, 0), line, font=f) for line in lines]
    widths = [m[2] - m[0] for m in metrics]
    heights = [m[3] - m[1] for m in metrics]
    total_h = sum(heights) + 5 * (len(lines) - 1)
    x1, y1, x2, y2 = xy
    y = y1 + ((y2 - y1) - total_h) / 2
    for line, w, h in zip(lines, widths, heights):
        draw.text((x1 + ((x2 - x1) - w) / 2, y), line, font=f, fill=text_fill)
        y += h + 5


def arrow(draw, start, end, color=(46, 116, 181), width=4):
    draw.line([start, end], fill=color, width=width)
    ex, ey = end
    sx, sy = start
    if abs(ex - sx) >= abs(ey - sy):
        direction = 1 if ex > sx else -1
        points = [(ex, ey), (ex - 13 * direction, ey - 8), (ex - 13 * direction, ey + 8)]
    else:
        direction = 1 if ey > sy else -1
        points = [(ex, ey), (ex - 8, ey - 13 * direction), (ex + 8, ey - 13 * direction)]
    draw.polygon(points, fill=color)


def create_langgraph_image(path: Path) -> None:
    img = Image.new("RGB", (1800, 980), "white")
    draw = ImageDraw.Draw(img)
    title = font(36, True)
    body = font(20)
    draw.text((55, 35), "LangGraph workflow sau khi tách node", font=title, fill=(20, 50, 90))

    box(draw, (80, 175, 235, 260), "START", "#EAF2FF")
    box(draw, (330, 145, 590, 290), "detect_intent\nLLM Intent Detector\nrecord_attempt", "#F2EAFE")

    route_x = 735
    route_y = 215
    draw.polygon(
        [(route_x, route_y - 80), (route_x + 115, route_y), (route_x, route_y + 80), (route_x - 115, route_y)],
        fill="#FFF7E6",
        outline="#E59F23",
    )
    draw.text((route_x - 47, route_y - 12), "route", font=font(20, True), fill=(20, 20, 20))

    nodes = [
        ((1020, 70, 1300, 145), "submit_problem"),
        ((1020, 180, 1300, 255), "request_hint"),
        ((1020, 290, 1300, 365), "submit_code"),
        ((1020, 400, 1300, 475), "direct_solution_guard"),
        ((1020, 510, 1300, 585), "submit_approach"),
        ((1020, 620, 1300, 695), "ask_theory"),
    ]
    for xy, label in nodes:
        box(draw, xy, label, "#F0F7FF")

    box(draw, (1480, 325, 1700, 430), "finalize\nfinal_response", "#EAF7EE")
    box(draw, (1480, 540, 1640, 625), "END", "#EAF2FF")

    arrow(draw, (235, 218), (330, 218))
    arrow(draw, (590, 218), (620, 218))
    draw.line([(620, 218), (620, route_y), (620, route_y), (route_x - 115, route_y)], fill=(46, 116, 181), width=4)
    arrow(draw, (850, route_y), (1020, 108))
    arrow(draw, (850, route_y), (1020, 218))
    arrow(draw, (850, route_y), (1020, 328))
    arrow(draw, (850, route_y), (1020, 438))
    arrow(draw, (850, route_y), (1020, 548))
    arrow(draw, (850, route_y), (1020, 658))

    for xy, _ in nodes:
        arrow(draw, (xy[2], (xy[1] + xy[3]) // 2), (1480, 378))
    arrow(draw, (1590, 430), (1590, 540))

    draw.text(
        (85, 835),
        "Mỗi intent đi qua một node riêng nên có thể mở rộng, debug và trình bày rõ hơn trong báo cáo đồ án.",
        font=body,
        fill=(80, 80, 80),
    )
    img.save(path)


def create_agent_trace_image(path: Path) -> None:
    img = Image.new("RGB", (1800, 980), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    title = font(36, True)
    body = font(20)
    small = font(18)

    draw.text((55, 35), "Agent Trace cho một lượt hội thoại", font=title, fill=(20, 50, 90))
    draw.text(
        (58, 92),
        "Trace ghi lại các bước workflow đã chạy, không hiển thị chain-of-thought nội bộ của LLM.",
        font=body,
        fill=(85, 85, 85),
    )

    panel = (70, 160, 1730, 875)
    draw.rounded_rectangle(panel, radius=28, fill="#F7F8FA", outline="#D6DAE2", width=2)

    steps = [
        ("1", "Intent Detector", "REQUEST_HINT", "#EAF2FF"),
        ("2", "State Update", "hint_level: 1 -> 2", "#EEF7EF"),
        ("3", "Hint Generator", "LLM sinh gợi ý Socratic", "#FFF7E6"),
        ("4", "Pedagogy Critic", "safe_to_send = true", "#F1EAFE"),
        ("5", "Finalize", "Trả 1-2 gợi ý chính", "#EAF7F8"),
    ]

    x = 125
    y = 235
    card_w = 285
    card_h = 180
    gap = 35
    for index, name, result, fill in steps:
        xy = (x, y, x + card_w, y + card_h)
        draw.rounded_rectangle(xy, radius=20, fill=fill, outline="#CBD5E1", width=2)
        draw.ellipse((x + 22, y + 22, x + 62, y + 62), fill="#1F4E79")
        draw.text((x + 36, y + 30), index, font=font(20, True), fill="white")
        draw.text((x + 80, y + 28), name, font=font(22, True), fill=(25, 34, 49))
        draw.line((x + 24, y + 82, x + card_w - 24, y + 82), fill="#CBD5E1", width=1)
        draw.text((x + 28, y + 105), result, font=small, fill=(55, 65, 81))
        if index != "5":
            arrow(draw, (x + card_w + 3, y + card_h // 2), (x + card_w + gap - 8, y + card_h // 2))
        x += card_w + gap

    box(draw, (170, 545, 795, 735), "Student message\n\"Em xin thêm gợi ý bài này\"", "#FFFFFF", "#CBD5E1")
    box(draw, (1005, 545, 1630, 735), "Tutor response\n\"Thử nhìn vào trạng thái cần lưu sau mỗi bước...\"", "#FFFFFF", "#CBD5E1")
    arrow(draw, (795, 640), (1005, 640), color=(80, 92, 110), width=3)

    draw.text(
        (170, 795),
        "Agent Trace được dùng cho debug, demo và đánh giá chất lượng; người học chỉ thấy phản hồi cuối và các testcase/gợi ý cần thiết.",
        font=body,
        fill=(80, 80, 80),
    )
    img.save(path)


if __name__ == "__main__":
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    create_langgraph_image(ASSET_DIR / "langgraph.png")
    create_agent_trace_image(ASSET_DIR / "agent-trace.png")
