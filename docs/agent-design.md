# Thiết kế Agent

## Vai trò tổng thể

Hệ thống gồm một agent điều phối chính và các agent chuyên trách. `AI Tutor Agent` giữ vai trò trợ giảng cá nhân: hiểu trạng thái học, chọn công cụ phù hợp, tạo phản hồi nháp và chỉ gửi phản hồi sau khi qua quality review.

## AI Tutor Agent

Nhiệm vụ:

- Dùng LLM nhận diện intent: hỏi lý thuyết, gửi đề, xin gợi ý, gửi ý tưởng, gửi code, đòi lời giải trực tiếp.
- Cập nhật `LearningState`.
- Chọn module hoặc quality agent cần gọi.
- Dùng LLM để sinh phản hồi Socratic cuối cùng.
- Không trả lời trực tiếp từ LLM thô; phản hồi phải đi qua policy và `Pedagogy Critic Agent`.

Pipeline bắt buộc:

```text
LLM detect intent
-> update state
-> call learning modules
-> call quality agents if needed
-> draft response
-> pedagogy review
-> rewrite if needed
-> final response
```

Trong code hiện tại, pipeline này được bọc bằng `DsaTutorGraph`. LangGraph đã được tách thành nhiều node thay vì gộp toàn bộ agent vào một node lớn: `detect_intent`, `submit_problem`, `request_hint`, `submit_code`, `direct_solution_guard`, `submit_approach`, `ask_theory` và `finalize`. `DsaLearningAgent` vẫn là lõi nghiệp vụ, nhưng từng hành vi chính đã được tách thành method riêng để graph gọi trực tiếp.

## Learning Modules

### LLM Problem Classifier

Phân loại bài toán theo chủ đề và pattern tư duy: array/string, sliding window, hash map, stack, BFS, DFS, graph, greedy, dynamic programming, sorting/searching.

Output gồm `topic`, `pattern`, `confidence`, `key_signals`, `recommended_hint_path`.

### LLM Hint Generator

Sinh gợi ý theo cấp. LLM sinh gợi ý dựa trên `LearningState`, bài hiện tại, attempts gần nhất và policy Socratic. Các guideline trong `hints.py` chỉ dùng làm ngữ cảnh prompt, không phải câu trả lời cố định.

- Level 1: làm rõ input/output, constraint, ví dụ nhỏ.
- Level 2: gợi ý chiến lược hoặc cấu trúc dữ liệu.
- Level 3: gợi ý gần lời giải nhưng vẫn yêu cầu sinh viên tự hoàn thiện.
- Level 4: phản biện bằng edge cases, độ phức tạp và tính đúng.

### Code Analyzer

Phân tích code ở mức tư duy:

- Code đang thể hiện chiến lược nào?
- Mỗi phần tử/trạng thái được xử lý bao nhiêu lần?
- Có edge case nào dễ sai?
- Có thể tối ưu bằng cấu trúc dữ liệu hoặc trạng thái khác không?

## Quality Agents

### Testcase Generator Agent

Dùng LLM sinh testcase để người học tự kiểm:

- Basic case để trace tay.
- Edge case như input rỗng, một phần tử, toàn số âm, trùng lặp.
- Adversarial/stress case khi ràng buộc cho thấy nguy cơ TLE hoặc sai logic.
- `expected_output` có thể là `null` nếu đề bài chưa đủ rõ; khi đó testcase dùng để trace tay thay vì chấm tự động.

### Code Execution Validator Agent

Chạy code khi sandbox sẵn sàng:

- V1 chỉ hỗ trợ Python.
- Timeout mặc định 2 giây/test.
- Nếu testcase chưa có `expected_output`, validator bỏ qua testcase đó.
- Không dump đáp án; kết quả được Tutor Agent chuyển thành câu hỏi/gợi ý.

### Pedagogy Critic Agent

Dùng LLM kiểm phản hồi trước khi gửi:

- Có lộ full code/lời giải không?
- Có quá nhiều câu hỏi trong một lượt không?
- Có đúng hint level không?
- Có đủ tính Socratic không?

Nếu phản hồi không đạt, critic trả `revision_instruction` để Tutor Agent gọi LLM viết lại trước khi gửi.

## Intent và hành động

| Intent | Hành động |
| --- | --- |
| `ASK_THEORY` | Giải thích ngắn + hỏi kiểm tra hiểu |
| `SUBMIT_PROBLEM` | LLM phân loại bài + sinh testcase trace nhỏ + hỏi input/output |
| `REQUEST_HINT` | Tăng hint level + LLM sinh hint + pedagogy review |
| `SUBMIT_APPROACH` | Kiểm giả định bằng phản ví dụ và độ phức tạp |
| `SUBMIT_CODE` | Phân tích code + sinh testcase + validate bằng sandbox khi có thể |
| `ASK_DIRECT_SOLUTION` | Guard chặn lời giải trực tiếp + chuyển thành gợi ý |

## Nguyên tắc sản phẩm

- Chế độ mặc định là Socratic, không phải giải bài thuê.
- LLM được dùng cho các bước có thể cần hiểu ngữ cảnh: intent detection, classification, testcase generation, pedagogy review và final response.
- Các module heuristic còn lại đóng vai trò utility/guideline nội bộ để prompt có thêm ngữ cảnh và để test được những phần nhỏ.
