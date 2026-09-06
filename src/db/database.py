import sqlite3
import json
from datetime import datetime
from pathlib import Path
from src.config import SQLITE_DB_PATH

def init_db():
    """Initialize SQLite tables for queries, reports, agent logs, and human feedback."""
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cursor = conn.cursor()

    # Queries Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_text TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id INTEGER,
        query_text TEXT,
        report_markdown TEXT,
        report_json TEXT,
        confidence_score REAL,
        fact_check_status TEXT,
        pdf_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(query_id) REFERENCES queries(id)
    );
    """)

    # Agent Execution Activity Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id INTEGER,
        agent_name TEXT,
        status TEXT,
        output_summary TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Human-in-the-Loop Approvals
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS human_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id INTEGER,
        recommendation_draft TEXT,
        human_decision TEXT, -- 'approved', 'modified', 'rejected'
        feedback_comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

def save_query(query_text: str) -> int:
    """Saves a new business query into DB and returns query_id."""
    init_db()
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO queries (query_text, status) VALUES (?, ?)", (query_text, "processing"))
    query_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return query_id

def log_agent_activity(query_id: int, agent_name: str, status: str, output_summary: str):
    """Logs an agent activity step to DB."""
    init_db()
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO agent_logs (query_id, agent_name, status, output_summary) VALUES (?, ?, ?, ?)",
        (query_id, agent_name, status, output_summary)
    )
    conn.commit()
    conn.close()

def save_report(query_id: int, query_text: str, report_markdown: str, report_json: dict, confidence_score: float, fact_check_status: str, pdf_path: str = "") -> int:
    """Saves a generated business report into DB."""
    init_db()
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO reports (query_id, query_text, report_markdown, report_json, confidence_score, fact_check_status, pdf_path)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (query_id, query_text, report_markdown, json.dumps(report_json), confidence_score, fact_check_status, pdf_path)
    )
    report_id = cursor.lastrowid
    
    # Update query status to completed
    cursor.execute("UPDATE queries SET status = 'completed' WHERE id = ?", (query_id,))
    conn.commit()
    conn.close()
    return report_id

def get_all_reports():
    """Fetches list of all historical business reports."""
    init_db()
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, query_text, confidence_score, fact_check_status, created_at, pdf_path FROM reports ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_report_by_id(report_id: int):
    """Fetches full report by report ID."""
    init_db()
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        if data.get("report_json"):
            data["report_json"] = json.loads(data["report_json"])
        return data
    return None

def get_agent_logs(query_id: int):
    """Fetches activity logs for a specific query."""
    init_db()
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT agent_name, status, output_summary, timestamp FROM agent_logs WHERE query_id = ? ORDER BY id ASC", (query_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# Initialize DB on module load
init_db()
