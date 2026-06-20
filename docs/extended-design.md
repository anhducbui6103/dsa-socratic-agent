# Thiết kế mở rộng cho DSA Socratic Agent

Tài liệu này mô tả phiên bản mở rộng của project sau khi bổ sung các thành phần giúp hệ thống thể hiện rõ tính agentic AI hơn trong phạm vi Đồ án 2.

## Mục tiêu mở rộng

- Thể hiện workflow multi-agent rõ ràng bằng LangGraph.
- Cho phép quan sát pipeline xử lý qua Agent Trace.
- Sinh tiêu đề ngắn cho từng phiên chat thay vì dùng nguyên văn message đầu tiên.
- Cải thiện quality layer bằng chính sách testcase có expected output và trace-only testcase.
- Chuẩn hóa dữ liệu đánh giá để demo và viết báo cáo dễ hơn.

## Các agent bổ sung

### Session Title Agent

Sinh tiêu đề ngắn cho một phiên chat dựa trên các lượt trao đổi đầu tiên.

Input:

- `messages`: các message đầu phiên.
- `problem_type`: nếu đã phân loại được.

Output:

- `title`: 3-6 từ, ví dụ `Maximum Subarray`, `DFS trên đồ thị`, `Sliding Window`.

Policy:

- Không dùng nguyên văn toàn bộ câu hỏi dài.
- Không chứa API key, code dài hoặc dữ liệu nhạy cảm.
- Nếu chưa đủ ngữ cảnh, dùng `Phiên mới`.

### Agent Trace Logger

Ghi lại các bước workflow đã chạy trong một lượt hội thoại.

Input:

- `session_id`
- `node_name`
- `status`
- `summary`
- `structured_output`

Output:

- Danh sách trace item để UI hiển thị ở panel bên phải.

Lưu ý:

- Agent Trace không phải chain-of-thought của LLM.
- Chỉ ghi dữ liệu kỹ thuật ở mức workflow: node nào chạy, kết quả rút gọn, trạng thái pass/fail.

### Evaluation Agent

Đánh giá phản hồi cuối sau một số kịch bản demo.

Tiêu chí:

- Có tránh full solution không?
- Có đúng hint level không?
- Có tập trung 1-2 gợi ý chính không?
- Có tận dụng testcase hoặc validation result không?
- Có phù hợp với trạng thái học tập không?

## Cập nhật LearningState

Đề xuất bổ sung:

```python
chat_title: str
agent_trace: list[AgentTraceItem]
evaluation_scores: list[EvaluationScore]
```

Schema gợi ý:

```python
class AgentTraceItem:
    node_name: str
    status: str
    summary: str
    metadata: dict

class EvaluationScore:
    safe_socratic: bool
    hint_level_match: bool
    concise: bool
    uses_quality_signal: bool
    notes: list[str]
```

## UI đề xuất

Bố cục Streamlit:

- Cột trái: danh sách phiên chat, title ngắn, nút tạo phiên, nút xóa phiên.
- Vùng giữa: nội dung chat hiện tại.
- Ô nhập: cố định phía dưới.
- Panel phải: trạng thái học tập, testcase/validation summary, pedagogy review và Agent Trace.

Agent Trace hiển thị theo dạng timeline:

```text
Intent Detector -> State Update -> Hint Generator -> Pedagogy Critic -> Finalize
```

## Chính sách testcase

Testcase được chia thành hai loại:

- `validation`: có `expected_output`, dùng được cho execution validator.
- `trace_only`: chưa chắc expected output, dùng để sinh viên tự trace.

Nguyên tắc:

- Không ép LLM sinh expected output khi đề bài chưa đủ rõ.
- Nếu có reference solution nội bộ, chỉ dùng để tạo oracle, không hiển thị.
- Khi trả cho sinh viên, chỉ diễn giải testcase như công cụ tự kiểm, không dump lời giải.

## Kịch bản demo

1. Sinh viên gửi đề Maximum Subarray.
2. Agent detect intent, classify thành dynamic programming/array.
3. Agent sinh testcase basic và edge case toàn số âm.
4. Sinh viên xin gợi ý, hint level tăng và Pedagogy Critic review phản hồi.
5. Sinh viên gửi code sai với toàn số âm.
6. Validator phát hiện fail hoặc trace-only case làm lộ vấn đề.
7. Tutor hỏi dẫn về cách khởi tạo biến trạng thái.
8. Sinh viên xin full solution, guard chuyển thành gợi ý cao hơn thay vì đưa code hoàn chỉnh.

## Thứ tự triển khai code

1. Thêm schema `AgentTraceItem` và `EvaluationScore`.
2. Bổ sung trace collector vào LangGraph nodes.
3. Thêm Session Title Agent sau 1-2 lượt message đầu.
4. Cập nhật Streamlit panel phải để hiển thị Agent Trace.
5. Cập nhật Testcase Generator để phân biệt `validation` và `trace_only`.
6. Thêm Evaluation Agent cho kịch bản demo.
