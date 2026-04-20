# 💼 Senior .NET Interview Preparation App

An AI-powered interview coaching application built with **Streamlit**, **LangChain**, and **OpenRouter**. Practice for Senior .NET Developer interviews with an adaptive AI interviewer that provides real-time feedback, searches live documentation, and reviews your code.

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![LangChain](https://img.shields.io/badge/LangChain-0.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

### Core
- **Interactive Interview Chat** — Multi-turn conversation with an AI interviewer that adapts question difficulty based on your answers
- **5 Prompting Techniques** — Zero-Shot, Few-Shot, Chain-of-Thought, Self-Consistency, and Generated Knowledge
- **Prompt Lab** — Side-by-side comparison of all 5 techniques on the same job description
- **Full Model Tuning** — Temperature, Top P, Top K, Frequency Penalty, Presence Penalty, Max Tokens
- **3 Model Options** — GPT-5 Mini (recommended), GPT-5 Nano (cheap), GPT-5 (premium)

### Agent Mode (LangGraph)
- 🔍 **Web Search** — Live .NET documentation search via Jina Search API
- 📄 **Fetch Docs** — Reads specific Microsoft Learn / documentation pages
- 🔬 **Code Review** — In-depth analysis of C# code snippets you provide

### Security
- **Two-layer injection detection** — Regex pre-filter + LLM-based classification
- **Input validation** — Verifies job descriptions are legitimate and .NET-related
- **English-only enforcement** — Interview conducted entirely in English

### Data & Persistence
- **ChromaDB Vector Store** — Resume previous interview sessions with similar job descriptions
- **Multi-strategy Web Scraper** — Extract job postings from URLs (CloudScraper → Requests → Jina Reader)
- **JSON-LD / Meta tag parsing** — Structured data extraction from job posting sites

### Cost Tracking
- **Live pricing** — Fetches current model pricing from OpenRouter API
- **Per-message cost** — Displays token count and USD cost after each response
- **Session total** — Running cost accumulator in the sidebar

---

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│         Streamlit UI (app.py)        │
│  ├─ 🎙️ Interview Page               │
│  └─ 🔬 Prompt Lab Page              │
└──────────────┬───────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────────┐
│  Services   │  │     Core        │
│ ├ interview │  │ ├ llm (factory) │
│ ├ pricing   │  │ ├ prompts       │
│ ├ validation│  │ └ security      │
│ └ prompt_lab│  └──────┬──────────┘
└──────┬──────┘         │
       │         ┌──────▼──────────┐
       │         │  Tools (Agent)  │
       │         │ ├ search        │
       │         │ ├ docs          │
       │         │ └ code_review   │
       │         └─────────────────┘
       │
┌──────▼──────┐  ┌─────────────────┐
│    Data     │  │  External APIs  │
│ ├ scraper   │  │ ├ OpenRouter    │
│ └ vector_store│ │ ├ Jina API     │
└─────────────┘  │ └ ChromaDB     │
                 └─────────────────┘
```

The project follows a **layered architecture** with clear separation of concerns:

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **UI** | `ui/` | Streamlit pages, sidebar, user interaction |
| **Services** | `services/` | Business logic, chain/agent orchestration |
| **Core** | `core/` | LLM factory, prompts, security |
| **Tools** | `tools/` | LangGraph agent tools (search, docs, code review) |
| **Data** | `data/` | Web scraping, ChromaDB vector store |

---

## 📂 Project Structure

```
TurungInterviewApp/
├── app.py                    # Streamlit entry point
├── config.py                 # Environment variable loader
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not in repo)
├── .env.example              # Template for .env
├── README.md                 # This file
├── TECHNICAL_DOCS.md         # Detailed technical documentation
│
├── core/                     # Core modules
│   ├── llm.py                # LLM factory (ChatOpenAI → OpenRouter)
│   ├── prompts.py            # All prompts & metadata
│   └── security.py           # Prompt injection detection
│
├── data/                     # Data layer
│   ├── scraper.py            # Multi-strategy job URL scraper
│   └── vector_store.py       # ChromaDB session persistence
│
├── services/                 # Business services
│   ├── interview.py          # Interview chain & agent
│   ├── pricing.py            # OpenRouter pricing calculator
│   ├── prompt_lab.py         # Single-turn technique comparison
│   └── validation.py         # Job description validator
│
├── tools/                    # LangGraph agent tools
│   ├── search.py             # Web search (.NET docs)
│   ├── docs.py               # URL content fetcher
│   └── code_review.py        # C# code analysis
│
├── ui/                       # Streamlit UI
│   ├── sidebar.py            # Navigation & model settings
│   ├── interview_page.py     # Interview chat interface
│   └── prompt_lab_page.py    # Technique comparison lab
│
└── chroma_db/                # ChromaDB persistent storage (auto-created)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- An [OpenRouter API key](https://openrouter.ai/keys)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/TuringCollegeSubmissions/agalva-AE.1.5.git
cd TurungInterviewApp

# 2. Create virtual environment
python -m venv .venv

# 3. Activate it
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

### Configuration

Create a `.env` file with:

```env
OPENAI_API_KEY=sk-or-v1-your-openrouter-api-key-here
OPENAI_MODEL=openai/gpt-5-mini
```

### Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 📖 How to Use

### Interview Mode

1. **Paste a job description** or **enter a URL** — the app scrapes and validates it
2. The AI interviewer analyzes the job requirements and starts with a relevant question
3. Answer questions in the chat — the interviewer adapts difficulty and gives feedback
4. **Enable Agent Mode** (sidebar checkbox) for live .NET doc search and code review
5. Paste C# code snippets to receive in-depth code analysis

### Prompt Lab

1. Enter a job description (same input options)
2. Click **"Validate & Run all techniques"**
3. Compare responses from all 5 prompting techniques side by side
4. Each result shows token count and cost

### Model Tuning

The sidebar provides full control over:

| Setting | Range | Default | Purpose |
|---------|-------|---------|---------|
| Temperature | 0.0 – 2.0 | 0.5 | Randomness/creativity |
| Top P | 0.0 – 1.0 | 1.0 | Nucleus sampling threshold |
| Top K | 0 – 100 | 0 (off) | Limits top token choices |
| Frequency Penalty | -2.0 – 2.0 | 0.0 | Reduces repetition |
| Presence Penalty | -2.0 – 2.0 | 0.0 | Encourages new topics |
| Max Tokens | 0 – 16384 | 0 (auto) | Output length limit |

---

## 💰 Model Pricing

Prices are fetched live from the OpenRouter API and displayed per-message:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-5 Mini | $0.25 | $2.00 |
| GPT-5 Nano | $0.05 | $0.40 |
| GPT-5 | $1.25 | $10.00 |

---

## 🛡️ Security

The app implements multiple security layers:

1. **Regex pre-filter** — Catches common injection patterns instantly (e.g., "ignore all previous instructions", "you are now DAN", `[SYSTEM]`)
2. **LLM-based classification** — A separate zero-temperature LLM call evaluates ambiguous inputs with a conservative prompt (whitelist of normal interview behavior)
3. **Job description validation** — Verifies input is a real, .NET-related job description before starting
4. **English enforcement** — Interviewer requests rephrasing if user writes in another language

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit (wide layout, 2-page app) |
| **LLM Framework** | LangChain + LangChain-OpenAI |
| **Agent Framework** | LangGraph (`create_react_agent`) |
| **LLM Provider** | OpenRouter API (`https://openrouter.ai/api/v1`) |
| **Vector Database** | ChromaDB (persistent, cosine similarity) |
| **Web Scraping** | CloudScraper + BeautifulSoup + Jina Reader API |
| **Language** | Python 3.11 |

---

## 📋 Task Requirements Coverage

### Core Requirements ✅

| # | Requirement | Status | Implementation |
|---|-------------|--------|----------------|
| 1 | Research interview preparation type | ✅ | Senior .NET Developer interview coaching |
| 2 | Build front-end | ✅ | Streamlit with wide layout, 2 pages |
| 3 | Create OpenRouter API key | ✅ | Configured via `.env` |
| 4 | Choose OpenRouter model | ✅ | 3 models: gpt-5-mini, gpt-5-nano, gpt-5 |
| 5 | 5 system prompts with different techniques | ✅ | Zero-Shot, Few-Shot, CoT, Self-Consistency, Generated Knowledge |
| 6 | Tune at least one model setting | ✅ | All 6 tunable: temperature, top_p, top_k, frequency/presence penalty, max_tokens |
| 7 | At least one security guard | ✅ | Two-layer injection detection + input validation |

### Optional Tasks Completed

| Difficulty | Task | Status |
|------------|------|--------|
| **Easy** | More security constraints (LLM validation) | ✅ |
| **Medium** | All model settings as sliders | ✅ |
| **Medium** | Prompt pricing calculation | ✅ |
| **Medium** | Job description URL scraping (RAG input) | ✅ |
| **Medium** | Multiple LLM model selection | ✅ |
| **Hard** | Full chatbot with multi-turn conversation | ✅ |
| **Hard** | LangChain chains and agents | ✅ |
| **Hard** | Vector database for session persistence | ✅ |

---

## 👤 Author

**Turing College** — AI Engineering Sprint 1 Project (AE.1.5)

---

## 📄 License

This project is for educational purposes as part of the Turing College AI Engineering program.
