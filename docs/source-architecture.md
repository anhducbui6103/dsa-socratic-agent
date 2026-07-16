# Source Architecture

Tài liệu này giải thích cấu trúc source sau refactor. Mục tiêu chính là tách rõ các tầng, bỏ route bằng keyword cố định và để mọi quyết định ngữ nghĩa quan trọng đi qua LLM agent.

## Tổng Quan Layer

```text
UI layer
  app.py

Application/workflow layer
  graph_workflow.py
  orchestrator.py
  studio.py

Agent layer
  agents/intent_detector.py
  agents/problem_classifier.py
  agents/testcase_generator.py
  agents/response_generator.py
  agents/pedagogy_critic.py
  agents/session_title.py

Domain layer
  models.py
  hints.py

Infrastructure layer
  llm_client.py
  quality/validation.py
  code_analysis.py

Test layer
  tests/test_agent.py
```

## Luồng Xử Lý Chính

```text
User message
-> app.py nhận input
-> DsaTutorGraph.run(message)
-> detect_intent node gọi DsaLearningAgent.detect_intent()
-> IntentDetectorAgent gọi LLM và trả Intent
-> LangGraph route theo enum Intent, không route theo keyword
-> node nghiệp vụ gọi method tương ứng trong DsaLearningAgent
-> DsaLearningAgent gọi các specialist agents/tool cần thiết
-> SocraticResponseAgent tạo draft response
-> PedagogyCriticAgent review draft
-> nếu chưa an toàn, SocraticResponseAgent revise
-> trả AgentTurn cho UI
```

Điểm quan trọng: keyword không còn được dùng để chọn intent hoặc phân loại bài toán. Routing trong LangGraph chỉ dựa trên `Intent` đã được LLM agent suy luận.

## UI Layer

### `app.py`

Đây là Streamlit UI. File này không chứa logic phân loại intent hay phân loại bài toán. Nhiệm vụ của nó:

- Quản lý nhiều phiên chat trong `st.session_state`.
- Tạo `DsaTutorGraph` cho mỗi phiên chat.
- Nhận message từ người dùng và đưa vào `graph.run(...)`.
- Render chat history ở giữa màn hình.
- Render panel trạng thái bên phải: hint level, problem type, testcase, validation, pedagogy review.
- Gọi `SessionTitleAgent` thông qua `session.graph.agent.generate_session_title(...)` để đặt tiêu đề phiên, thay cho keyword title routing cũ.

UI chỉ là presentation layer. Nếu cần thay Streamlit bằng API server hoặc frontend khác, phần core trong `src/dsa_agent` vẫn dùng lại được.

## Application/Workflow Layer

### `graph_workflow.py`

File này bọc tutor bằng LangGraph. Các node hiện tại:

- `detect_intent`: gọi LLM intent detector thông qua `DsaLearningAgent`.
- `submit_problem`: xử lý đề bài mới.
- `request_hint`: tăng hint level và sinh gợi ý.
- `submit_code`: validate/review code.
- `direct_solution_guard`: chặn yêu cầu xin lời giải trực tiếp.
- `submit_approach`: phản biện ý tưởng của sinh viên.
- `ask_theory`: trả lời lý thuyết theo hướng gợi mở.
- `finalize`: đóng trace workflow.

`_route_intent` chỉ map `Intent` enum sang node tương ứng. Đây là routing theo kết quả agent, không phải keyword matching.

### `studio.py`

Entrypoint cho LangGraph Studio/LangGraph CLI. File này:

- Load `.env` từ root project.
- Tạo `DsaLearningAgent`.
- Bọc agent bằng `DsaTutorGraph`.
- Export biến `graph` để `langgraph.json` trỏ vào.

`langgraph.json` ở root khai báo:

```json
{
  "dependencies": ["."],
  "graphs": {
    "dsa_tutor": "dsa_agent.studio:graph"
  },
  "env": ".env"
}
```

Chạy:

```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev
```

### `orchestrator.py`

`DsaLearningAgent` là application service trung tâm. Nó không tự viết prompt dài cho từng agent nữa, mà khởi tạo và gọi các agent chuyên trách:

- `IntentDetectorAgent`
- `ProblemClassifierAgent`
- `TestcaseGeneratorAgent`
- `PedagogyCriticAgent`
- `SocraticResponseAgent`
- `SessionTitleAgent`
- `CodeExecutionValidatorAgent`

Các method chính:

- `handle(message)`: chạy full flow khi không dùng graph trực tiếp.
- `detect_intent(message)`: gọi LLM intent agent và ghi trace.
- `record_attempt(message)`: lưu attempt của sinh viên vào state.
- `run_intent(intent, message)`: gọi handler theo enum `Intent`.
- `handle_submit_problem(message)`: classify bài, sinh testcase, tạo guideline, sinh response.
- `handle_request_hint()`: tăng `hint_level`, lấy guideline từ `hints.py`, sinh response.
- `handle_submit_code(message)`: lấy/generate testcase, chạy validator, tạo guideline review code.
- `handle_direct_solution_request()`: chuyển yêu cầu xin lời giải thành gợi ý Socratic.
- `handle_submit_approach()`: hỏi phản ví dụ, edge case, độ phức tạp.
- `handle_theory_question()`: giải thích ngắn và kéo người học về ví dụ cụ thể.
- `generate_session_title(messages)`: gọi title agent.

Các helper nội bộ:

- `_generate_test_suite(...)`: gọi testcase agent và ghi trace số validation/trace-only tests.
- `_generate_reviewed_response(...)`: sinh response rồi đưa qua pedagogy critic.
- `_review_response(...)`: nếu critic báo chưa an toàn thì revise.
- `_code_review_guideline(...)`: ghép phân tích code + trạng thái validation thành guideline cho response agent.
- `_trace(...)`: ghi `AgentTraceItem` để UI/docs debug được flow.

## Agent Layer

### `agents/intent_detector.py`

LLM-only intent detector. Agent nhận toàn bộ message và trả JSON:

```json
{"intent":"SUBMIT_PROBLEM"}
```

Các intent hợp lệ nằm trong `models.Intent`:

- `ASK_THEORY`
- `SUBMIT_PROBLEM`
- `REQUEST_HINT`
- `SUBMIT_APPROACH`
- `SUBMIT_CODE`
- `ASK_DIRECT_SOLUTION`

File này có `_coerce_intent(...)` để normalize lỗi nhỏ trong output của LLM, ví dụ `SUBMITS_PROBLEM` về `SUBMIT_PROBLEM`. Đây không phải route keyword từ user input; nó chỉ sửa enum do LLM trả về.

### `agents/problem_classifier.py`

LLM problem classifier. Agent đọc đề bài và trả `Classification`:

- `topic`: nhóm bài như `sliding_window`, `graph`, `dynamic_programming`.
- `pattern`: pattern tư duy cụ thể.
- `confidence`: độ tin cậy.
- `key_signals`: tín hiệu LLM thấy trong đề.
- `recommended_hint_path`: hướng gợi ý nên đi.

Không còn `TAXONOMY_RULES` hay bảng keyword cố định trong source.

### `agents/testcase_generator.py`

LLM testcase generator. Agent sinh `TestSuite` gồm:

- `problem_id`
- `language`
- `coverage_notes`
- danh sách `GeneratedTestCase`

Mỗi testcase có:

- `name`
- `input`
- `expected_output`
- `purpose`: `validation` hoặc `trace_only`
- `category`: `basic`, `edge`, `adversarial`, `stress`
- `rationale`

Nếu `expected_output` là `null`, testcase dùng để trace tay thay vì chạy validator.

### `agents/response_generator.py`

Sinh phản hồi cuối cho sinh viên. Agent nhận `LearningState` và guideline nội bộ rồi tạo response Socratic.

Nó cũng có method `revise(...)`, dùng khi `PedagogyCriticAgent` báo response chưa an toàn.

Policy chính:

- Không đưa full code.
- Không nói thẳng đáp án cuối.
- Gợi ý tăng dần theo `hint_level`.
- Khi sinh viên gửi code, ưu tiên hỏi về trace, edge case hoặc độ phức tạp.

### `agents/pedagogy_critic.py`

Review response trước khi gửi. Agent trả `PedagogyReview`:

- `safe_to_send`
- `risk_level`
- `issues`
- `revision_instruction`

Nếu `safe_to_send` là `false` và có `revision_instruction`, orchestrator gọi response agent để sửa lại.

### `agents/session_title.py`

Sinh tiêu đề ngắn cho phiên chat từ các message đầu. UI gọi qua `DsaLearningAgent.generate_session_title(...)`.

### `agents/json_tools.py`

Utility nhỏ để parse JSON object từ output LLM. Có xử lý trường hợp model bọc JSON trong markdown fence.

## Domain Layer

### `models.py`

Chứa các dataclass và enum dùng xuyên suốt project:

- `Intent`
- `TestCategory`
- `TestPurpose`
- `ValidationStatus`
- `Classification`
- `GeneratedTestCase`
- `TestSuite`
- `FailedTest`
- `ValidationResult`
- `PedagogyReview`
- `AgentTraceItem`
- `EvaluationScore`
- `LearningState`
- `AgentTurn`

Đây là layer domain vì nó mô tả dữ liệu nghiệp vụ, không phụ thuộc Streamlit, LangGraph hay OpenRouter.

### `hints.py`

Chứa guideline gợi ý theo `topic` và `hint_level`. File này không route intent và không classify bài toán. Nó chỉ tạo guideline nội bộ để `SocraticResponseAgent` dùng làm ngữ cảnh khi sinh phản hồi.

Hai function chính:

- `next_hint(state, classification)`: lấy guideline phù hợp với topic/hint level.
- `direct_solution_guard()`: guideline khi người học xin lời giải trực tiếp.

## Infrastructure Layer

### `llm_client.py`

OpenRouter REST client. Interface chính là protocol:

```python
class LlmClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...
```

`OpenRouterLlmClient.from_env(...)` đọc `OPENROUTER_API_KEY`. Alias `GeminiLlmClient = OpenRouterLlmClient` được giữ để các import cũ vẫn chạy.

Client có:

- logging request/response preview không chứa API key.
- retry cho lỗi transient.
- normalize content dạng string hoặc list part.
- lỗi rõ ràng khi thiếu key.

### `quality/validation.py`

Sandbox validator cho code Python. Đây là deterministic tool, không phải LLM agent.

Nhiệm vụ:

- Bỏ qua nếu execution chưa bật.
- Chỉ hỗ trợ Python ở v1.
- Chặn import/call nguy hiểm trước khi chạy.
- Chạy code với timeout theo testcase.
- Hỗ trợ bài dạng stdin/stdout và dạng function-style.
- So sánh output text hoặc literal/JSON value.

Public API:

- `CodeExecutionValidatorAgent.validate(...)`
- `validate_code(...)`

### `code_analysis.py`

Phân tích code nhẹ để tạo context cho response agent. File này dùng heuristic để mô tả tín hiệu như vòng lặp, map/set, stack, queue, dp. Nó không route flow; output chỉ là guideline cho phần feedback code.

## Test Layer

### `tests/test_agent.py`

Test dùng `FakeLlmClient` để kiểm flow không cần gọi mạng thật.

Nhóm test chính:

- Agent flow: problem -> hint, direct solution guard, code analysis, LangGraph workflow, title agent.
- LLM output normalization: typo intent từ model vẫn được coerce.
- Validator: skipped, passed, failed, runtime error, timeout, blocked imports, function-style input.
- Agent layer: testcase generator và pedagogy critic được test qua fake LLM, không qua heuristic keyword.

Chạy:

```bash
python -m unittest discover -s tests
```

## Các File Đã Loại Bỏ

Sau refactor, các file sau bị xoá vì không còn phù hợp với kiến trúc agent-based hoặc không thuộc runtime project:

- `src/dsa_agent/intent.py`: route intent bằng regex/keyword.
- `src/dsa_agent/classifier.py`: classify bài bằng taxonomy keyword.
- `src/dsa_agent/quality/testcases.py`: testcase generator heuristic.
- `src/dsa_agent/quality/pedagogy.py`: pedagogy critic heuristic.
- Các artifact báo cáo/slides/script sinh report như `.pdf`, `.docx`, `.pptx`, `tools/`, report assets.

## Quy Ước Mở Rộng

Khi thêm tính năng mới:

1. Nếu tính năng cần hiểu ngữ nghĩa, thêm agent vào `src/dsa_agent/agents`.
2. Nếu tính năng chỉ là data contract, thêm vào `models.py`.
3. Nếu tính năng là tool deterministic như sandbox, đặt trong `quality/` hoặc một infrastructure package riêng.
4. Không thêm routing bằng keyword từ user input.
5. Mọi response gửi cho sinh viên nên đi qua `PedagogyCriticAgent`.
