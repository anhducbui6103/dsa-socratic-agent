from __future__ import annotations

import re


def analyze_code(code: str) -> str:
    normalized = code.lower()
    signals: list[str] = []

    loop_count = len(re.findall(r"\b(for|while)\b", normalized))
    if loop_count >= 2:
        signals.append("có nhiều vòng lặp, có thể cần kiểm tra xem chúng có lồng nhau và gây O(n^2) không")
    elif loop_count == 1:
        signals.append("có vẻ đang duyệt dữ liệu một lượt hoặc một vòng chính")

    if any(token in normalized for token in ("dict", "map", "unordered_map", "hashmap", "set(")):
        signals.append("có dùng cấu trúc tra cứu nhanh như map/set")

    if any(token in normalized for token in ("stack", "push", "pop")):
        signals.append("có dấu hiệu dùng stack để giữ trạng thái")

    if any(token in normalized for token in ("queue", "deque", "popleft", "bfs")):
        signals.append("có dấu hiệu duyệt theo hàng đợi/BFS")

    if any(token in normalized for token in ("dp", "memo", "cache")):
        signals.append("có dấu hiệu lưu trạng thái quy hoạch động")

    summary = "; ".join(signals) if signals else "chưa đủ dấu hiệu rõ ràng về chiến lược thuật toán"

    return (
        f"Code của em có vẻ đang thể hiện hướng: {summary}.\n\n"
        "Trước khi sửa chi tiết, em thử kiểm tra 2 điểm:\n"
        "1. Mỗi phần tử hoặc trạng thái đang được xử lý bao nhiêu lần trong trường hợp xấu nhất?\n"
        "2. Nếu input rỗng, chỉ có 1 phần tử, hoặc có nhiều giá trị trùng nhau thì biến kết quả của em thay đổi ra sao?\n\n"
        "Gợi ý nhỏ: hãy chọn một test rất nhỏ và ghi lại giá trị của các biến chính sau từng bước. "
        "Nếu em gửi lại trace đó, mình sẽ giúp em soi tiếp logic."
    )
