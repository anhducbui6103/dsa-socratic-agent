from __future__ import annotations

from dataclasses import dataclass
import sys
from html import escape
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dsa_agent import DsaLearningAgent
from dsa_agent.graph_workflow import DsaTutorGraph
from dsa_agent.llm_client import GeminiLlmClient, MissingApiKeyError


# =========================
# Config
# =========================

APP_TITLE = "DSA Socratic Agent"
DEFAULT_MODEL = "google/gemini-2.5-flash"

LEFT_SCROLL_HEIGHT = 925
CHAT_SCROLL_HEIGHT = 800
RIGHT_SCROLL_HEIGHT = 925

LEFT_COL_RATIO = 0.18
MIDDLE_COL_RATIO = 0.55
RIGHT_COL_RATIO = 0.27


# =========================
# Data model
# =========================

@dataclass
class ChatSession:
    id: str
    title: str
    messages: list[dict[str, str]]
    graph: DsaTutorGraph | None


# =========================
# CSS
# =========================

PAGE_CSS = """
<style>
:root {
    --left-bg: #f4f4f5;
    --right-bg: #fafafa;
    --border: rgba(120, 120, 120, 0.22);
    --border-soft: rgba(120, 120, 120, 0.16);
    --text-main: #111827;
    --text-muted: #6b7280;
    --hover-bg: #e9e9eb;
    --active-bg: #dedee1;
    --row-height: 2.55rem;
}

/* Không để body/page tạo outer scroll. Mỗi vùng tự có scroll box riêng. */
html,
body,
[data-testid="stAppViewContainer"],
.block-container {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}

.block-container {
    padding: 0.65rem 0 0 0 !important;
    max-width: 100% !important;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    display: none;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}

/* 3 vùng chính */
div[data-testid="column"]:has(.left-root) {
    background: var(--left-bg);
    border-right: 1px solid var(--border-soft);
    padding: 0.6rem 0.55rem !important;
    height: calc(100vh - 0.65rem) !important;
    overflow: hidden !important;
}

div[data-testid="column"]:has(.middle-root) {
    background: #ffffff;
    padding: 0.6rem 1.25rem 0.7rem 1.25rem !important;
    height: calc(100vh - 0.65rem) !important;
    overflow: hidden !important;
}

div[data-testid="column"]:has(.right-root) {
    background: var(--right-bg);
    border-left: 1px solid var(--border);
    padding: 0.6rem 0.75rem 0.8rem 0.85rem !important;
    height: calc(100vh - 0.65rem) !important;
    overflow: hidden !important;
}

/* Scroll container của Streamlit */
div[data-testid="column"]:has(.left-root) div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="column"]:has(.right-root) div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 0 !important;
    box-shadow: none !important;
    background: transparent !important;
}

div[data-testid="column"]:has(.middle-root) div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 0 !important;
    box-shadow: none !important;
    background: transparent !important;
    max-width: 820px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Sidebar buttons */
.chat-list-title {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text-muted);
    margin: 0.35rem 0.35rem 0.75rem 0.35rem;
}

.new-session-wrap div[data-testid="stButton"] > button,
.session-title-wrap div[data-testid="stButton"] > button,
.session-delete-wrap div[data-testid="stButton"] > button {
    border: 1px solid rgba(120, 120, 120, 0.18) !important;
    box-shadow: none !important;
    min-height: var(--row-height) !important;
    height: var(--row-height) !important;
    border-radius: 12px !important;
    color: var(--text-main) !important;
    background: rgba(255, 255, 255, 0.92) !important;
}

.new-session-wrap div[data-testid="stButton"] > button {
    justify-content: center !important;
    font-weight: 500 !important;
    margin-bottom: 0.65rem;
}

.session-title-wrap div[data-testid="stButton"] > button {
    justify-content: flex-start !important;
    padding: 0.35rem 0.8rem !important;
    width: 100% !important;
    text-align: left !important;
}

.session-delete-wrap div[data-testid="stButton"] > button {
    justify-content: center !important;
    padding: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    font-size: 0.95rem !important;
    color: #6b7280 !important;
}

.new-session-wrap div[data-testid="stButton"] > button:hover,
.session-title-wrap div[data-testid="stButton"] > button:hover,
.session-delete-wrap div[data-testid="stButton"] > button:hover {
    background: var(--hover-bg) !important;
    color: var(--text-main) !important;
}

.active-session-row + div .session-title-wrap div[data-testid="stButton"] > button,
.active-session-row + div .session-delete-wrap div[data-testid="stButton"] > button {
    background: var(--active-bg) !important;
    font-weight: 600 !important;
}

/* Chat */
div[data-testid="column"]:has(.middle-root) div[data-testid="stChatMessage"] {
    max-width: 760px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.empty-chat {
    color: var(--text-muted);
    padding: 28vh 0 0 0;
    text-align: center;
}

.chat-input-separator {
    max-width: 760px;
    margin: 0.55rem auto 0.55rem auto;
    border-top: 1px solid rgba(120, 120, 120, 0.18);
}

div[data-testid="column"]:has(.middle-root) div[data-testid="stForm"] {
    max-width: 760px !important;
    margin: 0 auto !important;
    border: 0 !important;
    background: #eef0f4 !important;
    border-radius: 14px !important;
    padding: 0.45rem 0.55rem !important;
}

div[data-testid="column"]:has(.middle-root) div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
    gap: 0.5rem !important;
    align-items: center !important;
}

div[data-testid="column"]:has(.middle-root) div[data-testid="stTextInput"] input {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    font-size: 0.92rem !important;
}

div[data-testid="column"]:has(.middle-root) div[data-testid="stTextInput"] input:focus {
    border: 0 !important;
    box-shadow: none !important;
}

div[data-testid="column"]:has(.middle-root) div[data-testid="stForm"] button {
    width: 2.4rem !important;
    height: 2.4rem !important;
    min-height: 2.4rem !important;
    border-radius: 10px !important;
    padding: 0 !important;
    justify-content: center !important;
}

div[data-testid="stChatInput"] {
    display: none !important;
}

/* Right cards */
.panel-card {
    border: 1px solid rgba(120, 120, 120, 0.18);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
    background: #ffffff;
}

.panel-title {
    color: #8a8f98;
    font-size: 0.95rem;
    margin-bottom: 0.75rem;
}

.stat-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid rgba(120, 120, 120, 0.12);
}

.stat-row:last-child {
    border-bottom: 0;
}

.stat-label {
    color: var(--text-muted);
}

.stat-value {
    font-weight: 600;
    text-align: right;
}

.panel-code {
    background: #f6f7f9;
    border-radius: 10px;
    padding: 0.85rem 0.95rem;
    margin: 0.65rem 0 1rem 0;
    overflow-x: auto;
    font-size: 0.82rem;
    line-height: 1.45;
}

.panel-test-name {
    font-weight: 700;
    color: #111827;
    margin-top: 0.75rem;
}

.panel-badge {
    display: inline-block;
    margin-left: 0.35rem;
    padding: 0.08rem 0.35rem;
    border-radius: 6px;
    background: #eefdf3;
    color: #15803d;
    font-size: 0.72rem;
    font-weight: 600;
}

.panel-caption {
    color: var(--text-muted);
    font-size: 0.82rem;
    margin: 0.55rem 0 0.3rem 0;
}

/* Native Streamlit container used as right panel card */
div[data-testid="column"]:has(.right-root) div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px !important;
}

div[data-testid="column"]:has(.right-root) div[data-testid="stVerticalBlockBorderWrapper"]:has(.panel-title) {
    border: 1px solid rgba(120, 120, 120, 0.18) !important;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05) !important;
    background: #ffffff !important;
}

</style>
"""


# =========================
# App / session lifecycle
# =========================

def setup_page() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    load_dotenv(ROOT_DIR / ".env")
    st.markdown(PAGE_CSS, unsafe_allow_html=True)


def init_session_state() -> None:
    if "model_name" not in st.session_state:
        st.session_state.model_name = DEFAULT_MODEL

    if "chat_sessions" not in st.session_state:
        first_session = create_session()
        st.session_state.chat_sessions = {first_session.id: first_session}
        st.session_state.active_session_id = first_session.id

    st.session_state.setdefault("pending_delete_session_id", None)
    st.session_state.setdefault("pending_response_session_id", None)
    st.session_state.setdefault("pending_user_message", None)


def create_agent() -> DsaTutorGraph:
    model = st.session_state.get("model_name", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    llm_client = GeminiLlmClient.from_env(model=model)
    agent = DsaLearningAgent(enable_execution=True, llm_client=llm_client)
    return DsaTutorGraph(agent)


def create_session(title: str = "Phiên mới") -> ChatSession:
    try:
        graph = create_agent()
    except MissingApiKeyError:
        graph = None

    return ChatSession(
        id=str(uuid4()),
        title=title,
        messages=[],
        graph=graph,
    )


def current_session() -> ChatSession:
    return st.session_state.chat_sessions[st.session_state.active_session_id]


def set_active_session(session_id: str) -> None:
    st.session_state.active_session_id = session_id


def new_session() -> None:
    session = create_session()
    st.session_state.chat_sessions[session.id] = session
    st.session_state.active_session_id = session.id


def delete_session(session_id: str) -> None:
    sessions: dict[str, ChatSession] = st.session_state.chat_sessions

    if session_id in sessions:
        del sessions[session_id]

    if not sessions:
        new_session()
        return

    if st.session_state.active_session_id == session_id:
        st.session_state.active_session_id = next(reversed(sessions))


# =========================
# Agent turn processing
# =========================

def process_pending_turn(session: ChatSession) -> None:
    pending_message = st.session_state.get("pending_user_message")
    pending_session_id = st.session_state.get("pending_response_session_id")

    if not pending_message or pending_session_id != session.id:
        return

    try:
        if session.graph is None:
            session.graph = create_agent()

        turn = session.graph.run(pending_message)
        assistant_message = turn.response

    except MissingApiKeyError as exc:
        assistant_message = (
            f"Thiếu LLM API key: `{exc}`. "
            "Hãy cấu hình key trong file `.env` rồi tạo phiên mới."
        )
    except Exception as exc:
        assistant_message = f"Hệ thống gặp lỗi khi xử lý lượt này: `{exc}`"
    finally:
        st.session_state.pending_response_session_id = None
        st.session_state.pending_user_message = None

    session.messages.append({"role": "assistant", "content": assistant_message})
    st.rerun()


def submit_user_message(session: ChatSession, user_message: str) -> None:
    user_message = user_message.strip()
    if not user_message:
        return

    session.messages.append({"role": "user", "content": user_message})
    update_session_title(session, user_message)

    st.session_state.pending_response_session_id = session.id
    st.session_state.pending_user_message = user_message
    st.rerun()


def update_session_title(session: ChatSession, first_message: str) -> None:
    if session.title != "Phiên mới":
        return

    normalized = first_message.lower()

    if "```" in first_message or "def " in normalized or "class " in normalized:
        session.title = "Phân tích code"
    elif any(keyword in normalized for keyword in ("gợi ý", "hint", "bị tắc", "không biết làm")):
        session.title = "Xin gợi ý"
    elif any(keyword in normalized for keyword in ("full code", "lời giải", "đáp án")):
        session.title = "Yêu cầu lời giải"
    elif any(keyword in normalized for keyword in ("quy hoạch động", "dp")):
        session.title = "Bài quy hoạch động"
    elif any(keyword in normalized for keyword in ("đồ thị", "graph", "bfs", "dfs")):
        session.title = "Bài đồ thị"
    elif any(keyword in normalized for keyword in ("mảng", "chuỗi", "array", "string")):
        session.title = "Bài mảng/chuỗi"
    else:
        words = " ".join(first_message.split()[:5])
        session.title = f"Bài DSA: {words}" if words else "Phiên học DSA"


# =========================
# Render helpers
# =========================

def render_marker(class_name: str) -> None:
    st.markdown(f'<div class="{class_name}"></div>', unsafe_allow_html=True)


def render_wrapped_button_start(class_name: str) -> None:
    st.markdown(f'<div class="{class_name}">', unsafe_allow_html=True)


def render_wrapped_button_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("Xoá phiên chat?")
def confirm_delete_session() -> None:
    session_id = st.session_state.pending_delete_session_id
    session = st.session_state.chat_sessions.get(session_id)

    if session is None:
        st.session_state.pending_delete_session_id = None
        return

    st.write(f"Bạn có chắc muốn xoá phiên **{session.title}** không?")
    st.caption("Hành động này sẽ xoá nội dung chat và trạng thái học tập của phiên này.")

    delete_col, cancel_col = st.columns(2)

    with delete_col:
        if st.button("Xoá phiên", use_container_width=True):
            delete_session(session_id)
            st.session_state.pending_delete_session_id = None
            st.rerun()

    with cancel_col:
        if st.button("Huỷ", use_container_width=True):
            st.session_state.pending_delete_session_id = None
            st.rerun()


def render_left_sidebar() -> None:
    render_marker("left-root")

    with st.container(height=LEFT_SCROLL_HEIGHT, border=False):
        st.markdown('<div class="chat-list-title">Đoạn chat</div>', unsafe_allow_html=True)

        render_wrapped_button_start("new-session-wrap")
        if st.button("+ Phiên mới", use_container_width=True):
            new_session()
        render_wrapped_button_end()

        for session in list(st.session_state.chat_sessions.values()):
            render_session_row(session)

        if st.session_state.pending_delete_session_id:
            confirm_delete_session()


def render_session_row(session: ChatSession) -> None:
    selected = session.id == st.session_state.active_session_id
    if selected:
        st.markdown('<span class="active-session-row"></span>', unsafe_allow_html=True)

    title_col, delete_col = st.columns([0.84, 0.16], gap="small")

    with title_col:
        render_wrapped_button_start("session-title-wrap")
        if st.button(session.title, key=f"session-{session.id}", use_container_width=True):
            set_active_session(session.id)
            st.session_state.pending_delete_session_id = None
        render_wrapped_button_end()

    with delete_col:
        render_wrapped_button_start("session-delete-wrap")
        if st.button("🗑", key=f"ask-delete-{session.id}", use_container_width=True):
            st.session_state.pending_delete_session_id = session.id
        render_wrapped_button_end()


def render_middle_content() -> None:
    render_marker("middle-root")
    session = current_session()

    render_chat_history(session)
    render_chat_form(session)


def render_chat_history(session: ChatSession) -> None:
    with st.container(height=CHAT_SCROLL_HEIGHT, border=False):
        if not session.messages:
            st.markdown(
                '<div class="empty-chat">Bắt đầu bằng cách gửi đề bài, ý tưởng, code hoặc yêu cầu gợi ý.</div>',
                unsafe_allow_html=True,
            )
        else:
            for message in session.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if st.session_state.pending_response_session_id == session.id:
            with st.spinner("Agent đang suy nghĩ..."):
                process_pending_turn(session)


def render_chat_form(session: ChatSession) -> None:
    st.markdown('<div class="chat-input-separator"></div>', unsafe_allow_html=True)

    with st.form("chat_input_form", clear_on_submit=True):
        input_col, send_col = st.columns([0.92, 0.08], gap="small")

        with input_col:
            user_message = st.text_input(
                "Tin nhắn",
                placeholder="Nhập đề bài, xin gợi ý, hoặc gửi code của bạn...",
                label_visibility="collapsed",
            )

        with send_col:
            submitted = st.form_submit_button("↑", use_container_width=True)

    if submitted:
        submit_user_message(session, user_message)


def render_right_sidebar() -> None:
    render_marker("right-root")

    with st.container(height=RIGHT_SCROLL_HEIGHT, border=False):
        session = current_session()
        graph = session.graph

        if graph is None:
            render_missing_key_panel()
            return

        state = graph.agent.state

        render_environment_panel(state)

        if state.generated_tests:
            render_testcases_panel(state)

        if state.latest_validation:
            render_validation_panel(state)

        if state.pedagogy_flags:
            render_pedagogy_panel(state)


def render_missing_key_panel() -> None:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Environment</div>
            <div class="stat-row">
                <span class="stat-label">LLM API</span>
                <span class="stat-value">Missing key</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning("Hãy cấu hình LLM API key trong file `.env` rồi tạo phiên mới.")


def render_environment_panel(state) -> None:
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="panel-title">Environment</div>
            <div class="stat-row">
                <span class="stat-label">Hint level</span>
                <span class="stat-value">{state.hint_level}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Problem type</span>
                <span class="stat-value">{state.problem_type or "Chưa có"}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_testcases_panel(state) -> None:
    latest_suite = state.generated_tests[-1]

    with st.container(border=True):
        st.markdown('<div class="panel-title">Testcase gợi ý</div>', unsafe_allow_html=True)

        for test in latest_suite.tests:
            st.markdown(
                f"""
                <div class="panel-test-name">
                    {escape(str(test.name))}
                    <span class="panel-badge">{escape(str(test.category.value))}</span>
                </div>
                <div class="panel-caption">{escape(str(test.rationale))}</div>
                """,
                unsafe_allow_html=True,
            )
            st.code(str(test.input), language="python")


def render_validation_panel(state) -> None:
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="panel-title">Validation</div>
            <div class="stat-row">
                <span class="stat-label">Status</span>
                <span class="stat-value">{state.latest_validation.status.value}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Passed</span>
                <span class="stat-value">{state.latest_validation.passed_count}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if state.latest_validation.failed_tests:
        st.write("**Failed tests:**", [test.name for test in state.latest_validation.failed_tests])


def render_pedagogy_panel(state) -> None:
    latest_review = state.pedagogy_flags[-1]

    st.markdown(
        f"""
        <div class="panel-card">
            <div class="panel-title">Pedagogy review</div>
            <div class="stat-row">
                <span class="stat-label">Risk</span>
                <span class="stat-value">{latest_review.risk_level}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Safe to send</span>
                <span class="stat-value">{latest_review.safe_to_send}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if latest_review.issues:
        st.write("**Issues:**", latest_review.issues)


# =========================
# Main
# =========================

def render_layout() -> None:
    left_col, middle_col, right_col = st.columns(
        [LEFT_COL_RATIO, MIDDLE_COL_RATIO, RIGHT_COL_RATIO],
        gap="small",
    )

    with left_col:
        render_left_sidebar()

    with middle_col:
        render_middle_content()

    with right_col:
        render_right_sidebar()


def main() -> None:
    setup_page()
    init_session_state()
    render_layout()


if __name__ == "__main__":
    main()
