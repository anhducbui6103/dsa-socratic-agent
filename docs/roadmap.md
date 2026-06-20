# Lộ trình phát triển

## Phase 1: Đặc tả và prototype

- Hoàn thiện taxonomy bài toán DSA.
- Định nghĩa schema trạng thái hội thoại.
- Xây dựng prompt/policy cho Socratic Agent.
- Tạo prototype CLI hoặc web chat đơn giản.
- Thử nghiệm với 10-20 bài tập mẫu.

## Phase 2: Core Agent

- Xây dựng intent detector.
- Xây dựng problem classifier ban đầu.
- Xây dựng hint engine theo 3-4 mức.
- Lưu session memory.
- Thêm bộ quy tắc chặn lời giải trực tiếp.

## Phase 3: Code Analysis

- Nhận diện ngôn ngữ lập trình.
- Trích xuất dấu hiệu thuật toán từ code.
- Ước lượng độ phức tạp.
- Tạo nhận xét Socratic.
- Đề xuất edge cases để sinh viên tự test.

## Phase 4: Evaluation

- Thiết kế bộ test hội thoại.
- Đánh giá chất lượng gợi ý theo tiêu chí:
  - Không lộ đáp án quá sớm.
  - Gợi ý có liên quan.
  - Có tính Socratic.
  - Giúp sinh viên tiến thêm một bước.
- So sánh với chatbot trả lời trực tiếp.

## Phase 5: Productization

- Xây dựng UI chat.
- Thêm lịch sử học tập.
- Thêm dashboard tiến trình theo chủ đề.
- Thêm chế độ giảng viên cấu hình bài tập và mức độ gợi ý.

## Milestone đề xuất

| Tuần | Kết quả |
| --- | --- |
| 1 | Hoàn thiện yêu cầu và kiến trúc |
| 2 | Prototype agent hội thoại có hint levels |
| 3 | Problem classifier ban đầu |
| 4 | Module phân tích code ban đầu |
| 5 | Web UI và session memory |
| 6 | Test, đánh giá, viết báo cáo |
