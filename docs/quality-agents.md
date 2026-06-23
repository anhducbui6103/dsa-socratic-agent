# Quality Agents

## Mục tiêu

Quality Layer giúp hệ thống không chỉ trả lời "nghe hợp lý", mà còn kiểm được ba khía cạnh:

- Bài toán có testcase đủ tốt để tự kiểm không?
- Code có chạy đúng trên testcase khi sandbox có thể chấm tự động không?
- Phản hồi có đúng tinh thần học tập Socratic không?

## Testcase Generator Agent

Input:

- Đề bài hiện tại.
- Kết quả phân loại bài toán.
- Ràng buộc nếu trích xuất được.

Output:

- `GeneratedTestCase`: `name`, `input`, `expected_output`, `category`, `rationale`.
- `TestSuite`: `problem_id`, `language`, `tests`, `coverage_notes`.

Nguyên tắc:

- Luôn có ít nhất một basic case và một edge case.
- Ưu tiên testcase nhỏ để sinh viên trace tay.
- `expected_output` có thể để `null` nếu đề bài chưa đủ rõ.
- Trong bản hiện tại, testcase thiên về hỗ trợ học tập; bản sau có thể bổ sung oracle theo từng dạng bài để chấm tự động tốt hơn.

## Code Execution Validator Agent

Input:

- Code sinh viên hoặc code nội bộ.
- Ngôn ngữ lập trình.
- TestSuite.
- Timeout.

Output:

- `ValidationResult`: `status`, `passed_count`, `failed_tests`, `runtime_errors`, `timeout`, `complexity_notes`.

Status:

- `PASSED`: tất cả testcase có expected output đều đúng.
- `FAILED`: chạy được nhưng sai output.
- `RUNTIME_ERROR`: code lỗi khi chạy.
- `TIMEOUT`: vượt giới hạn thời gian.
- `SKIPPED`: testcase chưa có expected output, sandbox chưa bật hoặc ngôn ngữ chưa hỗ trợ.

Sandbox v1:

- Chỉ hỗ trợ Python.
- Timeout mặc định 2 giây/test.
- Giới hạn stdout/stderr.
- Không network.
- Không dùng kết quả validation để dump đáp án; Tutor Agent chuyển kết quả thành câu hỏi hoặc gợi ý.

## Pedagogy Critic Agent

Input:

- Draft response.
- LearningState.
- Policy hiện tại.

Output:

- `PedagogyReview`: `safe_to_send`, `risk_level`, `issues`, `revision_instruction`.

Critic cần flag khi:

- Phản hồi chứa full code hoặc code block quá hoàn chỉnh.
- Phản hồi nói thẳng "đáp án là", "lời giải là", "công thức là" quá sớm.
- Không có câu hỏi gợi mở trong chế độ Socratic.
- Hỏi quá nhiều câu trong một lượt.

Nếu `safe_to_send = false`, Tutor Agent gọi LLM lần nữa với `revision_instruction`, sau đó review lại trước khi gửi.

## Failure modes

- Testcase mơ hồ: trả testcase có `expected_output = null` và giải thích rationale.
- Sandbox chưa chấm được: trả `SKIPPED`, tutor chuyển sang trace tay hoặc hỏi về edge case.
- Critic reject nhiều lần: trả phản hồi an toàn ngắn, yêu cầu sinh viên bổ sung input/output hoặc ý tưởng hiện tại thay vì đưa lời giải.
