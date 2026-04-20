"""
Prompt Lab page UI.
Runs all prompting techniques against one job description and compares results.
"""

import streamlit as st

from core.security import check_prompt_injection
from core.prompts import PROMPTS, TECHNIQUE_META
from services.validation import validate_job_description
from services.prompt_lab import get_response_with_prompt
from data.scraper import scrape_job_url


def render():
    """Render the Prompt Lab page."""
    st.title("🔬 Prompt Technique Comparison Lab")
    st.caption(
        "Paste a job description URL or the full text — the AI will validate it's .NET-related, then run all prompting techniques"
    )

    job_text = _render_input()
    run_comparison = st.button("🚀 Validate & Run all techniques", type="primary", use_container_width=True)

    if run_comparison and job_text.strip():
        _run_comparison(job_text.strip())
    elif run_comparison and not job_text.strip():
        st.warning("Please enter a job description or URL before running.")

    _render_results()


# ──────────────────────────────────────────────
#  PRIVATE HELPERS
# ──────────────────────────────────────────────

def _render_input() -> str:
    """Render the input area and return the job text."""
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

    return job_text


def _run_comparison(job_text: str):
    """Validate and run all prompt techniques."""
    st.session_state.lab_results = {}
    st.session_state.lab_input = ""
    st.session_state.pop("lab_validation", None)

    with st.spinner("🔍 Checking for prompt injection..."):
        injection = check_prompt_injection(job_text)

    if injection.get("injection_detected"):
        st.error(f"🛑 **Prompt injection detected.** {injection.get('reason', '')} Please provide a legitimate job description.")
        return

    with st.spinner("🔍 Validating job description..."):
        validation = validate_job_description(job_text)
        st.session_state.lab_validation = validation

    if not validation.get("valid"):
        st.error(f"🚫 **Invalid input.** {validation.get('reason', 'The text does not appear to be a legitimate job description.')}")
        return
    if not validation.get("dotnet_related"):
        st.warning(f"⚠️ **Not .NET-related.** {validation.get('reason', '')} Please provide a .NET developer job description.")
        return

    st.success(f"✅ **Valid .NET job description.** {validation.get('reason', '')}")
    st.session_state.lab_input = job_text

    progress = st.progress(0, text="Running techniques...")
    total = len(PROMPTS)

    user_message = (
        f"Here is the job description I want to prepare for:\n\n{job_text}\n\n"
        f"Based on this job description, start the interview with the most relevant question."
    )

    for i, (key, prompt_text) in enumerate(PROMPTS.items()):
        label, icon = TECHNIQUE_META.get(key, (key, "🔹"))
        progress.progress(i / total, text=f"Running {label}...")
        try:
            result = get_response_with_prompt(
                prompt_text,
                user_message,
                temperature=st.session_state.temperature,
                model=st.session_state.model,
            )
            st.session_state.lab_results[key] = result
        except Exception as e:
            st.session_state.lab_results[key] = f"⚠️ Error: {e}"

    progress.progress(1.0, text="Done!")


def _render_results():
    """Display results from the last comparison run."""
    if st.session_state.get("lab_results"):
        st.divider()
        st.markdown("### Results by Technique")

        for key, response_text in st.session_state.lab_results.items():
            label, icon = TECHNIQUE_META.get(key, (key, "🔹"))
            with st.expander(f"{icon} {label}", expanded=False):
                st.markdown(response_text)
