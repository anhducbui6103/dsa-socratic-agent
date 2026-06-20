from __future__ import annotations

from .models import Classification, LearningState


TOPIC_HINTS: dict[str, list[str]] = {
    "array_string": [
        "Theo em, input và output đang biến đổi thông tin nào của dãy hoặc chuỗi?",
        "Nếu duyệt từ trái sang phải, em cần giữ lại thông tin trung gian nào?",
        "Có trường hợp biên nào như chuỗi rỗng, một phần tử, hoặc toàn giá trị giống nhau không?",
    ],
    "sliding_window": [
        "Cửa sổ hiện tại được xem là hợp lệ khi điều kiện nào đúng?",
        "Khi mở rộng cửa sổ làm điều kiện bị vi phạm, em sẽ thu hẹp từ phía nào?",
        "Em cần lưu những đại lượng nào để cập nhật cửa sổ mà không tính lại từ đầu?",
    ],
    "two_pointers": [
        "Hai con trỏ của em đại diện cho hai ứng viên hay hai biên của một vùng tìm kiếm?",
        "Khi điều kiện chưa đạt, dấu hiệu nào cho biết nên di chuyển con trỏ trái hay phải?",
        "Tính chất sắp xếp giúp em loại bỏ nhóm trường hợp nào sau mỗi bước?",
    ],
    "hash_map": [
        "Nếu dùng bảng băm, khóa và giá trị nên biểu diễn điều gì?",
        "Em cần tra cứu thông tin trước hay cập nhật tần suất trước ở mỗi phần tử?",
        "Trường hợp có phần tử trùng lặp sẽ ảnh hưởng đến cách cập nhật ra sao?",
    ],
    "stack": [
        "Phần tử nào cần được giữ lại để so sánh với phần tử xuất hiện sau?",
        "Điều kiện nào làm một phần tử không còn hữu ích và nên bị pop khỏi stack?",
        "Stack của em đang duy trì tính chất tăng, giảm hay một trạng thái khác?",
    ],
    "queue_bfs": [
        "Một trạng thái trong hàng đợi cần chứa những thông tin nào?",
        "Từ một trạng thái, em sinh ra các trạng thái kế tiếp bằng quy tắc nào?",
        "Em đánh dấu visited ở thời điểm đưa vào hàng đợi hay khi lấy ra? Vì sao?",
    ],
    "tree_dfs": [
        "Kết quả tại một nút phụ thuộc vào thông tin nào từ cây con trái và phải?",
        "Base case của lời gọi đệ quy là gì khi gặp nút rỗng hoặc lá?",
        "Em cần trả về gì từ mỗi lời gọi để nút cha dùng được?",
    ],
    "graph": [
        "Em biểu diễn quan hệ giữa các đối tượng thành đỉnh và cạnh như thế nào?",
        "Bài này cần duyệt toàn bộ graph, tìm đường đi, hay phát hiện chu trình?",
        "Nếu graph không liên thông, thuật toán của em có bỏ sót thành phần nào không?",
    ],
    "greedy": [
        "Lựa chọn cục bộ của em dựa trên tiêu chí nào?",
        "Em có thể nghĩ ra ví dụ nhỏ làm tiêu chí đó thất bại không?",
        "Sau khi chọn một phần tử, các lựa chọn còn lại thay đổi như thế nào?",
    ],
    "dynamic_programming": [
        "Trạng thái nhỏ nhất nào đủ mô tả một bài toán con?",
        "Kết quả của trạng thái hiện tại phụ thuộc vào những trạng thái trước nào?",
        "Base case là gì và thứ tự tính trạng thái nên đi theo chiều nào?",
    ],
    "sorting_searching": [
        "Tính chất nào cho phép em sắp xếp hoặc tìm kiếm nhị phân?",
        "Không gian tìm kiếm của em là chỉ số, giá trị, hay đáp án?",
        "Điều kiện biên nào dễ gây lệch một đơn vị ở left/right?",
    ],
}


def next_hint(state: LearningState, classification: Classification | None) -> str:
    topic = classification.topic if classification else state.problem_type or "array_string"
    hints = TOPIC_HINTS.get(topic, TOPIC_HINTS["array_string"])

    level = min(max(state.hint_level, 1), len(hints))
    hint = hints[level - 1]

    if level == 1:
        prefix = "Mình giữ gợi ý ở mức định hướng trước nhé."
    elif level == 2:
        prefix = "Ta tiến thêm một nấc về chiến lược."
    else:
        prefix = "Gợi ý này gần hơn với cấu trúc lời giải, nhưng em vẫn là người chốt bước tiếp theo."

    return f"{prefix}\n\n{hint}\n\nEm thử trả lời câu đó bằng một ví dụ nhỏ trước đã."


def direct_solution_guard() -> str:
    return (
        "Mình chưa đưa lời giải hoàn chỉnh ngay, vì mục tiêu là giúp em tự dựng được hướng đi.\n\n"
        "Thay vào đó, em thử nói: bài này cần tìm/đếm/tối ưu đại lượng nào, và ràng buộc input lớn cỡ nào? "
        "Từ hai thông tin đó mình sẽ gợi ý bước tiếp theo sát hơn."
    )
