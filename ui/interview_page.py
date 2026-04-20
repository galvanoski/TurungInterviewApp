"""
Interview page UI.
Handles job description intake, validation, vector DB resume, and chat loop.
"""

import streamlit as st

from core.security import check_prompt_injection
from core.prompts import TOOL_DISPLAY_NAMES
from services.interview import get_interview_response, get_agent_interview_response
from services.validation import validate_job_description
from data.scraper import scrape_job_url
from data.vector_store import search_similar_session, save_session


def render():
    """Render the Interview page."""
    st.title("Interview Prep — Senior .NET Developer")
    st.caption("Practice with an AI-powered technical interviewer")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "interview_validated" not in st.session_state:
        st.session_state.interview_validated = False

    # ── Sidebar controls (must run first so agent_mode is current) ──
    _render_sidebar_controls()

    # ── Job description intake ────────────────
    if not st.session_state.interview_validated:
        _render_job_input()

    # ── Interview chat ────────────────────────
    if st.session_state.interview_validated:
        _render_chat()


# ──────────────────────────────────────────────
#  PRIVATE HELPERS
# ──────────────────────────────────────────────

def _render_job_input():
    """Render the job description intake form."""
    st.info("📋 To begin, provide the job description you want to prepare for.")

    iv_mode = st.radio(
        "Input method",
        ["📋 Paste job description text", "🔗 Enter a URL"],
        horizontal=True,
        key="iv_mode",
    )

    iv_job_text = ""

    if iv_mode == "🔗 Enter a URL":
        iv_url = st.text_input("Job posting URL", placeholder="https://www.linkedin.com/jobs/view/...", key="iv_url")
        if iv_url:
            with st.spinner("🌐 Fetching job posting..."):
                result = scrape_job_url(iv_url)
            if result["success"]:
                iv_job_text = result["text"]
                with st.expander(f"📄 Extracted text via {result['method']} (preview)", expanded=False):
                    st.text(iv_job_text[:2000] + ("..." if len(iv_job_text) > 2000 else ""))
            else:
                st.error(f"Could not fetch the URL: {result['error']}")
    else:
        iv_job_text = st.text_area(
            "Paste the full job description",
            placeholder="Senior .NET Developer – We are looking for an experienced developer with expertise in C#, ASP.NET Core...",
            height=200,
            key="iv_job_text",
            label_visibility="collapsed",
        )

    if st.button("✅ Validate & Start Interview", type="primary", use_container_width=True):
        if not iv_job_text.strip():
            st.warning("Please enter a job description or URL first.")
        else:
            _validate_and_start(iv_job_text.strip())

    # Similar session found — ask user
    if st.session_state.get("pending_similar"):
        _render_resume_prompt()


def _validate_and_start(job_text: str):
    """Run injection check, validation, and vector DB search."""
    with st.spinner("🔍 Checking for prompt injection..."):
        injection = check_prompt_injection(job_text)

    if injection.get("injection_detected"):
        st.error(f"🛑 **Prompt injection detected.** {injection.get('reason', '')} Please provide a legitimate job description.")
        return

    with st.spinner("🔍 Validating job description..."):
        validation = validate_job_description(job_text)

    if not validation.get("valid"):
        st.error(f"🚫 **Invalid input.** {validation.get('reason', 'The text does not appear to be a legitimate job description.')}")
        return
    if not validation.get("dotnet_related"):
        st.warning(f"⚠️ **Not .NET-related.** {validation.get('reason', '')} Please provide a .NET developer job description.")
        return

    similar = search_similar_session(job_text)
    if similar:
        st.session_state.pending_similar = similar
        st.session_state.pending_job_desc = job_text
        st.rerun()
    else:
        st.session_state.interview_validated = True
        st.session_state.interview_job_desc = job_text
        st.session_state.messages = []
        st.rerun()


def _render_resume_prompt():
    """Show the resume/new-interview buttons when a similar session is found."""
    similar = st.session_state.pending_similar
    st.divider()
    st.warning(
        f"📂 **A previous interview session was found** with a similar job description "
        f"({len(similar['messages'])} messages, similarity: {1 - similar['distance']:.0%}).\n\n"
        f"**Previous job description (preview):**\n"
        f"> {similar['job_desc'][:300]}{'...' if len(similar['job_desc']) > 300 else ''}"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Continue previous interview", type="primary", use_container_width=True):
            st.session_state.interview_validated = True
            st.session_state.interview_job_desc = similar["job_desc"]
            st.session_state.messages = similar["messages"]
            st.session_state.pop("pending_similar", None)
            st.session_state.pop("pending_job_desc", None)
            st.rerun()
    with col2:
        if st.button("🆕 Start a new interview", use_container_width=True):
            st.session_state.interview_validated = True
            st.session_state.interview_job_desc = st.session_state.pending_job_desc
            st.session_state.messages = []
            st.session_state.pop("pending_similar", None)
            st.session_state.pop("pending_job_desc", None)
            st.rerun()


def _render_chat():
    """Render the interview chat interface."""
    is_agent = st.session_state.get("agent_mode", False)

    if is_agent:
        st.success(
            "🤖 **Agent Mode is ON** — The interviewer can now:\n"
            "- 🔍 Search the web for up-to-date .NET documentation and best practices\n"
            "- 📄 Read specific documentation pages (e.g. Microsoft Learn)\n"
            "- 🔬 Perform in-depth code review when you paste C# code\n\n"
            "💡 **Tip:** Try pasting a C# code snippet in your answer to get detailed feedback!"
        )

    # Auto-start with job description context
    if not st.session_state.messages:
        _generate_first_message(is_agent)

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tools_used"):
                friendly = [TOOL_DISPLAY_NAMES.get(t, t) for t in set(msg["tools_used"])]
                st.caption(f"Tools used: {', '.join(friendly)}")

    # User input
    placeholder = "Type your answer here (paste C# code for agent review)..." if is_agent else "Type your answer here..."
    if user_input := st.chat_input(placeholder):
        _handle_user_input(user_input, is_agent)


def _generate_first_message(is_agent: bool):
    """Generate the first interviewer message based on the job description."""
    job_context = st.session_state.get("interview_job_desc", "")
    initial_msg = (
        f"Here is the job description I want to prepare for:\n\n{job_context}\n\n"
        f"Based on this job description, start the interview with the most relevant question."
    )
    spinner_text = "🤖 Agent is preparing the interview..." if is_agent else "Preparing the interview..."
    with st.spinner(spinner_text):
        if is_agent:
            first_message, tools_used = get_agent_interview_response(
                [{"role": "user", "content": initial_msg}],
                temperature=st.session_state.temperature,
                model=st.session_state.model,
            )
        else:
            first_message = get_interview_response(
                [{"role": "user", "content": initial_msg}],
                temperature=st.session_state.temperature,
                model=st.session_state.model,
            )
            tools_used = []
    st.session_state.messages.append({"role": "assistant", "content": first_message, "tools_used": tools_used})
    save_session(st.session_state.interview_job_desc, st.session_state.messages)
    st.rerun()


def _handle_user_input(user_input: str, is_agent: bool):
    """Process user input: injection check, then generate response."""
    injection = check_prompt_injection(user_input)
    if injection.get("injection_detected"):
        st.error(f"🛑 **Prompt injection detected.** {injection.get('reason', '')} Please rephrase your answer.")
        return

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        spinner_text = "🤖 Agent is evaluating..." if is_agent else "Evaluating your answer..."
        with st.spinner(spinner_text):
            if is_agent:
                reply, tools_used = get_agent_interview_response(
                    st.session_state.messages,
                    temperature=st.session_state.temperature,
                    model=st.session_state.model,
                )
            else:
                reply = get_interview_response(
                    st.session_state.messages,
                    temperature=st.session_state.temperature,
                    model=st.session_state.model,
                )
                tools_used = []
        st.markdown(reply)
        if tools_used:
            friendly = [TOOL_DISPLAY_NAMES.get(t, t) for t in set(tools_used)]
            st.caption(f"Tools used: {', '.join(friendly)}")

    st.session_state.messages.append({"role": "assistant", "content": reply, "tools_used": tools_used})
    save_session(st.session_state.interview_job_desc, st.session_state.messages)
    st.rerun()


def _render_sidebar_controls():
    """Render interview-specific sidebar controls (agent mode + restart)."""
    with st.sidebar:
        agent_mode = st.checkbox(
            "🤖 Agent Mode",
            value=False,
            help="Enable AI agent with tools: web search for .NET docs, code review, and documentation lookup.",
        )
        st.session_state.agent_mode = agent_mode
        if agent_mode:
            st.info(
                "**Agent tools active:**\n"
                "- 🔍 **Web Search** — searches .NET docs live\n"
                "- 📄 **Fetch Docs** — reads specific URLs\n"
                "- 🔬 **Code Review** — analyzes your C# code"
            )
        if st.button("🔄 Restart interview"):
            if st.session_state.get("interview_job_desc") and st.session_state.get("messages"):
                save_session(st.session_state.interview_job_desc, st.session_state.messages)
            st.session_state.messages = []
            st.session_state.interview_validated = False
            st.session_state.pop("interview_job_desc", None)
            st.session_state.pop("pending_similar", None)
            st.session_state.pop("pending_job_desc", None)
            st.rerun()
