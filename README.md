# AI Agent hỗ trợ học Cấu trúc dữ liệu và Giải thuật

Dự án xây dựng một hệ thống **LLM-powered multi-agent tutor** hỗ trợ sinh viên học Cấu trúc dữ liệu và Giải thuật theo hướng phát triển tư duy. Hệ thống ưu tiên đặt câu hỏi gợi mở, đưa ra gợi ý theo nhiều cấp độ và dùng quality agents để kiểm phản hồi trước khi gửi cho người học.

## Mục tiêu

- Phân loại bài toán theo từng dạng bài trong môn Cấu trúc dữ liệu và Giải thuật.
- Sinh gợi ý theo phương pháp Socratic, tăng dần theo `hint_level`.
- Xây dựng AI Tutor Agent có khả năng điều phối hội thoại, gọi module/agent phù hợp và quản lý trạng thái học tập.
- Phân tích code ở mức tư duy giải bài, độ phức tạp thuật toán và edge cases.
- Bổ sung Quality Layer gồm Testcase Generator, Code Execution Validator và Pedagogy Critic.

## Nguyên tắc sư phạm

Hệ thống không đóng vai trò là công cụ giải bài thay sinh viên. Agent hoạt động như một người hướng dẫn:

- Khuyến khích người học tự diễn giải ý tưởng.
- Đặt câu hỏi để kiểm tra giả định, biến, điều kiện đúng và độ phức tạp.
- Đưa ra gợi ý theo mức độ cần thiết, tăng dần khi người học gặp khó khăn.
- Tránh đưa code hoàn chỉnh hoặc đáp án trực tiếp trong chế độ mặc định.

## Thành phần chính

1. **AI Tutor Agent**
   - Trung tâm điều phối hội thoại.
   - Nhận diện intent, cập nhật trạng thái học tập và chọn module/agent phù hợp.
   - Không trả lời trực tiếp từ LLM thô; phản hồi cần qua policy và pedagogy review.

2. **LLM Problem Classifier**
   - Dùng Gemini để nhận diện chủ đề và dạng bài: mảng, danh sách liên kết, stack, queue, cây, đồ thị, quy hoạch động, tham lam, sắp xếp, tìm kiếm.
   - Trả output có cấu trúc gồm topic, pattern, confidence, signals và hướng gợi ý.

3. **Socratic Hint Generator**
   - Dùng LLM để sinh gợi ý dựa trên `LearningState`, intent hiện tại, `hint_level` và policy.
   - Các guideline trong code chỉ dùng để định hướng prompt, không phải câu trả lời cố định.

4. **Code Analysis Module**
   - Phân tích ý tưởng trong code.
   - Ước lượng độ phức tạp thời gian và bộ nhớ.
   - Phát hiện điểm có thể tối ưu hoặc edge case dễ sai.

5. **Quality Agents**
   - `Testcase Generator Agent`: dùng LLM sinh testcase để người học tự kiểm.
   - `Code Execution Validator Agent`: chạy Python code trong sandbox khi có testcase có expected output.
   - `Pedagogy Critic Agent`: dùng LLM kiểm phản hồi có đúng tinh thần Socratic không; nếu chưa đạt thì yêu cầu viết lại.

## Tài liệu thiết kế

- [Phạm vi dự án](docs/project-scope.md)
- [Kiến trúc hệ thống](docs/system-architecture.md)
- [Thiết kế Agent](docs/agent-design.md)
- [Quality Agents](docs/quality-agents.md)
- [Chiến lược gợi ý](docs/hint-strategy.md)
- [Phân loại bài toán](docs/problem-taxonomy.md)
- [Module phân tích code](docs/code-analysis.md)
- [Lộ trình phát triển](docs/roadmap.md)

## Prototype hiện tại

Repo đã có prototype Python trong thư mục `src/dsa_agent`. Hiện tại hệ thống có Streamlit UI, LangGraph workflow wrapper và Gemini API client:

- `orchestrator.py`: điều phối hội thoại; gọi LLM cho intent detection, problem classification, testcase generation, pedagogy review và final response.
- `llm_client.py`: Gemini REST client đọc `GEMINI_API_KEY` từ `.env`.
- `graph_workflow.py`: bọc Tutor Agent bằng LangGraph, tách workflow thành các node riêng như `detect_intent`, `submit_problem`, `request_hint`, `submit_code`, `direct_solution_guard`, `submit_approach`, `ask_theory` và `finalize`.
- `quality/`: schema và tool cho testcase, pedagogy review và execution validation.
- `code_analysis.py`: phân tích code bằng heuristic nhẹ để cung cấp context cho LLM.
- `intent.py`, `classifier.py`, `hints.py`: module tham chiếu/guideline nội bộ, không phải luồng trả lời chính.
- `app.py`: giao diện demo cho Đồ án 2 với nhiều phiên chat, khung nhập cố định phía dưới và panel trạng thái bên phải.

## Công nghệ sử dụng

- **Python** cho core agent.
- **Streamlit** cho giao diện demo, không cần backend riêng trong phạm vi Đồ án 2.
- **LangGraph** cho workflow orchestration.
- **Gemini API** cho LLM generation thông qua `GEMINI_API_KEY`.
- **python-dotenv** để đọc file `.env`.
- **unittest** cho kiểm thử.

## Kiến trúc xử lý

```text
User message
-> LLM intent detection
-> LangGraph route theo intent
-> Node tương ứng: submit_problem / request_hint / submit_code / direct_solution_guard / submit_approach / ask_theory
-> LLM classifier / LLM testcase generator / code analyzer / execution validator khi cần
-> LLM sinh draft response và Pedagogy Critic review
-> Nếu chưa an toàn: LLM rewrite
-> Trả phản hồi Socratic cho người học
```

## Cài đặt

```bash
pip install -e .
```

Tạo file `.env` ở thư mục gốc:

```env
GEMINI_API_KEY=AIza...
```

Không cần đặt key trong dấu ngoặc kép.

## Chạy giao diện Streamlit

```bash
streamlit run app.py
```

Trong UI hiện tại:

- Bên trái là danh sách phiên chat.
- Ở giữa là nội dung phiên chat hiện tại.
- Ô nhập chat luôn ghim dưới cùng.
- Bên phải hiển thị trạng thái học tập như `hint_level`, problem type, testcase gợi ý, validation và pedagogy review.
- Sandbox Python được bật sẵn trong agent; UI không hiện toggle.

## Chạy test

```bash
python -m unittest discover tests
```

Nếu không cài package ở chế độ editable, hãy đặt `PYTHONPATH=src` trước khi chạy các lệnh trên.
