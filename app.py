import os
import tempfile
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.sammarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

st.set_page_config(
    page_title="Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── Styling ─────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap');

:root {
    --ink: #14213d;
    --ink-soft: #4a5775;
    --paper: #f3f5f9;
    --card: #ffffff;
    --line: #dde3ee;
    --accent: #1f6feb;
    --accent-soft: #e6efff;
    --ok: #12805c;
}

html, body, [class*="css"], .stMarkdown, p, li, label {
    font-family: 'Manrope', sans-serif;
}
h1, h2, h3, h4 { font-family: 'Sora', sans-serif; color: var(--ink); letter-spacing: -0.01em; }

.stApp { background: var(--paper); }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1100px; }

/* Sidebar */
section[data-testid="stSidebar"] { background: var(--ink); }
section[data-testid="stSidebar"] * { color: #e8edf8; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff; }
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #1f3158 !important;
    color: #fff !important;
    border-color: #2f4577 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #1f3158;
    border: 1px dashed #4a6199;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
    color: var(--ink);
    background: #e8edf8;
}
section[data-testid="stSidebar"] .stButton > button {
    background: var(--accent);
    color: #fff;
    border: none;
    font-weight: 600;
    padding: 0.6rem 1rem;
}
section[data-testid="stSidebar"] .stButton > button:hover { background: #3b82f6; }

/* Title block */
.hero-title { font-family: 'Sora', sans-serif; font-size: 2rem; font-weight: 700; color: var(--ink); margin: 0; }
.hero-sub { color: var(--ink-soft); margin-top: .25rem; }

/* Metric tiles */
.tile {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 14px 16px;
}
.tile .n { font-family: 'Sora', sans-serif; font-size: 1.6rem; font-weight: 700; color: var(--ink); }
.tile .l { color: var(--ink-soft); font-size: .85rem; }

/* Content panels */
.panel {
    background: var(--card);
    border: 1px solid var(--line);
    border-left: 4px solid var(--accent);
    border-radius: 8px;
    padding: 18px 22px;
    line-height: 1.7;
    color: var(--ink);
}
.transcript {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 18px 22px;
    max-height: 520px;
    overflow-y: auto;
    line-height: 1.75;
    color: var(--ink);
    white-space: pre-wrap;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { font-weight: 600; color: var(--ink-soft); padding: 10px 16px; }
.stTabs [aria-selected="true"] { color: var(--accent); }

/* Empty state */
.empty {
    background: var(--card);
    border: 1px dashed #b9c4db;
    border-radius: 12px;
    padding: 48px 32px;
    text-align: center;
    color: var(--ink-soft);
}
.empty h3 { margin-bottom: .4rem; }

@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────── State ─────────────────────────
st.session_state.setdefault("result", None)
st.session_state.setdefault("chat", [])
st.session_state.setdefault("source_label", "")


# ───────────────────────── Helpers ─────────────────────────
def as_text(value) -> str:
    """Normalise model output (str or list) to markdown text."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(f"- {item}" for item in value)
    return str(value)


def count_items(value) -> int:
    """Rough count of list-like items in an output for the metric tiles."""
    if isinstance(value, (list, tuple)):
        return len(value)
    lines = [l for l in as_text(value).splitlines() if l.strip()]
    bullets = [l for l in lines if l.lstrip().startswith(("-", "*", "•")) or l.lstrip()[:2].rstrip(".").isdigit()]
    return len(bullets) or len(lines)


def build_report(result: dict) -> str:
    return (
        f"# {result['title']}\n\n"
        f"_Generated {datetime.now():%d %b %Y, %H:%M}_\n\n"
        f"## Summary\n{as_text(result['summary'])}\n\n"
        f"## Action items\n{as_text(result['action_items'])}\n\n"
        f"## Key decisions\n{as_text(result['key_decisions'])}\n\n"
        f"## Open questions\n{as_text(result['open_questions'])}\n\n"
        f"## Transcript\n{result['transcript']}\n"
    )


def run_with_progress(source: str, language: str) -> dict:
    """Same steps as main.run_pipeline, with live progress in the UI."""
    with st.status("Processing your recording…", expanded=True) as status:
        st.write("Preparing audio")
        chunks = process_input(source)

        st.write("Transcribing speech")
        transcript = transcribe_all(chunks, language)

        st.write("Writing title and summary")
        title = generate_title(transcript)
        summary = summarize(transcript)

        st.write("Finding action items, decisions and open questions")
        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        st.write("Indexing the transcript for chat")
        rag_chain = build_rag_chain(transcript)

        status.update(label="Done. Your recording is ready.", state="complete", expanded=False)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.markdown("### Meeting Assistant")
    st.caption("Turn a recording into notes you can search and question.")
    st.divider()

    input_mode = st.radio("Source", ["YouTube link", "Upload a file"], horizontal=True)

    youtube_url = ""
    uploaded = None
    if input_mode == "YouTube link":
        youtube_url = st.text_input("Video URL", placeholder="https://www.youtube.com/watch?v=…")
    else:
        uploaded = st.file_uploader(
            "Audio or video file",
            type=["mp3", "wav", "m4a", "mp4", "mkv", "mov", "webm"],
        )

    language = st.selectbox("Spoken language", ["english", "hinglish"])

    ready = bool(youtube_url.strip()) if input_mode == "YouTube link" else uploaded is not None
    start = st.button("Analyze recording", use_container_width=True, disabled=not ready)

    if st.session_state.result:
        st.divider()
        if st.button("Start over", use_container_width=True):
            st.session_state.result = None
            st.session_state.chat = []
            st.session_state.source_label = ""
            st.rerun()

# ───────────────────────── Run pipeline ─────────────────────────
if start:
    st.session_state.chat = []
    tmp_path = None
    try:
        if input_mode == "Upload a file":
            suffix = os.path.splitext(uploaded.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getbuffer())
                tmp_path = tmp.name
            source = tmp_path
            st.session_state.source_label = uploaded.name
        else:
            source = youtube_url.strip()
            st.session_state.source_label = source

        st.session_state.result = run_with_progress(source, language)
    except Exception as e:
        st.session_state.result = None
        st.error(f"Could not process this recording. {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# ───────────────────────── Main area ─────────────────────────
result = st.session_state.result

if not result:
    st.markdown('<p class="hero-title">Meeting Assistant</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">Add a YouTube link or upload a recording to get a summary, action items and a chat that answers from the transcript.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="empty">
  <h3>No recording yet</h3>
  <p>Choose a source in the sidebar, then select <b>Analyze recording</b>.<br>
  Long recordings can take a few minutes to transcribe.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()

# Header
st.markdown(f'<p class="hero-title">{result["title"]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="hero-sub">{st.session_state.source_label}</p>', unsafe_allow_html=True)
st.write("")

# Metric tiles
word_count = len(result["transcript"].split())
tiles = [
    (f"{word_count:,}", "Words transcribed"),
    (str(count_items(result["action_items"])), "Action items"),
    (str(count_items(result["key_decisions"])), "Key decisions"),
    (str(count_items(result["open_questions"])), "Open questions"),
]
for col, (n, label) in zip(st.columns(4), tiles):
    col.markdown(f'<div class="tile"><div class="n">{n}</div><div class="l">{label}</div></div>', unsafe_allow_html=True)

st.write("")

# Tabs
tab_summary, tab_actions, tab_decisions, tab_questions, tab_transcript, tab_chat = st.tabs(
    ["Summary", "Action items", "Key decisions", "Open questions", "Transcript", "Ask the recording"]
)

with tab_summary:
    st.markdown(f'<div class="panel">{as_text(result["summary"])}</div>', unsafe_allow_html=True)

with tab_actions:
    text = as_text(result["action_items"])
    if text.strip():
        with st.container(border=True):
            st.markdown(text)
    else:
        st.info("No action items were found in this recording.")

with tab_decisions:
    text = as_text(result["key_decisions"])
    if text.strip():
        with st.container(border=True):
            st.markdown(text)
    else:
        st.info("No decisions were found in this recording.")

with tab_questions:
    text = as_text(result["open_questions"])
    if text.strip():
        with st.container(border=True):
            st.markdown(text)
    else:
        st.info("No open questions were found in this recording.")

with tab_transcript:
    st.markdown(f'<div class="transcript">{result["transcript"]}</div>', unsafe_allow_html=True)
    st.write("")
    c1, c2, _ = st.columns([1, 1, 3])
    c1.download_button(
        "Download transcript",
        result["transcript"],
        file_name="transcript.txt",
        mime="text/plain",
        use_container_width=True,
    )
    c2.download_button(
        "Download full report",
        build_report(result),
        file_name="meeting_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

with tab_chat:
    st.caption("Answers come from this recording's transcript only.")

    suggestions = [
        "What were the main topics?",
        "Who owns which task?",
        "What was decided?",
    ]
    if not st.session_state.chat:
        for col, s in zip(st.columns(len(suggestions)), suggestions):
            if col.button(s, use_container_width=True, key=f"sugg_{s}"):
                st.session_state.pending_question = s
                st.rerun()

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask something about the recording")
    question = question or st.session_state.pop("pending_question", None)

    if question:
        st.session_state.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching the transcript…"):
                try:
                    answer = ask_question(result["rag_chain"], question)
                except Exception as e:
                    answer = f"I couldn't get an answer. {e}"
            st.markdown(answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})

    if st.session_state.chat:
        if st.button("Clear chat"):
            st.session_state.chat = []
            st.rerun()