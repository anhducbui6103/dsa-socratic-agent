from __future__ import annotations

from dataclasses import dataclass
from html import escape
import sys
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dsa_agent import DsaLearningAgent
from dsa_agent.graph_workflow import DsaTutorGraph
from dsa_agent.llm_client import GeminiLlmClient, MissingApiKeyError, TransientLlmError


@dataclass
class ChatSession:
    id: str
    title: str
    messages: list[dict[str, str]]
    graph: DsaTutorGraph | None


st.set_page_config(page_title="DSA Socratic Agent", layout="wide")
load_dotenv(ROOT_DIR / ".env")

st.markdown(
    """
    <style>
    :root {
        --sidebar-width: 18rem;
        --right-width: 23rem;
        --page-bg: #ffffff;
        --sidebar-bg: #f4f4f5;
        --border: #d9dce2;
        --muted: #6b7280;
        --ink: #0f172a;
        --soft: #eef0f4;
        --active: #dedee1;
        --blue: #0f3764;
    }

    .block-container {
        padding: 0 !important;
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

    div[data-testid="column"]:first-of-type {
        flex: 0 0 var(--sidebar-width) !important;
        width: var(--sidebar-width) !important;
        min-width: 12rem !important;
        max-width: 24rem !important;
        background: var(--sidebar-bg);
        min-height: 100vh;
        border-right: 1px solid var(--border);
        padding: 1rem 0.85rem;
        overflow: hidden;
    }

    div[data-testid="column"]:nth-of-type(2) {
        display: none;
    }

    div[data-testid="column"]:nth-of-type(3) {
        background: var(--page-bg);
        min-height: 100vh;
        padding: 1.45rem 2.3rem 7.5rem 2.8rem;
    }

    div[data-testid="column"]:nth-of-type(4) {
        flex: 0 0 var(--right-width) !important;
        width: var(--right-width) !important;
        background: var(--page-bg);
        min-height: 100vh;
        padding: 2.9rem 1.7rem 2rem 1rem;
    }

    div[data-testid="stChatInput"] {
        position: fixed;
        left: calc(var(--sidebar-width) + 5rem);
        right: calc(var(--right-width) + 3rem);
        bottom: 1.4rem;
        z-index: 100;
        background: transparent;
    }

    div[data-testid="stChatInput"] > div {
        border-radius: 10px !important;
        background: #eef0f4;
        border: 0 !important;
    }

    .sidebar-title {
        font-weight: 800;
        font-size: 1.05rem;
        color: #3f3f46;
        margin: 0.25rem 0 0.75rem 0.15rem;
    }

    .app-title {
        font-weight: 800;
        font-size: 1.08rem;
        color: var(--blue);
        margin: 0 0 1.9rem 0;
    }

    .new-session-link {
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #d1d5db !important;
        background: #ffffff !important;
        color: #111827 !important;
        height: 1.72rem;
        border-radius: 6px;
        font-size: 0.82rem;
        text-decoration: none !important;
        margin: 0.25rem 0 1rem 0;
    }

    .new-session-link:hover {
        background: #f8fafc !important;
    }

    .session-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 2rem;
        align-items: center;
        height: 2rem;
        border-radius: 6px;
        margin: 0.08rem 0;
        overflow: hidden;
        background: transparent;
    }

    .session-row:hover {
        background: #e9e9eb;
    }

    .session-row.active {
        background: var(--active);
    }

    .session-title-link {
        display: flex;
        align-items: center;
        height: 100%;
        min-width: 0;
        padding: 0 0.55rem;
        color: #24242a !important;
        text-decoration: none !important;
        font-size: 0.88rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .session-row.active .session-title-link {
        font-weight: 600;
    }

    .session-delete-link {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #71717a !important;
        text-decoration: none !important;
        font-size: 0.82rem;
    }

    .session-delete-link:hover {
        color: #111827 !important;
        background: #d4d4d8;
    }

    .chat-shell {
        max-width: 760px;
        margin: 0 auto;
    }

    .sidebar-resize-handle {
        position: fixed;
        left: calc(var(--sidebar-width) - 3px);
        top: 0;
        width: 6px;
        height: 100vh;
        cursor: col-resize;
        z-index: 9999;
        background: transparent;
    }

    .sidebar-resize-handle:hover {
        background: rgba(15, 55, 100, 0.12);
    }

    .empty-chat {
        color: var(--muted);
        padding-top: 24vh;
        text-align: center;
        font-size: 1rem;
    }

    .message-row {
        display: flex;
        margin: 1rem 0;
    }

    .message-row.user {
        justify-content: flex-start;
        padding-left: 1rem;
    }

    .message-row.assistant {
        justify-content: center;
    }

    .message-bubble {
        max-width: 560px;
        border-radius: 10px;
        padding: 0.85rem 1.05rem;
        line-height: 1.55;
        font-size: 0.92rem;
        color: #111827;
    }

    .message-bubble.user {
        background: #eef0f4;
        border: 1px solid #dfe3ea;
    }

    .message-bubble.assistant {
        background: #ffffff;
        border: 1px solid #d8dde6;
    }

    .panel-card {
        border: 1px solid #d9dde6;
        border-radius: 12px;
        padding: 0.95rem 1.05rem;
        margin-bottom: 1.1rem;
        background: #ffffff;
        box-shadow: none;
    }

    .panel-title {
        color: #71717a;
        font-size: 0.82rem;
        margin-bottom: 0.75rem;
    }

    .stat-row {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.34rem 0;
    }

    .stat-label {
        color: #52525b;
        font-size: 0.84rem;
    }

    .stat-value {
        font-size: 0.84rem;
        font-weight: 700;
        color: #18181b;
        text-align: right;
    }

    .mini-item {
        font-size: 0.82rem;
        color: #18181b;
        margin: 0.35rem 0 0.15rem 0;
    }

    .mini-caption {
        color: #71717a;
        font-size: 0.76rem;
        line-height: 1.35;
    }

    @media (max-width: 1100px) {
        div[data-testid="stChatInput"] {
            left: 14rem;
            right: 2rem;
        }

        div[data-testid="column"]:nth-of-type(4) {
            display: none;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

components.html(
    """
    <script>
    const doc = window.parent.document;
    const root = doc.documentElement;
    const key = "dsa-agent-sidebar-width";

    function topLevelColumns() {
        return [...doc.querySelectorAll('div[data-testid="column"]')]
            .filter((node) => node.closest('div[data-testid="stHorizontalBlock"]') === node.parentElement);
    }

    function setWidth(px) {
        const bounded = Math.max(190, Math.min(380, px));
        root.style.setProperty("--sidebar-width", bounded + "px");
        window.localStorage.setItem(key, String(bounded));
        const cols = topLevelColumns();
        if (cols[0]) {
            cols[0].style.flex = `0 0 ${bounded}px`;
            cols[0].style.width = `${bounded}px`;
        }
        if (handle) {
            handle.style.left = `${bounded - 3}px`;
        }
    }

    let handle = doc.getElementById("dsa-sidebar-resize-handle");
    if (!handle) {
        handle = doc.createElement("div");
        handle.id = "dsa-sidebar-resize-handle";
        handle.className = "sidebar-resize-handle";
        Object.assign(handle.style, {
            position: "fixed",
            top: "0",
            width: "8px",
            height: "100vh",
            cursor: "col-resize",
            zIndex: "999999",
            background: "transparent"
        });
        doc.body.appendChild(handle);
    }

    const saved = Number(window.localStorage.getItem(key));
    if (saved) setWidth(saved);
    else setWidth(288);

    let dragging = false;
    handle.onmousedown = (event) => {
        dragging = true;
        event.preventDefault();
    };
    doc.onmousemove = (event) => {
        if (!dragging) return;
        setWidth(event.clientX);
    };
    doc.onmouseup = () => {
        dragging = false;
    };
    </script>
    """,
    height=0,
    width=0,
)


def create_agent() -> DsaTutorGraph:
    model = st.session_state.get("model_name", "gemini-flash-latest").strip() or "gemini-flash-latest"
    llm_client = GeminiLlmClient.from_env(model=model)
    agent = DsaLearningAgent(enable_execution=True, llm_client=llm_client)
    return DsaTutorGraph(agent)


def create_session(title: str = "Phiên mới") -> ChatSession:
    try:
        graph = create_agent()
    except MissingApiKeyError:
        graph = None
    return ChatSession(id=str(uuid4()), title=title, messages=[], graph=graph)


def current_session() -> ChatSession:
    return st.session_state.chat_sessions[st.session_state.active_session_id]


def set_active_session(session_id: str) -> None:
    st.session_state.active_session_id = session_id


def new_session() -> None:
    session = create_session()
    st.session_state.chat_sessions[session.id] = session
    st.session_state.active_session_id = session.id


def delete_session(session_id: str) -> None:
    sessions = st.session_state.chat_sessions
    if session_id in sessions:
        del sessions[session_id]

    if not sessions:
        new_session()
        return

    if st.session_state.active_session_id == session_id:
        st.session_state.active_session_id = next(reversed(sessions))


def query_link(**params: str) -> str:
    return "?" + "&".join(f"{key}={quote(value)}" for key, value in params.items())


def clear_query_params() -> None:
    st.query_params.clear()


def handle_sidebar_actions() -> None:
    params = st.query_params
    new_chat = params.get("new_chat")
    active_session = params.get("active_session")
    delete_session_id = params.get("delete_session")

    if new_chat:
        new_session()
        clear_query_params()
        st.rerun()

    if active_session and active_session in st.session_state.chat_sessions:
        set_active_session(active_session)
        st.session_state.pending_delete_session_id = None
        clear_query_params()
        st.rerun()

    if delete_session_id and delete_session_id in st.session_state.chat_sessions:
        st.session_state.pending_delete_session_id = delete_session_id
        clear_query_params()
        st.rerun()


@st.dialog("Xoá phiên chat?")
def confirm_delete_session() -> None:
    session_id = st.session_state.pending_delete_session_id
    session = st.session_state.chat_sessions.get(session_id)

    if session is None:
        st.session_state.pending_delete_session_id = None
        st.rerun()

    st.write(f"Bạn có chắc muốn xoá phiên **{session.title}** không?")
    st.caption("Hành động này sẽ xoá nội dung chat và trạng thái học tập của phiên này.")

    if st.button("Xoá phiên", use_container_width=True, type="primary"):
        delete_session(session_id)
        st.session_state.pending_delete_session_id = None
        st.rerun()
    if st.button("Huỷ", use_container_width=True):
        st.session_state.pending_delete_session_id = None
        st.rerun()


def update_session_title(session: ChatSession) -> None:
    if session.title != "Phiên mới":
        return

    user_messages = [message["content"] for message in session.messages if message["role"] == "user"]
    if not user_messages:
        return

    if session.graph is None:
        words = " ".join(user_messages[0].split()[:5])
        session.title = words or "Phiên học DSA"
        return

    session.title = session.graph.agent.generate_session_title(user_messages[:2])


def render_message(role: str, content: str) -> None:
    safe = escape(content).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="message-row {role}">
            <div class="message-bubble {role}">{safe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def process_pending_turn(session: ChatSession) -> None:
    user_message = st.session_state.pending_user_message
    if not user_message or st.session_state.pending_response_session_id != session.id:
        return

    try:
        if session.graph is None:
            session.graph = create_agent()
        turn = session.graph.run(user_message)
        assistant_message = turn.response
        update_session_title(session)
    except MissingApiKeyError as exc:
        assistant_message = f"Thiếu Gemini API key: `{exc}`. Hãy cấu hình khóa LLM rồi tạo phiên mới."
    except TransientLlmError as exc:
        assistant_message = f"{exc}\n\nTin nhắn của bạn vẫn đã được lưu trong phiên chat. Bạn có thể bấm gửi lại sau khi Gemini hết quá tải."
    except Exception as exc:
        assistant_message = f"Hệ thống gặp lỗi khi xử lý lượt này: `{exc}`"
    finally:
        st.session_state.pending_response_session_id = None
        st.session_state.pending_user_message = None

    session.messages.append({"role": "assistant", "content": assistant_message})
    st.rerun()


if "model_name" not in st.session_state:
    st.session_state.model_name = "gemini-flash-latest"
if "chat_sessions" not in st.session_state:
    first_session = create_session()
    st.session_state.chat_sessions = {first_session.id: first_session}
    st.session_state.active_session_id = first_session.id
if "pending_delete_session_id" not in st.session_state:
    st.session_state.pending_delete_session_id = None
if "pending_response_session_id" not in st.session_state:
    st.session_state.pending_response_session_id = None
if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None

handle_sidebar_actions()

session_list_col, spacer_col, chat_col, detail_col = st.columns([0.18, 0.001, 0.54, 0.279], gap="small")

with session_list_col:
    st.markdown('<div class="sidebar-title">Đoạn chat</div>', unsafe_allow_html=True)

    st.markdown(
        f'<a class="new-session-link" href="{query_link(new_chat="1")}">+ Phiên mới</a>',
        unsafe_allow_html=True,
    )

    for session in list(st.session_state.chat_sessions.values()):
        active_class = " active" if session.id == st.session_state.active_session_id else ""
        st.markdown(
            f"""
            <div class="session-row{active_class}">
                <a class="session-title-link" href="{query_link(active_session=session.id)}">{escape(session.title)}</a>
                <a class="session-delete-link" href="{query_link(delete_session=session.id)}" title="Xoá phiên">🗑</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.pending_delete_session_id:
        confirm_delete_session()

with spacer_col:
    st.empty()

with chat_col:
    session = current_session()
    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
    st.markdown('<div class="app-title">DSA Socratic Agent</div>', unsafe_allow_html=True)

    if not session.messages:
        st.markdown(
            '<div class="empty-chat">Bắt đầu bằng cách gửi đề bài, ý tưởng, code hoặc yêu cầu gợi ý.</div>',
            unsafe_allow_html=True,
        )
    else:
        for message in session.messages:
            render_message(message["role"], message["content"])

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_response_session_id == session.id:
        with st.spinner("Agent đang suy nghĩ..."):
            process_pending_turn(session)

    if user_message := st.chat_input("Nhập đề bài, xin gợi ý, hoặc gửi code của bạn..."):
        session.messages.append({"role": "user", "content": user_message})
        st.session_state.pending_response_session_id = session.id
        st.session_state.pending_user_message = user_message
        st.rerun()

with detail_col:
    session = current_session()
    graph = session.graph

    if graph is None:
        st.markdown(
            """
            <div class="panel-card">
                <div class="panel-title">Environment</div>
                <div class="stat-row"><span class="stat-label">LLM</span><span class="stat-value">Missing key</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.warning("Hãy cấu hình khóa LLM rồi tạo phiên mới.")
    else:
        state = graph.agent.state

        st.markdown(
            f"""
            <div class="panel-card">
                <div class="panel-title">Environment</div>
                <div class="stat-row"><span class="stat-label">Hint level</span><span class="stat-value">{state.hint_level}</span></div>
                <div class="stat-row"><span class="stat-label">Problem type</span><span class="stat-value">{state.problem_type or "Chưa có"}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if state.generated_tests:
            st.markdown('<div class="panel-card"><div class="panel-title">Testcase gợi ý</div>', unsafe_allow_html=True)
            latest_suite = state.generated_tests[-1]
            for test in latest_suite.tests[:3]:
                st.markdown(
                    f'<div class="mini-item"><b>{escape(test.name)}</b> · {test.category.value} · {test.purpose.value}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="mini-caption">{escape(test.rationale)}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if state.latest_validation:
            st.markdown(
                f"""
                <div class="panel-card">
                    <div class="panel-title">Validation</div>
                    <div class="stat-row"><span class="stat-label">Status</span><span class="stat-value">{state.latest_validation.status.value}</span></div>
                    <div class="stat-row"><span class="stat-label">Passed</span><span class="stat-value">{state.latest_validation.passed_count}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if state.agent_trace:
            st.markdown('<div class="panel-card"><div class="panel-title">Agent Trace</div>', unsafe_allow_html=True)
            for item in state.agent_trace[-5:]:
                st.markdown(
                    f'<div class="mini-item"><b>{escape(item.node_name)}</b> · {escape(item.status)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="mini-caption">{escape(item.summary)}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
