from __future__ import annotations

from .models import Classification


TAXONOMY_RULES: list[tuple[str, list[str], list[str], list[str]]] = [
    (
        "dynamic_programming",
        ["quy hoạch động", "dp", "bài toán con", "tối ưu", "số cách", "dãy con"],
        ["state_definition", "transition_question", "base_case"],
        ["bài toán con lặp lại", "tối ưu hoặc đếm số cách"],
    ),
    (
        "graph",
        ["đồ thị", "đỉnh", "cạnh", "liên thông", "chu trình", "đường đi"],
        ["representation", "traversal_choice", "visited_state"],
        ["đỉnh/cạnh", "quan hệ giữa đối tượng"],
    ),
    (
        "queue_bfs",
        ["bfs", "hàng đợi", "shortest path", "ngắn nhất", "theo lớp"],
        ["state_queue", "neighbor_generation", "visited_state"],
        ["duyệt theo lớp", "đường đi ngắn nhất không trọng số"],
    ),
    (
        "stack",
        ["stack", "ngăn xếp", "ngoặc", "nearest greater", "nearest smaller", "đơn điệu"],
        ["kept_candidates", "pop_condition", "edge_case"],
        ["giữ phần tử ứng viên", "so sánh với phần tử phía sau"],
    ),
    (
        "sliding_window",
        ["subarray", "substring", "đoạn con", "liên tiếp", "cửa sổ", "window"],
        ["valid_window", "expand_shrink", "tracked_summary"],
        ["đoạn con liên tiếp", "cửa sổ hợp lệ"],
    ),
    (
        "two_pointers",
        ["hai con trỏ", "two pointers", "mảng sắp xếp", "cặp phần tử", "trái", "phải"],
        ["pointer_invariant", "move_condition", "sorted_property"],
        ["hai đầu trái/phải", "loại bỏ ứng viên"],
    ),
    (
        "hash_map",
        ["tần suất", "đếm", "xuất hiện", "duplicate", "trùng", "tồn tại", "hash"],
        ["key_value_meaning", "lookup_condition", "update_order"],
        ["tìm nhanh", "đếm hoặc kiểm tra tồn tại"],
    ),
    (
        "tree_dfs",
        ["cây", "tree", "node", "nút", "dfs", "đệ quy", "binary tree"],
        ["recursive_meaning", "child_result", "base_case"],
        ["quan hệ cha-con", "kết quả phụ thuộc cây con"],
    ),
    (
        "greedy",
        ["tham lam", "greedy", "chọn", "lớn nhất", "nhỏ nhất", "sắp xếp theo"],
        ["local_choice", "exchange_argument", "counterexample"],
        ["lựa chọn cục bộ", "tiêu chí sắp xếp"],
    ),
    (
        "sorting_searching",
        ["binary search", "tìm kiếm nhị phân", "sắp xếp", "sorted", "thứ tự"],
        ["search_space", "monotonic_property", "boundary_condition"],
        ["tính đơn điệu", "loại bỏ không gian tìm kiếm"],
    ),
]


def classify_problem(text: str) -> Classification:
    normalized = text.lower()
    scores: list[tuple[int, str, list[str], list[str], list[str]]] = []

    for topic, keywords, hint_path, signals in TAXONOMY_RULES:
        matched = [keyword for keyword in keywords if keyword in normalized]
        if matched:
            scores.append((len(matched), topic, matched, hint_path, signals))

    if not scores:
        return Classification(
            topic="array_string",
            pattern="general_iteration",
            confidence=0.45,
            key_signals=["dạng tổng quát, cần làm rõ input/output và ràng buộc"],
            recommended_hint_path=["input_output", "constraints", "small_example"],
        )

    score, topic, matched, hint_path, signals = max(scores, key=lambda item: item[0])
    confidence = min(0.95, 0.55 + score * 0.12)

    return Classification(
        topic=topic,
        pattern=hint_path[0],
        confidence=confidence,
        key_signals=signals + [f"từ khóa: {keyword}" for keyword in matched[:3]],
        recommended_hint_path=hint_path,
    )
