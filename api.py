import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.config import UPLOAD_DIR
from src.db.database import save_query, get_all_reports, get_report_by_id, get_agent_logs, save_report
from src.rag.ingestion import load_file, chunk_documents
from src.rag.vectorstore import VectorDBManager
from src.graph.workflow import run_agent_workflow
from src.tools.what_if_tool import run_what_if_simulation
from src.reports.pdf_generator import generate_pdf_report

app = FastAPI(
    title="AI Business Research & Decision Support Agent API",
    description="Enterprise Multi-Agent API powered by LangGraph, RAG, ChromaDB, and Fact Verification.",
    version="1.0.0"
)

class AnalyzeRequest(BaseModel):
    query: str
    llm_provider: Optional[str] = "gemini"

class WhatIfRequest(BaseModel):
    base_price: float = 75000.0
    price_change_percent: float = -10.0
    unit_cost: float = 58000.0
    base_volume: int = 15000

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AI Business Research & Decision Support Agent API",
        "endpoints": [
            "/api/analyze",
            "/api/documents/upload",
            "/api/what-if",
            "/api/reports",
            "/api/reports/{id}",
            "/api/reports/{id}/pdf"
        ]
    }

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a PDF, DOCX, CSV, or TXT document and indexes it into ChromaDB vector database."""
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())

        raw_docs = load_file(file_path)
        chunks = chunk_documents(raw_docs)
        
        db_manager = VectorDBManager()
        db_manager.add_documents(chunks)

        return {
            "status": "success",
            "filename": file.filename,
            "chunks_indexed": len(chunks),
            "total_documents_in_db": db_manager.get_document_count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.post("/api/analyze")
def analyze_business_inquiry(req: AnalyzeRequest):
    """Triggers the full 6-Agent LangGraph workflow for a business decision query."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    query_id = save_query(req.query)
    final_state = run_agent_workflow(req.query, query_id=query_id, llm_provider=req.llm_provider)

    # Generate PDF Report
    pdf_filename = f"report_query_{query_id}.pdf"
    pdf_path = generate_pdf_report(final_state.get("report_markdown", ""), filename=pdf_filename)

    return {
        "status": "completed",
        "query_id": query_id,
        "confidence_score": final_state.get("confidence_score"),
        "fact_check_status": final_state.get("fact_check_audit", {}).get("overall_status"),
        "activity_logs": final_state.get("activity_logs"),
        "report_markdown": final_state.get("report_markdown"),
        "report_json": final_state.get("report_json"),
        "pdf_path": pdf_path
    }

@app.post("/api/what-if")
def calculate_what_if_scenario(req: WhatIfRequest):
    """Calculates financial sensitivity analysis when price or cost structure changes."""
    return run_what_if_simulation(
        base_price=req.base_price,
        price_change_percent=req.price_change_percent,
        unit_cost=req.unit_cost,
        base_volume=req.base_volume
    )

@app.get("/api/reports")
def list_reports():
    """Fetches list of all historical business decision reports."""
    return get_all_reports()

@app.get("/api/reports/{report_id}")
def get_report(report_id: int):
    """Fetches a specific report by ID."""
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report

@app.get("/api/reports/{report_id}/pdf")
def download_pdf_report(report_id: int):
    """Downloads the generated PDF report."""
    report = get_report_by_id(report_id)
    if not report or not report.get("pdf_path"):
        # Attempt generating on the fly
        if report and report.get("report_markdown"):
            pdf_path = generate_pdf_report(report["report_markdown"], filename=f"report_{report_id}.pdf")
            if pdf_path and os.path.exists(pdf_path):
                return FileResponse(pdf_path, media_type="application/pdf", filename=f"business_report_{report_id}.pdf")
        raise HTTPException(status_code=404, detail="PDF report not available.")
    
    pdf_path = report["pdf_path"]
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"business_report_{report_id}.pdf")
    raise HTTPException(status_code=404, detail="PDF file missing from disk.")

@app.get("/api/logs/{query_id}")
def get_logs(query_id: int):
    """Fetches real-time agent execution activity logs for a query."""
    return get_agent_logs(query_id)
