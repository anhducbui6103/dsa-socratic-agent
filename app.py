from __future__ import annotations

from dataclasses import dataclass
import sys
from pathlib import Path
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
from dsa_agent.llm_client import GeminiLlmClient, MissingApiKeyError


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
        --sidebar-bg: #f4f4f5;
        --border-soft: rgba(120, 120, 120, 0.18);
        --border-mid: rgba(120, 120, 120, 0.22);
        --hover-bg: #e9e9eb;
        --active-bg: #dedee1;
        --text-main: #111827;
        --text-muted: #6b7280;
        --row-height: 2.7rem;
        --shadow-soft: 0 6px 18px rgba(0, 0, 0, 0.05);
    }

    .block-container {
        padding: 0.7rem 0 0 0 !important;
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

    div[data-testid="column"]:has(.sidebar-anchor) {
        flex: 0 0 var(--sidebar-width) !important;
        width: var(--sidebar-width) !important;
        min-width: var(--sidebar-width) !important;
        max-width: var(--sidebar-width) !important;
        background: var(--sidebar-bg);
        min-height: calc(100vh - 0.7rem);
        padding: 0.9rem 0.65rem 1rem 0.65rem;
        border-right: 1px solid rgba(120, 120, 120, 0.14);
    }

    div[data-testid="column"]:has(.separator-anchor) {
        flex: 0 0 0.75rem !important;
        width: 0.75rem !important;
        min-width: 0.75rem !important;
        max-width: 0.75rem !important;
        padding: 0 !important;
    }

    div[data-testid="column"]:has(.chat-anchor) {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        padding: 0.8rem 2rem 6.6rem 2rem;
        overflow: hidden;
    }

    div[data-testid="column"]:has(.detail-anchor) {
        flex: 0 0 27rem !important;
        width: 27rem !important;
        min-width: 27rem !important;
        max-width: 27rem !important;
        padding: 0.8rem 1rem 2rem 1.15rem;
        border-left: 1px solid rgba(120, 120, 120, 0.22);
        background: #fafafa;
        min-height: calc(100vh - 0.7rem);
        box-shadow: none;
        overflow-y: auto;
    }

    div[data-testid="column"]:has(.chat-anchor) div[data-testid="stChatMessage"] {
        max-width: 760px;
        margin-left: auto;
        margin-right: auto;
    }

    div[data-testid="stChatInput"] {
        position: fixed;
        left: calc(var(--sidebar-width) + 4rem);
        right: 29rem;
        bottom: 1rem;
        z-index: 100;
        background: transparent;
    }

    div[data-testid="stChatInput"] > div {
        border-radius: 12px;
    }

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

    .new-session-wrap div[data-testid="stButton"] > button:hover,
    .session-title-wrap div[data-testid="stButton"] > button:hover,
    .session-delete-wrap div[data-testid="stButton"] > button:hover {
        background: var(--hover-bg) !important;
        color: var(--text-main) !important;
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

    .session-delete-wrap div[data-testid="stButton"] > button:hover {
        color: #111827 !important;
    }

    .active-session-row + div .session-title-wrap div[data-testid="stButton"] > button,
    .active-session-row + div .session-delete-wrap div[data-testid="stButton"] > button {
        background: var(--active-bg) !important;
        font-weight: 600 !important;
    }

    .vertical-separator {
        border-left: 1px solid var(--border-mid);
        min-height: calc(100vh - 0.7rem);
        margin-left: 0.25rem;
    }

    .detail-top-spacer {
        height: 2.2rem;
    }

    .panel-card {
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-soft);
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

    .empty-chat {
        color: var(--text-muted);
        padding: 30vh 0 0 0;
        text-align: center;
    }

    @media (max-width: 900px) {
        div[data-testid="stChatInput"] {
            left: 1rem;
            right: 1rem;
        }

        div[data-testid="column"]:has(.detail-anchor) {
            display: none;
        }
    }

    /* Fallback nếu JS chưa kịp chạy */
    div[data-testid="stChatInput"] {
        left: 21.4rem !important;
        right: 30.3rem !important;
        max-width: calc(100vw - 52rem) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

components.html(
    """
    <script>
    const doc = window.parent.document;

    function topLevelColumns() {
        const blocks = [...doc.querySelectorAll('div[data-testid="stHorizontalBlock"]')];
        for (const block of blocks) {
            const cols = [...block.children].filter(
                node => node.getAttribute("data-testid") === "column"
            );
            if (cols.length >= 4) {
                const hasSidebar = cols[0].innerText.includes("Đoạn chat") || cols[0].innerText.includes("+ Phiên mới");
                const hasEnv = cols[3].innerText.includes("Environment") || cols[3].innerText.includes("Hint level");
                if (hasSidebar || hasEnv) return cols;
            }
        }
        return [];
    }

    function applyLayout() {
        const cols = topLevelColumns();
        if (cols.length < 4) return;

        const leftWidth = 288;
        const gapWidth = 12;
        const rightWidth = 448;

        Object.assign(cols[0].style, {
            flex: `0 0 ${leftWidth}px`,
            width: `${leftWidth}px`,
            minWidth: `${leftWidth}px`,
            maxWidth: `${leftWidth}px`,
            background: "#f4f4f5",
            borderRight: "1px solid rgba(120, 120, 120, 0.14)",
            minHeight: "calc(100vh - 12px)"
        });

        Object.assign(cols[1].style, {
            flex: `0 0 ${gapWidth}px`,
            width: `${gapWidth}px`,
            minWidth: `${gapWidth}px`,
            maxWidth: `${gapWidth}px`,
            padding: "0"
        });

        Object.assign(cols[2].style, {
            flex: "1 1 auto",
            minWidth: "0",
            overflow: "hidden"
        });

        Object.assign(cols[3].style, {
            flex: `0 0 ${rightWidth}px`,
            width: `${rightWidth}px`,
            minWidth: `${rightWidth}px`,
            maxWidth: `${rightWidth}px`,
            background: "#fafafa",
            borderLeft: "1px solid rgba(120, 120, 120, 0.22)",
            boxShadow: "none",
            minHeight: "calc(100vh - 12px)",
            overflowY: "auto"
        });

        const chatInput = doc.querySelector('div[data-testid="stChatInput"]');
        if (chatInput) {
            Object.assign(chatInput.style, {
                position: "fixed",
                left: `${leftWidth + gapWidth + 42}px`,
                right: `${rightWidth + 36}px`,
                bottom: "16px",
                zIndex: "100",
                background: "transparent"
            });
        }

        const messages = cols[2].querySelectorAll('div[data-testid="stChatMessage"]');
        messages.forEach((message) => {
            message.style.maxWidth = "760px";
            message.style.marginLeft = "auto";
            message.style.marginRight = "auto";
        });
    }

    applyLayout();
    setTimeout(applyLayout, 100);
    setTimeout(applyLayout, 500);
    setTimeout(applyLayout, 1000);

    const observer = new MutationObserver(() => applyLayout());
    observer.observe(doc.body, {childList: true, subtree: true});
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


def process_pending_turn(session: ChatSession) -> None:
    """Render user message first, then generate assistant response on the next rerun."""
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
        assistant_message = f"Thiếu Gemini API key: `{exc}`. Hãy paste key vào file `.env` rồi tạo phiên mới."
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


session_list_col, separator_col, chat_col, detail_col = st.columns([0.17, 0.015, 0.54, 0.275], gap="small")

with session_list_col:
    st.markdown('<div class="sidebar-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-list-title">Đoạn chat</div>', unsafe_allow_html=True)

    st.markdown('<div class="new-session-wrap">', unsafe_allow_html=True)
    if st.button("+ Phiên mới", use_container_width=True):
        new_session()
    st.markdown('</div>', unsafe_allow_html=True)

    for session in list(st.session_state.chat_sessions.values()):
        selected = session.id == st.session_state.active_session_id
        if selected:
            st.markdown('<span class="active-session-row"></span>', unsafe_allow_html=True)
        title_col, delete_col = st.columns([0.84, 0.16], gap="small")
        with title_col:
            st.markdown('<div class="session-title-wrap">', unsafe_allow_html=True)
            if st.button(session.title, key=f"session-{session.id}", use_container_width=True):
                set_active_session(session.id)
                st.session_state.pending_delete_session_id = None
            st.markdown('</div>', unsafe_allow_html=True)
        with delete_col:
            st.markdown('<div class="session-delete-wrap">', unsafe_allow_html=True)
            if st.button("🗑", key=f"ask-delete-{session.id}", use_container_width=True):
                st.session_state.pending_delete_session_id = session.id
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.pending_delete_session_id:
        confirm_delete_session()

with separator_col:
    st.markdown('<div class="separator-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div class="vertical-separator"></div>', unsafe_allow_html=True)

with chat_col:
    st.markdown('<div class="chat-anchor"></div>', unsafe_allow_html=True)
    session = current_session()

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

    if user_message := st.chat_input("Nhập đề bài, xin gợi ý, hoặc gửi code của bạn..."):
        session.messages.append({"role": "user", "content": user_message})
        update_session_title(session, user_message)
        st.session_state.pending_response_session_id = session.id
        st.session_state.pending_user_message = user_message
        st.rerun()

with detail_col:
    st.markdown('<div class="detail-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div class="detail-top-spacer"></div>', unsafe_allow_html=True)
    session = current_session()
    graph = session.graph

    if graph is None:
        st.markdown(
            """
            <div class="panel-card">
                <div class="panel-title">Environment</div>
                <div class="stat-row"><span class="stat-label">Gemini API</span><span class="stat-value">Missing key</span></div>
                <div class="stat-row"><span class="stat-label">Sandbox</span><span class="stat-value">On</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.warning("Paste `GEMINI_API_KEY` vào file `.env` rồi tạo phiên mới.")
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
            for test in latest_suite.tests:
                st.markdown(f"**{test.name}** · `{test.category.value}`")
                st.caption(test.rationale)
                st.code(test.input)
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
            if state.latest_validation.failed_tests:
                st.write("**Failed tests:**", [test.name for test in state.latest_validation.failed_tests])

        if state.pedagogy_flags:
            latest_review = state.pedagogy_flags[-1]
            st.markdown(
                f"""
                <div class="panel-card">
                    <div class="panel-title">Pedagogy review</div>
                    <div class="stat-row"><span class="stat-label">Risk</span><span class="stat-value">{latest_review.risk_level}</span></div>
                    <div class="stat-row"><span class="stat-label">Safe to send</span><span class="stat-value">{latest_review.safe_to_send}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if latest_review.issues:
                st.write("**Issues:**", latest_review.issues)
