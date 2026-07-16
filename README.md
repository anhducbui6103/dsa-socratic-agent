# DSA Socratic Agent

LLM-powered tutor hỗ trợ học Cấu trúc dữ liệu và Giải thuật theo phương pháp Socratic. Ứng dụng dùng nhiều agent chuyên trách để hiểu intent, phân loại bài toán, sinh testcase học tập, tạo phản hồi, kiểm phản hồi bằng pedagogy critic và validate code Python khi có expected output.

## Điểm chính

- `DsaTutorGraph` dùng LangGraph để điều phối node theo `Intent` do LLM suy luận.
- `DsaLearningAgent` giữ vai trò application service: cập nhật state, gọi agent chuyên trách, gọi validator và trả `AgentTurn`.
- Các LLM agent nằm trong `src/dsa_agent/agents`.
- Quality layer runtime chỉ còn sandbox execution validator trong `src/dsa_agent/quality`.
- Streamlit UI ở `app.py` dùng cùng agent graph cho từng phiên chat.

## Cấu Trúc

```text
app.py
src/dsa_agent/
  agents/
  graph_workflow.py
  orchestrator.py
  models.py
  llm_client.py
  hints.py
  code_analysis.py
  quality/
tests/
docs/source-architecture.md
```

Giải thích chi tiết từng layer và từng file nằm ở [docs/source-architecture.md](docs/source-architecture.md).

## Cài Đặt

```bash
pip install -e .
```

Tạo file `.env` ở thư mục gốc:

```env
OPENROUTER_API_KEY=...
```

Mặc định app dùng model `google/gemini-2.5-flash` qua OpenRouter client.

## Chạy App

```bash
streamlit run app.py
```

## Chạy LangGraph Studio

Project đã có `langgraph.json` trỏ tới graph `dsa_tutor`.

```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev
```

Sau khi server chạy, mở URL Studio mà CLI in ra. Graph được export từ:

```text
dsa_agent.studio:graph
```

## Chạy Test

```bash
python -m unittest discover -s tests
```
