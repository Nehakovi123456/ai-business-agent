# 🚀 AI Business Research & Decision Support Agent

> An Enterprise-Grade Multi-Agent AI System built with **LangGraph**, **LangChain**, **FastAPI**, **Streamlit**, **ChromaDB**, **SQLite**, and **ReportLab**.

---

## 🎯 Overview

Instead of asking a simple chatbot a broad business question (e.g. *"Should Company X launch an affordable electric scooter in India?"*) and getting a generic generated response, this system delegates the strategic inquiry across **6 specialized AI agents**. 

The agents collaborate to perform live web market research, search internal company documents via RAG vector search, benchmark competitors, evaluate financial sensitivity, verify claims for AI hallucination prevention, and output executive decision reports with downloadable PDF artifacts.

---

## 🏗️ Architecture

```
                                 USER / STREAMLIT UI
                                          │
                                          ▼
                                   FASTAPI BACKEND
                                          │
                                          ▼
                                LANGGRAPH ORCHESTRATOR
                                          │
       ┌──────────────────────────────────┼──────────────────────────────────┐
       ▼                                  ▼                                  ▼
 🔍 Research Agent                   📄 RAG Agent                   ⚔️ Competitor Agent
(DuckDuckGo / Web)             (ChromaDB + Vector Store)           (Pricing & Market Grid)
       │                                  │                                  │
       └──────────────────────────────────┼──────────────────────────────────┘
                                          ▼
                                 💡 Analysis Agent
                           (Attractiveness & What-If)
                                          │
                                          ▼
                                🛡️ Fact-Check Agent
                             (Contradictions & Audit)
                                          │
                                          ▼
                                 📊 Report Agent
                             (Markdown + PDF Exporter)
```

---

## 🤖 The 6 Specialized Agents

| # | Agent Name | Core Role & Responsibilities | Key Tools / Technologies |
|---|---|---|---|
| 1 | **Supervisor / Orchestrator Agent** | Receives business question, decomposes problem into sub-tasks, and orchestrates agent execution flow. | LangGraph StateGraph |
| 2 | **Research Agent** | Gathers external market size, growth drivers, consumer demographics, and regulatory policies. | DuckDuckGo / Tavily Search API |
| 3 | **RAG / Document Agent** | Indexes and retrieves passages from internal company PDFs, DOCX, CSVs, and annual reports. | ChromaDB, PyPDF, Pandas |
| 4 | **Competitor Analysis Agent** | Compiles pricing comparison grids, feature matrix, market share split, strengths, and weaknesses. | Competitor Matrix Engine |
| 5 | **Analysis & Decision Agent** | Calculates Market Attractiveness (0-10), Risk Level, Opportunity Rating, and runs What-If sensitivity scenarios. | Elasticity & Financial Simulator |
| 6 | **Fact-Checker Agent** | Compares report claims against raw evidence snippets to tag claims as Supported, Unsupported, or Conflicting. | Evidence Audit Engine |
| 7 | **Report Generation Agent** | Synthesizes executive report in Markdown and exports styled PDFs. | ReportLab PDF Exporter |

---

## ⭐ Core Features

### 🟢 MVP Features
- [x] Natural language business inquiry input & preset scenarios.
- [x] LangGraph state-driven 6-agent workflow.
- [x] Document RAG pipeline (PDF, DOCX, CSV, TXT ingestion).
- [x] Multi-provider LLM support (Gemini 1.5 Flash, OpenAI GPT-4o-mini, Ollama local, or Offline fallback).

### 🚀 Advanced Features
- [x] **FastAPI REST Endpoints**: Headless API for document upload, analysis, reports, and PDF downloads.
- [x] **SQLite Historical Database**: Permanent persistence of queries, report archives, and agent execution trace logs.
- [x] **Real-Time Agent Activity Tracker**: Live progress status cards showing which agent is active.
- [x] **ReportLab PDF Exporter**: One-click downloadable executive PDF reports.

### 🔥 Unique & Differentiating Features
1. **Evidence Verification & Fact-Checking Audit**: Every key claim in the report is cross-referenced with retrieved evidence chunks to detect hallucinations.
2. **Contradiction Detection Engine**: Automatically flags when two data sources report conflicting numbers (e.g. Source A says 12% growth, Source B says 18% growth).
3. **Interactive What-If Sensitivity Simulator**: Interactive sliders allow users to adjust price change % and cost structure to see volume demand and margin impact.
4. **Human-in-the-Loop Review Step**: Optional approval checkpoint allowing humans to review intermediate recommendations before final report publication.

---

## 📦 Project Structure

```
.
├── app.py                          # Streamlit Interactive Web Application
├── api.py                          # FastAPI REST API Backend
├── requirements.txt                # System Python dependencies
├── .env.example                    # Environment variable template
├── sample_data/                    # Sample internal company reports for instant testing
│   ├── company_annual_report_2025.txt
│   └── ev_market_internal_summary.csv
├── src/
│   ├── config.py                   # Centralized configuration & LLM provider fallback
│   ├── db/
│   │   └── database.py             # SQLite database manager
│   ├── rag/
│   │   ├── ingestion.py            # PDF/DOCX/CSV/TXT loader & text chunker
│   │   └── vectorstore.py          # ChromaDB vector store manager & retriever
│   ├── tools/
│   │   ├── search_tool.py          # Web search tool wrapper
│   │   ├── rag_tool.py             # RAG document retriever tool
│   │   ├── what_if_tool.py         # Financial sensitivity simulator
│   │   └── fact_check_tool.py      # Evidence verifier & contradiction detector
│   ├── graph/
│   │   ├── state.py                # AgentState TypedDict schema
│   │   └── workflow.py             # LangGraph StateGraph builder
│   ├── agents/
│   │   ├── supervisor.py           # Supervisor Orchestrator Agent
│   │   ├── research_agent.py       # Web Market Research Agent
│   │   ├── rag_agent.py            # RAG Document Intelligence Agent
│   │   ├── competitor_agent.py     # Competitor Benchmarking Agent
│   │   ├── analysis_agent.py       # Decision & Financial Analysis Agent
│   │   ├── fact_check_agent.py     # Fact-Checker Agent
│   │   └── report_agent.py         # Report Synthesizer Agent
│   └── reports/
│       └── pdf_generator.py        # ReportLab PDF report exporter
└── README.md                       # Comprehensive guide & Technical Interview Manual
```

---

## ⚡ Quick Start Guide

### 1. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and add your API key (Gemini, OpenAI, or Tavily):
```bash
cp .env.example .env
```

### 3. Run Streamlit Dashboard
Launch the interactive web application:
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

### 4. Run FastAPI Backend (Optional)
Launch the REST API server:
```bash
uvicorn api:app --reload --port 8000
```
API Documentation available at `http://localhost:8000/docs`.

---

## 🎙️ Technical Interview Speaking Guide

When interviewing for AI Engineering, LLM System Architect, or Data Science roles, use this structured framework to explain this project:

### 1. Elevator Pitch (30 seconds)
> *"I built an Enterprise Multi-Agent System called the **AI Business Research & Decision Support Agent**. Instead of relying on a single LLM prompt, it uses **LangGraph** to coordinate 6 specialized agents—Supervisor, Market Research, Document RAG, Competitor Benchmarking, Financial Analysis, and Fact-Checking. It ingests company PDFs and market data into **ChromaDB**, runs sensitivity models, verifies assertions against evidence to prevent AI hallucinations, and outputs executive decision reports with PDF export capabilities."*

### 2. Deep Dive: "Why LangGraph over standard LangChain sequential chains?"
> *"Standard sequential chains are rigid. LangGraph allows cyclic state graphs, explicit state sharing via `TypedDict` schemas, conditional edge routing, and human-in-the-loop state interrupts. For example, if our Fact-Checker Agent detects unsupported claims or contradictory metrics, it can route back to the RAG or Research Agent before finalizing the report."*

### 3. Deep Dive: "How did you address AI Hallucinations?"
> *"I implemented a dedicated **Fact-Checker Agent** and **Evidence Verification Engine**. Before the final report is compiled, draft assertions are cross-referenced with exact chunk IDs from ChromaDB and web snippets. We perform keyword density matching, numerical cross-verification, and contradiction detection to score verifiability."*

### 4. Key Takeaways for Interviewers
- **Agentic AI Architecture**: Multi-agent coordination with state preservation.
- **RAG Production Practices**: Chunking with overlap, metadata tracking, vector persistence.
- **Enterprise Features**: PDF generation, SQLite auditing, FastAPI REST API, Streamlit UI.
