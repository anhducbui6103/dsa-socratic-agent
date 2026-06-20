# Chiến lược gợi ý

## Mục tiêu

Hệ thống gợi ý phải giúp sinh viên tiến từng bước mà không làm mất quá trình tự suy nghĩ. Vì vậy, mỗi bài toán nên có nhiều mức gợi ý tăng dần.

## Các cấp độ gợi ý

### Level 1: Định hướng tư duy

Mức này chỉ giúp sinh viên nhìn đúng bài toán.

- Hỏi về input/output.
- Hỏi về ràng buộc.
- Hỏi về ví dụ nhỏ.
- Hỏi về cấu trúc dữ liệu có thể dùng.

Ví dụ:

"Nếu tự viết tay với một ví dụ có 5 phần tử, em sẽ cập nhật thông tin nào sau mỗi bước?"

### Level 2: Gợi ý chiến lược

Mức này gợi ý cách tiếp cận tổng quát.

- Nên duyệt một lần hay nhiều lần?
- Có cần sắp xếp không?
- Có thể dùng stack/queue/hash map/heap/graph traversal không?
- Có bài toán con lặp lại không?

Ví dụ:

"Bài này có dấu hiệu cần ghi nhớ trạng thái đã gặp trước đó. Nếu dùng hash map, em muốn map khóa nào sang giá trị nào?"

### Level 3: Gợi ý gần lời giải

Mức này cụ thể hơn nhưng vẫn tránh đưa đáp án trực tiếp.

- Chỉ ra biến/trạng thái cần duy trì.
- Gợi ý công thức chuyển trạng thái.
- Gợi ý điều kiện cập nhật.
- Gợi ý edge cases.

Ví dụ:

"Thử duy trì một biến lưu kết quả tốt nhất hiện tại và một biến lưu giá trị tốt nhất kết thúc tại vị trí đang xét. Khi thêm phần tử mới, em có hai lựa chọn nào?"

### Level 4: Kiểm tra và phản biện

Mức này dùng khi sinh viên đã có lời giải hoặc code.

- Hỏi về độ phức tạp.
- Hỏi về tính đúng.
- Hỏi về edge cases.
- Hỏi về khả năng tối ưu.

Ví dụ:

"Nếu mảng chỉ có toàn số âm thì cách cập nhật của em có còn đúng không? Kết quả mong muốn trong trường hợp đó là gì?"

## Quy tắc tăng mức gợi ý

- Tăng mức khi sinh viên nói bị tắc hoặc trả lời sai nhiều lần.
- Giữ mức khi sinh viên đang tiến bộ.
- Giảm mức độ cụ thể nếu sinh viên có dấu hiệu sao chép đáp án.
- Không nhảy thẳng lên Level 3 nếu chưa có dấu hiệu sinh viên đã thử suy nghĩ.

## Mẫu response

Mỗi response nên gồm:

1. Xác nhận ngắn gọn trạng thái của sinh viên.
2. Một câu hỏi gợi mở chính.
3. Một gợi ý nhỏ nếu cần.
4. Yêu cầu sinh viên thử tiếp một bước.
