import os
import time
import pandas as pd
import streamlit as st

from src.config import UPLOAD_DIR, GEMINI_API_KEY, OPENAI_API_KEY, get_llm
from src.db.database import save_query, get_all_reports, get_report_by_id
from src.rag.ingestion import load_file, chunk_documents
from src.rag.vectorstore import VectorDBManager
from src.graph.workflow import run_agent_workflow
from src.tools.what_if_tool import run_what_if_simulation, run_multi_scenario_comparison
from src.reports.pdf_generator import generate_pdf_report

# Page Config
st.set_page_config(
    page_title="AI Business Research & Decision Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom SaaS CSS Styling
st.markdown("""
<style>
    /* SaaS Color Palette */
    :root {
        --primary-blue: #1E3A8A;
        --secondary-blue: #2563EB;
        --light-bg: #F8FAFC;
        --card-border: #E2E8F0;
    }
    
    .saas-header {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .saas-sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.8rem;
    }
    .hero-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 2.2rem;
        border-radius: 0.8rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.8rem;
        color: #ffffff;
    }
    .hero-body {
        font-size: 1.1rem;
        opacity: 0.95;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .feature-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 1.4rem;
        border-radius: 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
    }
    .feature-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .feature-body {
        font-size: 0.95rem;
        color: #4B5563;
        line-height: 1.5;
    }
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 1.2rem;
        border-radius: 0.6rem;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "🏠 Home"
if "latest_report" not in st.session_state:
    st.session_state["latest_report"] = None
if "activity_logs" not in st.session_state:
    st.session_state["activity_logs"] = []

def render_download_buttons(report_markdown: str, key_prefix: str = "main"):
    """Renders prominent PDF and Markdown download buttons reliably."""
    if not report_markdown:
        return
    
    st.markdown("### 📥 Download Executive Report")
    col1, col2 = st.columns(2)
    
    col1.download_button(
        label="📄 Download Markdown Report",
        data=report_markdown,
        file_name="Business_Decision_Report.md",
        mime="text/markdown",
        key=f"{key_prefix}_md_btn",
        use_container_width=True
    )

    try:
        pdf_path = generate_pdf_report(report_markdown, filename=f"report_{key_prefix}.pdf")
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            col2.download_button(
                label="🔴 Download Executive PDF Report",
                data=pdf_bytes,
                file_name="Business_Decision_Report.pdf",
                mime="application/pdf",
                key=f"{key_prefix}_pdf_btn",
                use_container_width=True
            )
        else:
            col2.warning("PDF generation pending...")
    except Exception as e:
        col2.error(f"PDF export error: {e}")

# ==========================================
# SIDEBAR NAVIGATION & CONFIG
# ==========================================
st.sidebar.markdown("## 🤖 Decision Support Suite")

nav_choice = st.sidebar.radio(
    "Navigation Menu",
    ["🏠 Home", "📊 Dashboard", "🔍 New Analysis", "💡 Scenario Simulator", "📁 Knowledge Base", "📚 Reports & History", "⚙️ Settings & Profile"],
    index=["🏠 Home", "📊 Dashboard", "🔍 New Analysis", "💡 Scenario Simulator", "📁 Knowledge Base", "📚 Reports & History", "⚙️ Settings & Profile"].index(st.session_state["nav_page"])
)
st.session_state["nav_page"] = nav_choice

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Quick Configuration")

llm_provider = st.sidebar.selectbox(
    "Select LLM Provider",
    ["gemini", "openai", "ollama", "mock"],
    index=0
)

gemini_env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
openai_env_key = os.getenv("OPENAI_API_KEY") or ""

if llm_provider == "gemini":
    api_key_input = st.sidebar.text_input("Gemini API Key", value=gemini_env_key, type="password")
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        os.environ["GOOGLE_API_KEY"] = api_key_input
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        st.sidebar.warning("⚠️ Gemini API key missing. Set in .env or enter above.")
elif llm_provider == "openai":
    api_key_input = st.sidebar.text_input("OpenAI API Key", value=openai_env_key, type="password")
    if api_key_input:
        os.environ["OPENAI_API_KEY"] = api_key_input
    if not os.getenv("OPENAI_API_KEY"):
        st.sidebar.warning("⚠️ OpenAI API key missing. Set in .env or enter above.")

db_manager = VectorDBManager()
doc_count = db_manager.get_document_count()
st.sidebar.info(f"📊 Vector RAG Count: **{doc_count}** chunks")

# ==========================================
# PAGE 1: 🏠 LANDING / HOME PAGE
# ==========================================
if st.session_state["nav_page"] == "🏠 Home":
    st.markdown('<div class="saas-header">🚀 AI Business Research & Decision Support Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-sub-header">Enterprise Multi-Agent Intelligence System powered by LangGraph, ChromaDB RAG, Competitor Benchmarking & Evidence Fact-Checking</div>', unsafe_allow_html=True)

    # Hero Section Card
    st.markdown("""
    <div class="hero-card">
        <div class="hero-title">Empower Executive Decisions with Multi-Agent AI</div>
        <div class="hero-body">
            Synthesize complex market inquiries using autonomous LangGraph agents. Combine live external web research with private internal company documents via ChromaDB RAG, execute multi-scenario financial elasticity models, audit evidence against AI hallucinations, and generate 30/60/90-day execution roadmaps.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_cta1, col_cta2 = st.columns([1, 3])
    with col_cta1:
        if st.button("🚀 Start New Analysis", type="primary", use_container_width=True):
            st.session_state["nav_page"] = "🔍 New Analysis"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🌟 Key Enterprise Capabilities")

    col_cap1, col_cap2, col_cap3, col_cap4 = st.columns(4)
    with col_cap1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">🧠 Multi-Agent Orchestration</div>
            <div class="feature-body">6 specialized LangGraph agents (Supervisor, Research, RAG, Competitor, Analysis, Fact Checker, Report) decomposing strategic business inquiries.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_cap2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">📄 RAG Citation Isolation</div>
            <div class="feature-body">ChromaDB vector search retrieving exact internal company facts (PDF, DOCX, CSV, TXT) with clear <code>[SOURCE FACT]</code> citations.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_cap3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">⚔️ Competitor & Risk Audit</div>
            <div class="feature-body">Real-time competitor positioning, feature matrices, and Risk & Mitigation tables with monitoring KPIs.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_cap4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">💡 Scenario Simulator</div>
            <div class="feature-body">Side-by-side evaluation of Base Case, -10% Price Discount, +15% Marketing Spend, and Cost Optimization scenarios.</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 2: 📊 DASHBOARD
# ==========================================
elif st.session_state["nav_page"] == "📊 Dashboard":
    st.markdown('<div class="saas-header">📊 Executive Dashboard Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-sub-header">Real-time analytics summary, recent report history, and system status</div>', unsafe_allow_html=True)

    history_reports = get_all_reports()
    latest_rep = st.session_state.get("latest_report")
    metrics = latest_rep.get("analysis_metrics", {}) if latest_rep else {}

    # Stats Row
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    s_col1.metric("Total Executed Reports", f"{len(history_reports)} Reports", "Saved in SQLite")
    s_col2.metric("Active Knowledge Base", f"{doc_count} Chunks", "ChromaDB Memory")
    s_col3.metric("System Confidence", f"{latest_rep.get('confidence_score', 88.5) if latest_rep else 88.5}%", "Fact Verified")
    s_col4.metric("Active LLM Engine", f"{llm_provider.upper()}", "Multi-Agent Backend")

    st.markdown("---")

    # Quick Actions
    st.markdown("### ⚡ Quick Navigation Actions")
    q_col1, q_col2, q_col3 = st.columns(3)
    with q_col1:
        if st.button("🚀 Launch New Feasibility Study", use_container_width=True):
            st.session_state["nav_page"] = "🔍 New Analysis"
            st.rerun()
    with q_col2:
        if st.button("📁 Manage Vector Knowledge Base", use_container_width=True):
            st.session_state["nav_page"] = "📁 Knowledge Base"
            st.rerun()
    with q_col3:
        if st.button("📚 View Full Report Archive", use_container_width=True):
            st.session_state["nav_page"] = "📚 Reports & History"
            st.rerun()

    st.markdown("---")
    st.markdown("### 📜 Recent Business Decision Reports")
    if history_reports:
        df_dash = pd.DataFrame(history_reports)
        st.dataframe(df_dash[["id", "query_text", "confidence_score", "fact_check_status", "created_at"]].head(5), use_container_width=True)
    else:
        st.info("No reports saved yet. Launch a new study in 'New Analysis'.")

# ==========================================
# PAGE 3: 🔍 NEW ANALYSIS (FEASIBILITY STUDY)
# ==========================================
elif st.session_state["nav_page"] == "🔍 New Analysis":
    st.markdown('<div class="saas-header">🔍 Strategic Business Feasibility Study</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-sub-header">Submit a business inquiry to execute the multi-agent decision support workflow</div>', unsafe_allow_html=True)

    # Initialize user_query_text in session state if not present
    if "user_query_text" not in st.session_state:
        st.session_state["user_query_text"] = "Should Company X launch an affordable electric scooter in India?"

    st.markdown("**Sample Preset Scenarios:**")
    col_p1, col_p2, col_p3 = st.columns(3)
    if col_p1.button("🛵 Electric Scooter in India"):
        st.session_state["user_query_text"] = "Should Company X launch an affordable electric scooter in India under ₹90,000?"
        st.rerun()
    if col_p2.button("📱 Budget Smartphone for Students"):
        st.session_state["user_query_text"] = "Analyze launching a budget 5G smartphone for college students in India under ₹12,999."
        st.rerun()
    if col_p3.button("☕ Specialty Coffee Chain in Tier-2"):
        st.session_state["user_query_text"] = "Should we expand our specialty drive-thru coffee chain into Tier-2 Indian cities?"
        st.rerun()

    query_input = st.text_area(
        "Enter your strategic business inquiry:",
        value=st.session_state["user_query_text"],
        key="query_text_area",
        height=100
    )
    st.session_state["user_query_text"] = query_input

    col_btn, col_human = st.columns([2, 3])
    with col_btn:
        start_analysis = st.button("🚀 Run Multi-Agent Feasibility Study", type="primary", use_container_width=True)
    with col_human:
        enable_human_loop = st.checkbox("Enable Human-in-the-Loop Review Step", value=True)

    if start_analysis and query_input.strip():
        if llm_provider != "mock" and get_llm(llm_provider) is None:
            st.error(f"⚠️ {llm_provider.capitalize()} API key is missing or the selected LLM could not be initialized. Please configure a valid LLM provider in the sidebar or .env file.")
            st.stop()

        st.session_state["activity_logs"] = []
        st.markdown("### 🤖 Live Agent Execution Progress")
        progress_bar = st.progress(0)
        status_box = st.empty()

        # Step 1: Supervisor Agent
        status_box.info("🧠 Supervisor Agent is decomposing query into sub-tasks...")
        progress_bar.progress(15)
        query_id = save_query(query_input)

        # Execute Graph Workflow
        with st.spinner("Multi-Agent System executing steps (Research → RAG → Competitor → Analysis → Fact-Checker → Report)..."):
            final_state = run_agent_workflow(query_input, query_id=query_id, llm_provider=llm_provider)

        progress_bar.progress(100)
        status_box.success("✓ All Agents completed execution successfully!")

        st.session_state["latest_report"] = final_state
        st.session_state["activity_logs"] = final_state.get("activity_logs", [])

        # Display Real-time Agent Activity Tracker
        st.markdown("### 📋 Agent Activity Tracker")
        for log in final_state.get("activity_logs", []):
            st.markdown(f"**{log['agent']}**: {log['status']} — *{log['detail']}*")

        if enable_human_loop:
            st.warning("⚠️ **Human-in-the-Loop Approval Step**: Intermediate recommendation is ready for review.")
            st.markdown(f"**Draft Strategic Recommendation:** `{final_state.get('analysis_metrics', {}).get('strategic_recommendation')}`")
            col_app, col_rej = st.columns(2)
            if col_app.button("✅ Approve & Publish Final Report"):
                st.success("Report Approved and saved!")
            if col_rej.button("✏️ Modify Parameters"):
                st.info("You can adjust sensitivity parameters in the 'Scenario Simulator' tab.")

    latest_rep = st.session_state.get("latest_report")
    if latest_rep:
        st.markdown("---")
        st.markdown(latest_rep.get("report_markdown", ""))
        st.markdown("---")
        render_download_buttons(latest_rep.get("report_markdown", ""), key_prefix="new_analysis")

# ==========================================
# PAGE 4: 💡 SCENARIO SIMULATOR
# ==========================================
elif st.session_state["nav_page"] == "💡 Scenario Simulator":
    st.markdown('<div class="saas-header">💡 Multi-Scenario Comparison & Sensitivity Simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-sub-header">Evaluate side-by-side price elasticity, marketing expansion, and cost optimization trade-offs</div>', unsafe_allow_html=True)

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        sim_price = st.number_input("Baseline Unit Price (Rs.)", value=89999.0, step=5000.0)
        sim_cost = st.number_input("Unit Cost (Rs.)", value=68000.0, step=2000.0)
    with col_w2:
        sim_volume = st.number_input("Base Volume (Units)", value=12000, step=1000)
        sim_capacity = st.number_input("Factory Max Capacity Ceiling (Units)", value=15000, step=1000)

    st.markdown("---")
    st.markdown("### 📊 Side-by-Side Multi-Scenario Comparison Table")
    
    multi_scenarios = run_multi_scenario_comparison(
        base_price=sim_price,
        unit_cost=sim_cost,
        base_volume=sim_volume,
        max_capacity=sim_capacity,
        base_marketing_inr=50000000.0
    )

    df_scenarios = pd.DataFrame(multi_scenarios["scenarios"])
    st.dataframe(
        df_scenarios[[
            "name", "unit_price", "unit_cost", "volume", "revenue",
            "unit_margin_pct", "total_net_margin", "plant_capacity_utilization", "risk_rating", "feasibility_score"
        ]],
        use_container_width=True
    )

    st.success(f"💡 **AI Scenario Recommendation:** {multi_scenarios['recommendation']}")

    st.markdown("---")
    st.markdown("### ⚡ Custom Single Scenario Calculator")
    sim_change_pct = st.slider("Price Change Percentage (%)", min_value=-30.0, max_value=30.0, value=-10.0, step=2.5)

    sim_res = run_what_if_simulation(
        base_price=sim_price,
        price_change_percent=sim_change_pct,
        unit_cost=sim_cost,
        base_volume=sim_volume
    )

    s_col1, s_col2, s_col3 = st.columns(3)
    s_col1.metric("New Unit Price", f"Rs. {sim_res['new_price']:,.2f}", f"{sim_change_pct}% Price Shift")
    s_col2.metric("New Unit Margin %", f"{sim_res['new_unit_margin_pct']}%", f"Original: {sim_res['original_unit_margin_pct']}%")
    s_col3.metric("Projected Demand Volume", f"{sim_res['new_expected_volume']:,} units", f"{sim_res['volume_forecast_change_pct']:+}% Demand Shift")

    st.info(f"💡 **Scenario Impact:** {sim_res['recommendation_impact']}")

# ==========================================
# PAGE 5: 📁 KNOWLEDGE BASE (RAG)
# ==========================================
elif st.session_state["nav_page"] == "📁 Knowledge Base":
    st.markdown('<div class="saas-header">📁 Document Knowledge Base (ChromaDB RAG)</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-sub-header">Upload, index, and isolate company documents for vector similarity retrieval</div>', unsafe_allow_html=True)

    col_kb1, col_kb2 = st.columns([2, 1])

    with col_kb1:
        uploaded_file = st.file_uploader(
            "Upload Company Documents (PDF, DOCX, CSV, TXT)",
            type=["pdf", "docx", "csv", "txt"]
        )

        if uploaded_file is not None:
            st.caption("👇 Click the button below to index this file into RAG memory:")
            if st.button("⚡ Index Document into ChromaDB", type="primary", use_container_width=True):
                try:
                    with st.spinner("Processing & Indexing Document..."):
                        file_path = UPLOAD_DIR / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        raw_docs = load_file(file_path)
                        chunks = chunk_documents(raw_docs)
                        if not chunks:
                            st.warning("⚠️ The uploaded file is empty or contains no extractable text.")
                        else:
                            db_manager.add_documents(chunks)
                            st.success(f"✓ Indexed {len(chunks)} chunks into ChromaDB!")
                except Exception as e:
                    st.error(f"❌ Indexing Error: {e}")

    with col_kb2:
        st.markdown("### 📊 Vector DB Status")
        st.info(f"Active Document Chunks: **{doc_count}** chunks")
        if st.button("🗑️ Reset / Clear Vector Knowledge Base", use_container_width=True):
            cleared = db_manager.reset_collection()
            st.success(f"✓ Cleared {cleared} old chunks. Knowledge Base is clean and isolated!")
            st.rerun()

# ==========================================
# PAGE 6: 📚 REPORTS & HISTORY
# ==========================================
elif st.session_state["nav_page"] == "📚 Reports & History":
    st.markdown('<div class="saas-header">📚 Reports & Historical Decision Archive</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-sub-header">Browse, inspect, and export past business decision reports stored in SQLite</div>', unsafe_allow_html=True)

    history_reports = get_all_reports()

    if not history_reports:
        st.info("No historical reports found in database yet.")
    else:
        df_hist = pd.DataFrame(history_reports)
        st.dataframe(df_hist[["id", "query_text", "confidence_score", "fact_check_status", "created_at"]], use_container_width=True)

        selected_id = st.number_input("Enter Report ID to view:", min_value=1, value=history_reports[0]["id"] if history_reports else 1, step=1)
        if st.button("Load Report from Archive"):
            rep_data = get_report_by_id(selected_id)
            if rep_data:
                st.session_state["latest_report"] = {
                    "report_markdown": rep_data["report_markdown"],
                    "confidence_score": rep_data["confidence_score"],
                    "analysis_metrics": rep_data.get("report_json", {}).get("metrics", {}),
                    "fact_check_audit": rep_data.get("report_json", {}).get("fact_audit", {})
                }
                st.success(f"Loaded Report #{selected_id}. Displaying report below:")
                st.markdown(rep_data["report_markdown"])
                st.markdown("---")
                render_download_buttons(rep_data["report_markdown"], key_prefix=f"history_{selected_id}")
            else:
                st.error("Report ID not found.")

# ==========================================
# PAGE 7: ⚙️ SETTINGS & PROFILE AREA
# ==========================================
elif st.session_state["nav_page"] == "⚙️ Settings & Profile":
    st.markdown('<div class="saas-header">⚙️ System Settings & User Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-sub-header">Configure LLM providers, view system diagnostics, and manage session parameters</div>', unsafe_allow_html=True)

    col_set1, col_set2 = st.columns(2)

    with col_set1:
        st.markdown("### 👤 User Profile (Session)")
        st.text_input("User Name", value="Executive Strategist")
        st.text_input("Organization", value="Enterprise Decision Support Lab")
        st.text_input("Role", value="Chief Decision Officer (CDO)")
        st.text_input("Email", value="strategist@enterprise-ai.org", disabled=True)

    with col_set2:
        st.markdown("### ⚙️ LLM Provider & Temperature")
        st.selectbox("Active LLM Backend", ["gemini", "openai", "ollama", "mock"], index=["gemini", "openai", "ollama", "mock"].index(llm_provider), disabled=True)
        st.slider("Model Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
        st.text_input("Vector Database Path", value=str(db_manager.persist_dir), disabled=True)

    st.markdown("---")
    st.markdown("### 🛠️ System Diagnostics")
    st.json({
        "status": "OPERATIONAL",
        "llm_provider": llm_provider,
        "chromadb_chunks": doc_count,
        "sqlite_reports": len(get_all_reports()),
        "rag_isolation_status": "ENFORCED"
    })
