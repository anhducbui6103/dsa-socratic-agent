# Lộ trình phát triển

## Phase 1: Multi-Agent Specification

- Cập nhật kiến trúc 5 lớp.
- Định nghĩa schema cho learning state, testcase, validation và pedagogy review.
- Viết policy Socratic mặc định.
- Xác định các module heuristic chỉ là utility/guideline, không phải luồng trả lời chính.

## Phase 2: LLM Tutor Agent

- Thêm `llm_client` abstraction.
- Tích hợp Gemini API client.
- Thiết kế prompt cho Tutor Agent.
- Orchestrator gọi LLM cho intent detection, classification, testcase generation, pedagogy review và final response.
- Log module outputs và quality outputs để debug.

## Phase 3: Testcase Generator

- Sinh testcase bằng LLM theo taxonomy bài toán.
- Hỗ trợ basic, edge, adversarial/stress cases.
- Cho phép hiển thị testcase như bài tự kiểm cho sinh viên.
- Thêm evaluation set cho 10-20 bài DSA mẫu.
- Bổ sung expected output/oracle theo từng dạng bài ở bản sau.

## Phase 4: Pedagogy Critic

- Kiểm phản hồi có lộ lời giải/code không.
- Kiểm số lượng câu hỏi và mức độ gợi ý.
- Tự yêu cầu viết lại response khi không đạt policy.
- Chỉ gửi phản hồi sau khi review đạt hoặc đã được rút gọn an toàn.

## Phase 5: Sandbox Execution

- Hỗ trợ Python trước.
- Timeout 2 giây/test.
- Giới hạn output và môi trường chạy.
- Trả `SKIPPED` nếu testcase chưa có expected output, sandbox chưa bật hoặc ngôn ngữ chưa hỗ trợ.
- Chuyển validation result thành câu hỏi/gợi ý thay vì dump đáp án.

## Phase 6: Demo UI

- Xây dựng Streamlit chat UI cho demo Đồ án 2.
- Hỗ trợ nhiều phiên chat.
- Panel trạng thái học tập bên phải.
- Sandbox Python bật sẵn trong agent.
- Lưu session memory bền vững bằng SQLite/PostgreSQL nếu cần mở rộng.

## Milestone đề xuất

| Tuần | Kết quả |
| --- | --- |
| 1 | Kiến trúc multi-agent + schema + docs |
| 2 | LLM Tutor Agent và prompt policy |
| 3 | Testcase Generator Agent |
| 4 | Pedagogy Critic Agent |
| 5 | Sandbox Execution Python |
| 6 | Streamlit UI, evaluation và báo cáo |
