"""
Streamlit application entry point.
Run with:  streamlit run app.py
"""

import streamlit as st
from chat_service import get_client, get_interview_response, get_response_with_prompt, validate_job_description, check_prompt_injection
from prompts import PROMPTS
from scraper import scrape_job_url


# ── Page configuration ────────────────────────
st.set_page_config(
    page_title="Senior .NET Interview",
    page_icon="💼",
    layout="wide",
)

# ── Shared client ─────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = get_client()

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.header("Navigation")
    page = st.radio("", ["🎙️ Interview", "🔬 Prompt Lab"], label_visibility="collapsed")
    st.divider()
    st.header("Model Settings")
    AVAILABLE_MODELS = {
        "openai/gpt-5-mini": "GPT-5 Mini (recommended)",
        "openai/gpt-5-nano": "GPT-5 Nano (cheaper)",
        "openai/gpt-5": "GPT-5 (higher-capability)",
    }
    selected_model = st.selectbox(
        "🤖 Model",
        options=list(AVAILABLE_MODELS.keys()),
        index=0,
        format_func=lambda x: AVAILABLE_MODELS[x],
        help="Choose the AI model. Mini is the best balance of quality and cost.",
    )
    st.session_state.model = selected_model
    temperature = st.selectbox(
        "🌡️ Temperature",
        options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        index=7,
        format_func=lambda x: f"{x:.1f}" + (" (precise)" if x == 0.0 else " (creative)" if x == 1.0 else " (balanced)" if x == 0.5 else ""),
        help="Lower = more focused and deterministic. Higher = more creative and varied.",
    )
    st.session_state.temperature = temperature
    st.divider()

# ══════════════════════════════════════════════
#  PAGE 1 — Interview Chat
# ══════════════════════════════════════════════
if page == "🎙️ Interview":
    st.title("Interview Prep — Senior .NET Developer")
    st.caption("Practice with an AI-powered technical interviewer")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "interview_validated" not in st.session_state:
        st.session_state.interview_validated = False

    # ── Job description intake (before interview starts) ──
    if not st.session_state.interview_validated:
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
                with st.spinner("🔍 Checking for prompt injection..."):
                    injection = check_prompt_injection(st.session_state.client, iv_job_text.strip())

                if injection.get("injection_detected"):
                    st.error(f"🛑 **Prompt injection detected.** {injection.get('reason', 'Your input appears to contain instructions that try to manipulate the AI.')} Please provide a legitimate job description.")
                else:
                    with st.spinner("🔍 Validating job description..."):
                        validation = validate_job_description(st.session_state.client, iv_job_text.strip())

                    if not validation.get("valid"):
                        st.error(f"🚫 **Invalid input.** {validation.get('reason', 'The text does not appear to be a legitimate job description.')}")
                    elif not validation.get("dotnet_related"):
                        st.warning(f"⚠️ **Not .NET-related.** {validation.get('reason', 'This job description does not seem to involve .NET technologies.')} Please provide a .NET developer job description.")
                    else:
                        st.session_state.interview_validated = True
                        st.session_state.interview_job_desc = iv_job_text.strip()
                        st.session_state.messages = []
                        st.rerun()

    # ── Interview chat (after validation) ─────
    if st.session_state.interview_validated:
        # Auto-start with job description context
        if not st.session_state.messages:
            job_context = st.session_state.get("interview_job_desc", "")
            initial_user_msg = f"Here is the job description I want to prepare for:\n\n{job_context}\n\nBased on this job description, start the interview with the most relevant question."
            with st.spinner("Preparing the interview..."):
                first_message = get_interview_response(
                    st.session_state.client,
                    [{"role": "user", "content": initial_user_msg}],
                    temperature=st.session_state.temperature,
                    model=st.session_state.model,
                )
            st.session_state.messages.append({"role": "assistant", "content": first_message})

        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # User input
        if user_input := st.chat_input("Type your answer here..."):
            # Check for prompt injection before processing
            injection = check_prompt_injection(st.session_state.client, user_input)
            if injection.get("injection_detected"):
                st.error(f"🛑 **Prompt injection detected.** {injection.get('reason', 'Your message appears to contain instructions that try to manipulate the AI.')} Please rephrase your answer.")
            else:
                st.session_state.messages.append({"role": "user", "content": user_input})

                with st.chat_message("user"):
                    st.markdown(user_input)

                with st.chat_message("assistant"):
                    with st.spinner("Evaluating your answer..."):
                        reply = get_interview_response(
                            st.session_state.client,
                            st.session_state.messages,
                            temperature=st.session_state.temperature,
                            model=st.session_state.model,
                        )
                    st.markdown(reply)

                st.session_state.messages.append({"role": "assistant", "content": reply})

    # Sidebar controls for interview
    with st.sidebar:
        if st.button("🔄 Restart interview"):
            st.session_state.messages = []
            st.session_state.interview_validated = False
            st.session_state.pop("interview_job_desc", None)
            st.rerun()

# ══════════════════════════════════════════════
#  PAGE 2 — Prompt Technique Comparison Lab
# ══════════════════════════════════════════════
elif page == "🔬 Prompt Lab":
    st.title("🔬 Prompt Technique Comparison Lab")
    st.caption(
        "Paste a job description URL or the full text — the AI will validate it's .NET-related, then run all prompting techniques"
    )

    # Friendly labels and icons for each technique
    TECHNIQUE_META = {
        "zero_shot":            ("Zero-Shot",            "⚡"),
        "few_shot":             ("Few-Shot Learning",    "📝"),
        "chain_of_thought":     ("Chain-of-Thought",     "🔗"),
        "self_consistency":     ("Self-Consistency",     "🎯"),
        "generated_knowledge":  ("Generated Knowledge",  "🧠"),
    }

    # ── Input area ────────────────────────────
    input_mode = st.radio(
        "Input method",
        ["📋 Paste job description text", "🔗 Enter a URL"],
        horizontal=True,
    )

    job_text = ""

    if input_mode == "🔗 Enter a URL":
        url_input = st.text_input(
            "Job posting URL",
            placeholder="https://www.linkedin.com/jobs/view/...",
        )
        if url_input:
            with st.spinner("🌐 Fetching job posting..."):
                result = scrape_job_url(url_input)
            if result["success"]:
                job_text = result["text"]
                with st.expander(f"📄 Extracted text via {result['method']} (preview)", expanded=False):
                    st.text(job_text[:2000] + ("..." if len(job_text) > 2000 else ""))
            else:
                st.error(f"Could not fetch the URL: {result['error']}")
    else:
        job_text = st.text_area(
            "Paste the full job description",
            placeholder="Senior .NET Developer – We are looking for an experienced developer with expertise in C#, ASP.NET Core...",
            height=200,
            label_visibility="collapsed",
        )

    run_comparison = st.button("🚀 Validate & Run all techniques", type="primary", use_container_width=True)

    # ── Validate and run ──────────────────────
    if run_comparison and job_text.strip():
        # Reset previous results
        st.session_state.lab_results = {}
        st.session_state.lab_input = ""
        st.session_state.pop("lab_validation", None)

        with st.spinner("🔍 Checking for prompt injection..."):
            injection = check_prompt_injection(st.session_state.client, job_text.strip())

        if injection.get("injection_detected"):
            st.error(f"🛑 **Prompt injection detected.** {injection.get('reason', 'Your input appears to contain instructions that try to manipulate the AI.')} Please provide a legitimate job description.")
        else:
            with st.spinner("🔍 Validating job description..."):
                validation = validate_job_description(st.session_state.client, job_text.strip())
                st.session_state.lab_validation = validation

            if not validation.get("valid"):
                st.error(f"🚫 **Invalid input.** {validation.get('reason', 'The text does not appear to be a legitimate job description.')}")
            elif not validation.get("dotnet_related"):
                st.warning(f"⚠️ **Not .NET-related.** {validation.get('reason', 'This job description does not seem to involve .NET technologies.')} Please provide a .NET developer job description.")
            else:
                st.success(f"✅ **Valid .NET job description.** {validation.get('reason', '')}")
                st.session_state.lab_input = job_text.strip()

                progress = st.progress(0, text="Running techniques...")
                total = len(PROMPTS)

                user_message = f"Here is the job description I want to prepare for:\n\n{job_text.strip()}\n\nBased on this job description, start the interview with the most relevant question."

                for i, (key, prompt_text) in enumerate(PROMPTS.items()):
                    label, icon = TECHNIQUE_META.get(key, (key, "🔹"))
                    progress.progress((i) / total, text=f"Running {label}...")
                    try:
                        result = get_response_with_prompt(
                            st.session_state.client,
                            prompt_text,
                            user_message,
                            temperature=st.session_state.temperature,
                            model=st.session_state.model,
                        )
                        st.session_state.lab_results[key] = result
                    except Exception as e:
                        st.session_state.lab_results[key] = f"⚠️ Error: {e}"

                progress.progress(1.0, text="Done!")

    # ── Display results ───────────────────────
    if st.session_state.get("lab_results"):
        st.divider()
        st.markdown("### Results by Technique")

        for key, response_text in st.session_state.lab_results.items():
            label, icon = TECHNIQUE_META.get(key, (key, "🔹"))
            with st.expander(f"{icon} {label}", expanded=False):
                st.markdown(response_text)

    elif run_comparison and not job_text.strip():
        st.warning("Please enter a job description or URL before running.")
