# Technical Documentation — Senior .NET Interview Preparation App

> Last updated: July 2025

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Module Reference](#3-module-reference)
   - [3.1 Entry Point (app.py)](#31-entry-point)
   - [3.2 Configuration (config.py)](#32-configuration)
   - [3.3 Core Layer](#33-core-layer)
   - [3.4 Data Layer](#34-data-layer)
   - [3.5 Services Layer](#35-services-layer)
   - [3.6 Tools Layer](#36-tools-layer)
   - [3.7 UI Layer](#37-ui-layer)
4. [Prompt Engineering](#4-prompt-engineering)
5. [Security Architecture](#5-security-architecture)
6. [Agent System (LangGraph)](#6-agent-system-langgraph)
7. [Vector Database (ChromaDB)](#7-vector-database-chromadb)
8. [Web Scraping Pipeline](#8-web-scraping-pipeline)
9. [Pricing System](#9-pricing-system)
10. [Data Flow Diagrams](#10-data-flow-diagrams)
11. [API Dependencies](#11-api-dependencies)
12. [Configuration Reference](#12-configuration-reference)
13. [Error Handling](#13-error-handling)

---

## 1. System Overview

The application is an AI-powered interview preparation tool specializing in Senior .NET Developer positions. It uses Large Language Models (LLMs) via the OpenRouter API to simulate realistic technical interviews, analyze job descriptions, and provide feedback on code.

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Python files | 22 |
| Total lines of code | ~1,550 |
| Architecture layers | 5 (UI, Services, Core, Tools, Data) |
| Prompting techniques | 5 |
| Agent tools | 3 |
| Supported models | 3 |

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Web Framework | Streamlit | latest |
| LLM Framework | LangChain + LangChain-OpenAI | latest |
| Agent Framework | LangGraph | latest |
| Vector Database | ChromaDB | 1.5.8+ |
| Web Scraping | CloudScraper, BeautifulSoup4, Jina Reader | latest |
| LLM Provider | OpenRouter API | v1 |
| Environment | python-dotenv | latest |

---

## 2. Architecture

### Layered Architecture

The system follows a strict layered architecture. Each layer depends only on the layers below it.

```
┌─────────────────────────────────────────────────────────────┐
│                     UI LAYER (ui/)                          │
│  sidebar.py │ interview_page.py │ prompt_lab_page.py        │
└───────────────────────┬─────────────────────────────────────┘
                        │ calls
┌───────────────────────▼─────────────────────────────────────┐
│                  SERVICES LAYER (services/)                  │
│  interview.py │ prompt_lab.py │ validation.py │ pricing.py   │
└───────────────────────┬─────────────────────────────────────┘
                        │ uses
┌───────────────────────▼─────────────────────────────────────┐
│          CORE LAYER (core/)  │  TOOLS LAYER (tools/)        │
│  llm.py │ prompts.py │       │  search.py │ docs.py │       │
│  security.py                 │  code_review.py              │
└───────────────────────┬─────────────────────────────────────┘
                        │ persists/fetches
┌───────────────────────▼─────────────────────────────────────┐
│                    DATA LAYER (data/)                        │
│            scraper.py │ vector_store.py                      │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   EXTERNAL SERVICES                          │
│  OpenRouter API │ Jina Reader/Search API │ ChromaDB (local)  │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Graph

```
app.py
├── ui/sidebar.py
│   └── core/prompts.py (AVAILABLE_MODELS)
├── ui/interview_page.py
│   ├── core/security.py
│   │   ├── core/llm.py → OpenRouter API
│   │   └── core/prompts.py (INJECTION_DETECTION_PROMPT)
│   ├── services/interview.py
│   │   ├── core/llm.py
│   │   ├── core/prompts.py (SYSTEM_PROMPT, AGENT_SYSTEM_PROMPT)
│   │   └── tools/* (search, docs, code_review)
│   ├── services/validation.py
│   │   ├── core/llm.py
│   │   └── core/prompts.py (VALIDATION_PROMPT)
│   ├── services/pricing.py → OpenRouter Models API
│   ├── data/scraper.py → Jina Reader API, target URLs
│   └── data/vector_store.py → ChromaDB (local disk)
└── ui/prompt_lab_page.py
    ├── core/security.py
    ├── services/prompt_lab.py
    │   ├── core/llm.py
    │   └── core/prompts.py (PROMPTS dict)
    ├── services/validation.py
    ├── services/pricing.py
    └── data/scraper.py
```

---

## 3. Module Reference

### 3.1 Entry Point

#### `app.py`

The Streamlit entry point. Configures the page (title, icon, wide layout) and routes to one of two pages based on sidebar selection.

```python
st.set_page_config(page_title="Senior .NET Interview", page_icon="💼", layout="wide")
page = render_sidebar()  # Returns "🎙️ Interview" or "🔬 Prompt Lab"
```

### 3.2 Configuration

#### `config.py`

Loads environment variables from `.env` via `python-dotenv`:

| Variable | Purpose | Example |
|----------|---------|---------|
| `OPENAI_API_KEY` | OpenRouter API key | `sk-or-v1-...` |
| `OPENAI_MODEL` | Default model ID | `openai/gpt-5-mini` |

---

### 3.3 Core Layer

#### `core/llm.py` — LLM Factory

**Function:** `get_llm(**params) → ChatOpenAI`

Creates `ChatOpenAI` instances configured to point at OpenRouter's API base URL (`https://openrouter.ai/api/v1`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | `float` | `0.7` | Response randomness |
| `model` | `str \| None` | `OPENAI_MODEL` | Model identifier |
| `top_p` | `float \| None` | `None` | Nucleus sampling |
| `frequency_penalty` | `float \| None` | `None` | Reduce repetition |
| `presence_penalty` | `float \| None` | `None` | Encourage new topics |
| `max_tokens` | `int \| None` | `None` | Output length limit |
| `top_k` | `int \| None` | `None` | Top-K sampling (via `extra_body`) |

**Implementation detail:** `top_k` is not a standard OpenAI parameter. It is passed to OpenRouter via `model_kwargs.extra_body`, which OpenRouter forwards to the underlying model.

```python
# top_k handling for OpenRouter compatibility
extra_body = {}
if top_k is not None:
    extra_body["top_k"] = top_k

return ChatOpenAI(
    model_kwargs={**kwargs, **({"extra_body": extra_body} if extra_body else {})},
)
```

---

#### `core/prompts.py` — Prompt Registry

Contains all system prompts, organized by purpose:

| Constant | Purpose | Used By |
|----------|---------|---------|
| `PROMPTS` | Dict of 5 technique prompts | Prompt Lab |
| `SYSTEM_PROMPT` | Interviewer persona | Interview (simple chain) |
| `AGENT_SYSTEM_PROMPT` | Interviewer + tool guidelines | Interview (agent mode) |
| `INJECTION_DETECTION_PROMPT` | Security classifier | `security.py` |
| `VALIDATION_PROMPT` | Job description validator | `validation.py` |
| `TECHNIQUE_META` | Display names + emojis for techniques | Prompt Lab UI |
| `TOOL_DISPLAY_NAMES` | Friendly names for agent tools | Interview UI |
| `AVAILABLE_MODELS` | Model IDs → display labels | Sidebar UI |

---

#### `core/security.py` — Injection Detection

**Function:** `check_prompt_injection(text: str) → dict`

Returns: `{"injection_detected": bool, "reason": str}`

Two-layer detection pipeline:

**Layer 1 — Regex Pre-filter** (instant, zero-cost):

```python
_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules))"
    r"|(you\s+are\s+now\s+(?:a|an|the)\s+)"
    r"|(jailbreak|DAN\s*mode|developer\s*mode)"
    r"|(\[SYSTEM\]|\[INST\]|\<\|im_start\|)"
    # ... and more patterns
)
```

Catches patterns like:
- "ignore all previous instructions"
- "you are now a [role]"
- "pretend you are"
- `[SYSTEM]`, `[INST]`, `<|im_start|>` (raw prompt tokens)
- "jailbreak", "DAN mode", "developer mode"

**Layer 2 — LLM Classification** (runs if regex passes):

A separate `temperature=0.0` LLM chain classifies the message. The prompt includes an explicit whitelist of normal interview behaviors (asking to skip questions, requesting hints, etc.) to reduce false positives.

---

### 3.4 Data Layer

#### `data/scraper.py` — Web Scraper

**Function:** `scrape_job_url(url: str) → dict`

Returns: `{"success": bool, "text": str, "method": str, "error": str | None}`

Multi-strategy extraction pipeline with graceful fallbacks:

```
URL → _fetch_html() → BeautifulSoup → Extraction Pipeline → Result
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                               JSON-LD   Meta Tags   HTML Content
                                    │         │         │
                                    └─────────┼─────────┘
                                              │ (if all fail)
                                              ▼
                                      Jina Reader API
```

| Strategy | Method | Priority |
|----------|--------|----------|
| `_extract_json_ld()` | Parses `<script type="application/ld+json">` for `JobPosting` schema | 1st (highest) |
| `_extract_meta_tags()` | Reads Open Graph `og:title`, `og:description` | Combined with HTML |
| `_extract_main_content()` | CSS selectors for job-related elements, then `<article>`, `<main>`, `<body>` | 2nd |
| `fetch_via_jina()` | Jina Reader API (`r.jina.ai/URL`) for JS-rendered pages | Last resort |

**HTML Fetching** (`_fetch_html()`):
1. **CloudScraper** (primary) — Handles Cloudflare challenges, JS-based cookie walls
2. **Requests** (fallback) — Standard HTTP with browser-like headers, retries on cookie pages

All text is truncated to 8,000 characters to stay within LLM context limits.

---

#### `data/vector_store.py` — ChromaDB Session Persistence

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `search_similar_session` | `(job_desc: str) → dict \| None` | Find similar previous session |
| `save_session` | `(job_desc: str, messages: list) → str` | Save/update session |
| `delete_session` | `(session_id: str) → None` | Delete session by ID |
| `list_sessions` | `() → list[dict]` | List all stored sessions |

**Configuration:**

| Setting | Value | Description |
|---------|-------|-------------|
| Storage | `./chroma_db/` (persistent) | Local directory relative to project root |
| Collection | `interview_sessions` | Single collection for all sessions |
| Distance metric | Cosine | `{"hnsw:space": "cosine"}` |
| Similarity threshold | 0.25 | Maximum cosine distance to consider "similar" |
| ID generation | SHA-256 hash of job description (first 16 chars) | Deterministic, enables upsert |

**Data model:** Each document in the collection stores:
- **Document text**: The full job description (used as embedding)
- **Metadata**: `{"messages": JSON string of chat history, "message_count": int}`

ChromaDB uses its built-in default embedding model (Sentence Transformers) to embed job descriptions and compute cosine similarity.

---

### 3.5 Services Layer

#### `services/interview.py` — Interview Orchestration

Provides two modes of interview interaction:

**Simple Chain Mode:**
```
get_interview_response(history, temperature, model, **kwargs) → (text, usage_dict)
```

Pipeline: `ChatPromptTemplate → ChatOpenAI → AIMessage`

**Agent Mode (LangGraph):**
```
get_agent_interview_response(history, temperature, model, **kwargs) → (text, tools_used, usage_dict)
```

Pipeline: `create_react_agent(llm, tools, prompt) → invoke → parse results`

The agent uses LangGraph's `create_react_agent`, which implements the ReAct (Reasoning + Acting) pattern: the LLM can decide when to call tools and how to incorporate tool results.

**Usage Extraction** (`_extract_usage()`):
Handles two different LangChain metadata formats:
1. `response_metadata.token_usage` (OpenAI format)
2. `usage_metadata` (LangChain native format)

For agent mode, token usage is **aggregated** across all AI messages in the agent's execution trace.

---

#### `services/pricing.py` — Cost Calculator

**Functions:**

| Function | Description |
|----------|-------------|
| `get_model_pricing(model_id)` | Returns `{"prompt": float, "completion": float}` per-token costs |
| `calculate_cost(model_id, prompt_tokens, completion_tokens)` | Returns total cost in USD |
| `format_cost_caption(model_id, usage)` | Returns human-readable string |

Pricing data is fetched from the OpenRouter Models API (`GET /api/v1/models`) and cached for 1 hour using Streamlit's `@st.cache_data(ttl=3600)`.

**Cost formula:**
$$\text{cost} = (\text{prompt\_tokens} \times \text{price\_per\_prompt\_token}) + (\text{completion\_tokens} \times \text{price\_per\_completion\_token})$$

---

#### `services/prompt_lab.py` — Technique Comparison

**Function:**
```
get_response_with_prompt(system_prompt, user_message, temperature, model, **kwargs) → (text, usage_dict)
```

Simple single-turn chain: `system prompt + user message → ChatOpenAI → response`. Used by the Prompt Lab page to run the same job description through all 5 techniques.

---

#### `services/validation.py` — Job Description Validator

**Function:**
```
validate_job_description(text: str) → {"valid": bool, "dotnet_related": bool, "reason": str}
```

Uses a `temperature=0.0` LLM chain to classify input text. Checks two conditions:
1. **Legitimacy** — Is it a real job description (not gibberish/spam)?
2. **.NET relevance** — Does it mention C#, .NET, ASP.NET, Azure, or related technologies?

---

### 3.6 Tools Layer

LangGraph agent tools, all decorated with `@tool` from `langchain_core.tools`:

#### `tools/search.py` — Web Search

```python
@tool
def search_dotnet_docs(query: str) → str
```

Searches the web via **Jina Search API** (`s.jina.ai/{query}`). Returns up to 3,000 characters of plain text results. Used by the agent to find current .NET documentation and best practices.

#### `tools/docs.py` — Documentation Fetcher

```python
@tool
def fetch_documentation(url: str) → str
```

Reads a specific URL via **Jina Reader API** (`r.jina.ai/{url}`). Returns up to 3,000 characters. Reuses `fetch_via_jina()` from the scraper module.

#### `tools/code_review.py` — Code Analyzer

```python
@tool
def evaluate_code(code: str) → str
```

Performs in-depth C#/.NET code review. Creates a separate LLM instance with `temperature=0.2` for deterministic analysis. Reviews:
1. Correctness — bugs, edge cases
2. Quality — .NET conventions, clean code
3. Performance — optimization opportunities
4. Improvements — actionable suggestions

---

### 3.7 UI Layer

#### `ui/sidebar.py` — Shared Sidebar

**Functions:**
- `render_sidebar() → str` — Renders navigation radio + 7 model settings, returns selected page name
- `get_model_kwargs() → dict` — Collects non-default settings from `st.session_state` into a kwargs dict

Only passes parameters to the LLM factory when they differ from defaults (e.g., `top_p` is only included if < 1.0, `top_k` only if > 0).

#### `ui/interview_page.py` — Interview Chat

Main page with:
- **Job description intake** — Text area or URL input
- **Validation pipeline** — Injection check → legitimacy check → .NET relevance check
- **Vector DB resume** — Searches ChromaDB for similar previous sessions, offers to continue
- **Chat loop** — Streamlit `st.chat_input` + `st.chat_message` with full history
- **Agent mode toggle** — Sidebar checkbox to enable LangGraph agent with tools
- **Cost tracking** — Per-message caption + sidebar session total metric

**State management** (Streamlit session_state):

| Key | Type | Purpose |
|-----|------|---------|
| `messages` | `list[dict]` | Chat history |
| `interview_validated` | `bool` | Whether job desc is validated |
| `interview_job_desc` | `str` | Current job description |
| `agent_mode` | `bool` | Agent tools enabled |
| `session_cost` | `float` | Running USD total |
| `temperature` | `float` | Current temperature setting |
| `model` | `str` | Current model ID |
| `pending_similar` | `dict` | Similar session found (pending user choice) |

#### `ui/prompt_lab_page.py` — Technique Comparison Lab

Runs all 5 prompting techniques on the same job description and displays results in expandable sections. Shows:
- Response text per technique
- Token usage and cost per technique
- Progress bar during execution

---

## 4. Prompt Engineering

### 5 Prompting Techniques

Each technique produces a different style of interview preparation analysis:

#### 1. Zero-Shot Prompting
```
"Analyse the job description provided by the user and create a focused
interview preparation strategy..."
```
- **Approach:** Direct instruction with no examples
- **Strengths:** Fast, concise, works well for straightforward job descriptions
- **Typical output:** Prioritized study plan with key topics

#### 2. Few-Shot Learning
```
"Below are examples of how you should analyse a job description:
Example 1 — Input: 'Senior .NET Developer with ASP.NET Core...'
Analysis: • Core skills: C#, ASP.NET Core, Azure..."
```
- **Approach:** 2 complete examples of analysis before the actual task
- **Strengths:** Consistent output format, reliable categorization
- **Typical output:** Structured analysis matching the example format

#### 3. Chain-of-Thought
```
"Step 1 — EXTRACT: List every technical skill...
Step 2 — CLASSIFY: Group into categories...
Step 3 — ASSESS SENIORITY: Identify signals...
Step 4 — DETECT GAPS: Note implied skills...
Step 5 — PRIORITISE: Rank by interview weight...
Step 6 — BUILD STRATEGY: Suggest study areas..."
```
- **Approach:** Explicit 6-step reasoning chain
- **Strengths:** Most thorough analysis, catches implicit requirements
- **Typical output:** Step-by-step breakdown with reasoning visible at each stage

#### 4. Self-Consistency
```
"Analyse from three independent perspectives:
Perspective A — The Hiring Manager...
Perspective B — The Tech Lead...
Perspective C — The Recruiter...
Then SYNTHESISE into a single strategy."
```
- **Approach:** Three independent analyses merged into consensus
- **Strengths:** Catches different priority angles, robust prioritization
- **Typical output:** Three separate analyses + synthesized final strategy

#### 5. Generated Knowledge
```
"PHASE 1 — KNOWLEDGE GENERATION: Generate background knowledge...
PHASE 2 — JOB DESCRIPTION ANALYSIS: Map requirements to knowledge...
PHASE 3 — PREPARATION STRATEGY: Combine into study plan..."
```
- **Approach:** Self-generated industry knowledge before analysis
- **Strengths:** Provides context even for vague job descriptions, includes "curveball" predictions
- **Typical output:** Industry knowledge section + job-specific analysis + preparation timeline

### Interview System Prompt

The interviewer persona prompt enforces:
1. **One question at a time** — Prevents overwhelming the candidate
2. **Adaptive difficulty** — Adjusts based on answer quality
3. **Constructive feedback** — Brief feedback before each new question
4. **English-only** — Requests rephrasing if candidate writes in another language
5. **Coverage areas** — C#, ASP.NET Core, EF Core, Architecture, Testing, Azure, SQL, APIs, Security

---

## 5. Security Architecture

### Threat Model

| Threat | Mitigation | Layer |
|--------|------------|-------|
| Prompt injection (role hijack) | Regex + LLM classification | Input |
| Gibberish / spam input | LLM-based validation | Input |
| Non-.NET job descriptions | LLM validation with domain check | Input |
| Token injection via raw prompt tokens | Regex catches `[SYSTEM]`, `[INST]`, `<\|im_start\|>` | Input |
| False positive injection on normal interview text | Whitelist of normal behaviors in detection prompt | Classification |

### Security Pipeline (per user message)

```
User Input
    │
    ▼
┌──────────────────┐
│ Regex Pre-filter  │ ── match → 🛑 BLOCKED (instant, free)
│ _INJECTION_PATTERNS│
└────────┬─────────┘
         │ no match
         ▼
┌──────────────────┐
│ LLM Classifier   │ ── injection_detected: true → 🛑 BLOCKED
│ temperature=0.0  │
│ + whitelist      │
└────────┬─────────┘
         │ safe
         ▼
    ✅ PASSED → Continue to interview
```

### Regex Patterns Detected

| Category | Examples |
|----------|----------|
| System override | "ignore all previous instructions", "disregard your rules" |
| Role switching | "you are now a [role]", "pretend you are", "act as if you" |
| Prompt extraction | "system:", "new instructions:" |
| Known jailbreaks | "DAN mode", "developer mode", "jailbreak" |
| Raw tokens | `[SYSTEM]`, `[INST]`, `<\|im_start\|>` |

---

## 6. Agent System (LangGraph)

### ReAct Pattern

The agent uses LangGraph's `create_react_agent`, which implements the **ReAct** (Reasoning + Acting) loop:

```
                    ┌─────────────┐
                    │   LLM Call  │
                    │ (reasoning) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼────┐
        │ Web Search│ │Fetch   │ │Code     │
        │ (.NET)    │ │Docs    │ │Review   │
        └─────┬─────┘ └───┬────┘ └────┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │ LLM Call    │
                    │ (synthesis) │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Final      │
                    │  Response   │
                    └─────────────┘
```

The LLM autonomously decides:
- **Whether** to use tools (not every message needs them)
- **Which** tool(s) to use
- **How** to incorporate tool results into the conversation

### Tool Registration

Tools are registered as standard LangChain `@tool` functions with typed arguments and docstrings. LangGraph converts the docstrings into tool descriptions that the LLM uses to decide when to call each tool.

### Agent Prompt Extension

The agent's system prompt extends the base interview prompt with:
```
AGENT CAPABILITIES:
- search_dotnet_docs: Search for .NET documentation...
- fetch_documentation: Read specific documentation URLs...
- evaluate_code: Code review on candidate code snippets...

Guidelines for tool usage:
- Use search_dotnet_docs when you want to verify a concept
- Use evaluate_code when the candidate shares code
- You do NOT need to use tools for every interaction
- Incorporate tool results naturally
- Never show raw tool output
```

---

## 7. Vector Database (ChromaDB)

### Session Lifecycle

```
New Interview
    │
    ▼
search_similar_session(job_desc)
    │
    ├── Found (distance ≤ 0.25)
    │       │
    │       ▼
    │   Show resume prompt
    │       ├── "Continue previous" → Load messages
    │       └── "Start new" → Empty messages
    │
    └── Not found
            │
            ▼
        Start fresh interview
            │
            ▼ (after each message)
        save_session(job_desc, messages)  ← upsert
```

### Embedding & Search

- **Embedding model:** ChromaDB's default (all-MiniLM-L6-v2 from Sentence Transformers)
- **Distance metric:** Cosine similarity
- **Threshold:** 0.25 maximum distance (≈ 75% similarity minimum)
- **Query:** `collection.query(query_texts=[job_desc], n_results=1)`

### Storage Format

```
Collection: interview_sessions
├── Document: "Senior .NET Developer with C#, ASP.NET Core..."
│   ├── ID: sha256(document)[:16]
│   └── Metadata:
│       ├── messages: '[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]'
│       └── message_count: 12
```

---

## 8. Web Scraping Pipeline

### Strategy Priority

```
URL Input
    │
    ▼
┌────────────────┐
│ _fetch_html()  │
│ CloudScraper   │──fail──→ requests.Session
│ (JS/Cloudflare)│         (browser headers)
└───────┬────────┘
        │ HTML
        ▼
┌──────────────────────────────────────────┐
│           BeautifulSoup Parse            │
│                                          │
│ 1. JSON-LD (JobPosting schema)           │
│    → Title, Company, Location, Desc      │
│                                          │
│ 2. Meta Tags (og:title, og:description)  │
│    + HTML Content Extraction             │
│    → CSS selectors for job elements      │
│    → article/main/body fallback          │
│                                          │
│ 3. Jina Reader API (last resort)         │
│    → JS-rendered plain text              │
└──────────────────────────────────────────┘
```

### Content Extraction Selectors

For HTML content extraction, the scraper tries these CSS selectors in order:

```python
selectors = [
    "[class*='job-description']",
    "[class*='jobDescription']",
    "[class*='job-detail']",
    "[class*='jobDetail']",
    "[class*='vacancy']",
    "[class*='posting-description']",
    "[class*='listing-description']",
    "[id*='job-description']",
    "[id*='jobDescription']",
    "article",
    "main",
    "[role='main']",
]
```

---

## 9. Pricing System

### Architecture

```
OpenRouter Models API
(GET /api/v1/models)
        │
        ▼ (cached 1hr)
┌──────────────────┐
│ _fetch_all_model │
│    _pricing()    │ ← @st.cache_data(ttl=3600)
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
get_model   calculate
_pricing()  _cost()
    │         │
    └────┬────┘
         ▼
format_cost_caption()
    │
    ▼
"💰 Tokens: 1,234 in / 567 out (1,801 total) · Cost: $0.000789"
```

### Cost Tracking Flow

1. Every LLM call returns an `AIMessage` with token usage metadata
2. `_extract_usage()` normalizes into `{"prompt_tokens", "completion_tokens", "total_tokens"}`
3. `format_cost_caption()` computes and formats the cost per message
4. `_accumulate_session_cost()` adds to the running `st.session_state.session_cost`
5. Session cost displayed as a `st.metric` in the sidebar

---

## 10. Data Flow Diagrams

### Interview Chat Flow

```
User types message
        │
        ▼
check_prompt_injection(text)
        │
        ├── Injection → Error message, stop
        │
        ▼
Append to st.session_state.messages
        │
        ▼
┌───────────────────────────┐
│ Agent Mode?               │
├── Yes ────────────────────┤
│   get_agent_interview_    │
│   response()              │
│   → (text, tools, usage)  │
├── No ─────────────────────┤
│   get_interview_response()│
│   → (text, usage)         │
└───────────┬───────────────┘
            │
            ▼
format_cost_caption(model, usage)
            │
            ▼
Append assistant message + metadata
            │
            ▼
save_session(job_desc, messages) → ChromaDB
            │
            ▼
st.rerun() → Refresh UI
```

### Prompt Lab Flow

```
User provides job description
        │
        ▼
check_prompt_injection(text)
        │
        ▼
validate_job_description(text)
        │
        ▼
For each technique in PROMPTS (5 total):
    │
    ├── get_response_with_prompt(system_prompt, user_message)
    │       → (response_text, usage_dict)
    │
    ├── format_cost_caption(model, usage)
    │
    └── Store in st.session_state.lab_results[technique_key]
        │
        ▼
Display all results in expandable cards
```

---

## 11. API Dependencies

### OpenRouter API

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `POST /api/v1/chat/completions` | LLM inference (via LangChain) | Bearer token |
| `GET /api/v1/models` | Model pricing metadata | Bearer token |

### Jina APIs (free, no auth)

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET https://r.jina.ai/{url}` | Render + read any URL (Reader) | Plain text |
| `GET https://s.jina.ai/{query}` | Web search (Search) | Plain text |

---

## 12. Configuration Reference

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenRouter API key |
| `OPENAI_MODEL` | Yes | — | Default model (e.g., `openai/gpt-5-mini`) |

### Available Models

| Model ID | Display Name | Use Case |
|----------|-------------|----------|
| `openai/gpt-5-mini` | GPT-5 Mini (recommended) | Best quality/cost balance |
| `openai/gpt-5-nano` | GPT-5 Nano (cheaper) | Budget-friendly, faster |
| `openai/gpt-5` | GPT-5 (higher-capability) | Maximum quality |

### Hardcoded Constants

| Constant | Location | Value | Purpose |
|----------|----------|-------|---------|
| `SIMILARITY_THRESHOLD` | `data/vector_store.py` | `0.25` | Max cosine distance for session matching |
| `_COLLECTION_NAME` | `data/vector_store.py` | `"interview_sessions"` | ChromaDB collection name |
| `_DB_DIR` | `data/vector_store.py` | `./chroma_db/` | ChromaDB storage path |
| Text max length | `data/scraper.py` | `8000` chars | Scraper output truncation |
| Tool output max | `tools/*.py` | `3000` chars | Agent tool output truncation |
| Cache TTL | `services/pricing.py` | `3600` sec (1hr) | Pricing data cache duration |

---

## 13. Error Handling

### Strategy

The application applies a **graceful degradation** approach:

| Component | Failure Mode | Behavior |
|-----------|-------------|----------|
| Web scraper (CloudScraper) | Network/timeout | Falls back to `requests` → Jina Reader |
| Jina Reader API | Timeout/error | Returns `None`, scraper returns error dict |
| LLM call (injection check) | JSON parse error | Returns `injection_detected: False` (fail open) |
| LLM call (validation) | JSON parse error | Returns `valid: False` (fail closed) |
| ChromaDB query | Empty collection | Returns `None` (no resume offered) |
| Pricing API | Timeout/error | Returns empty dict, cost displays as $0 |
| Agent tool execution | Any exception | Returns error string, agent continues |

### Key Design Decision

- **Security classification fails open** — If the injection detection LLM returns unparseable output, the message is allowed through. This avoids blocking legitimate users due to LLM formatting issues.
- **Input validation fails closed** — If the validation LLM returns unparseable output, the input is rejected. This prevents invalid data from entering the interview pipeline.
