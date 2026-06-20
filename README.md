# AI Agent hỗ trợ học Cấu trúc dữ liệu và Giải thuật

Dự án xây dựng một hệ thống AI Agent hỗ trợ sinh viên học môn Cấu trúc dữ liệu và Giải thuật theo hướng phát triển tư duy. Hệ thống ưu tiên đặt câu hỏi gợi mở và đưa ra gợi ý theo nhiều cấp độ thay vì cung cấp lời giải trực tiếp.

## Mục tiêu

- Phân loại bài toán theo từng dạng bài cụ thể trong môn Cấu trúc dữ liệu và Giải thuật.
- Thiết kế cơ chế gợi ý nhiều cấp độ tăng dần, dựa trên phương pháp Socratic.
- Xây dựng AI Agent có khả năng điều phối hội thoại theo ngữ cảnh học tập.
- Phát triển module phân tích code, tập trung vào tư duy giải bài, độ phức tạp thuật toán và khả năng tối ưu hóa.

## Nguyên tắc sư phạm

Hệ thống không đóng vai trò là công cụ giải bài thay sinh viên. Thay vào đó, agent đóng vai trò như một người hướng dẫn:

- Khuyến khích người học tự diễn giải ý tưởng.
- Đặt câu hỏi để kiểm tra giả định, biến, điều kiện đúng và độ phức tạp.
- Đưa ra gợi ý theo mức độ cần thiết, tăng dần khi người học gặp khó khăn.
- Tránh đưa code hoàn chỉnh hoặc đáp án trực tiếp.

## Thành phần chính

1. **Problem Classifier**
   - Nhận diện chủ đề và dạng bài: mảng, danh sách liên kết, stack, queue, cây, đồ thị, quy hoạch động, tham lam, sắp xếp, tìm kiếm.
   - Xác định dấu hiệu bài toán: input/output, ràng buộc, từ khóa, cấu trúc dữ liệu phù hợp.

2. **Socratic Hint Engine**
   - Tạo gợi ý theo nhiều cấp độ.
   - Ưu tiên câu hỏi gợi mở.
   - Kiểm soát việc không tiết lộ lời giải quá sớm.

3. **Conversation Orchestrator Agent**
   - Lưu trạng thái hội thoại và tiến trình học tập.
   - Quyết định bước tiếp theo: đặt câu hỏi, gợi ý, phân tích code, tóm tắt tiến trình.
   - Điều chỉnh độ khó dựa trên phản hồi của sinh viên.

4. **Code Analysis Module**
   - Phân tích ý tưởng trong code.
   - Ước lượng độ phức tạp thời gian và bộ nhớ.
   - Phát hiện điểm có thể tối ưu hóa.
   - Đưa ra nhận xét và câu hỏi thay vì sửa code hoàn chỉnh.

## Tài liệu thiết kế

- [Phạm vi dự án](docs/project-scope.md)
- [Kiến trúc hệ thống](docs/system-architecture.md)
- [Thiết kế Agent](docs/agent-design.md)
- [Chiến lược gợi ý](docs/hint-strategy.md)
- [Phân loại bài toán](docs/problem-taxonomy.md)
- [Module phân tích code](docs/code-analysis.md)
- [Lộ trình phát triển](docs/roadmap.md)

## Hướng phát triển đề xuất

Giai đoạn đầu nên xây dựng prototype tập trung vào 3 luồng chính:

1. Sinh viên gửi đề bài, agent phân loại dạng bài và hỏi câu hỏi định hướng.
2. Sinh viên yêu cầu gợi ý, agent tăng dần mức độ gợi ý.
3. Sinh viên gửi code, agent phân tích cách tiếp cận và đưa ra câu hỏi cải thiện.

Sau khi prototype ổn định, có thể bổ sung giao diện web, cơ sở dữ liệu lưu lịch sử học tập và bộ test đánh giá chất lượng gợi ý.

## Prototype hiện tại

Repo đã có prototype Python thuần trong thư mục `src/dsa_agent`:

- `classifier.py`: phân loại bài toán bằng luật từ khóa theo taxonomy DSA.
- `intent.py`: nhận diện intent như gửi đề, xin gợi ý, gửi code hoặc đòi lời giải trực tiếp.
- `hints.py`: tạo gợi ý Socratic theo cấp độ.
- `code_analysis.py`: nhận xét code ở mức ý tưởng, độ phức tạp và edge cases.
- `orchestrator.py`: điều phối hội thoại và cập nhật trạng thái học tập.
- `cli.py`: giao diện dòng lệnh để demo.

Chạy thử CLI:

```bash
python -m dsa_agent.cli
```

Chạy test:

```bash
python -m unittest discover tests
```

Nếu không cài package ở chế độ editable, hãy đặt `PYTHONPATH=src` trước khi chạy các lệnh trên.
