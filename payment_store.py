"""Simple SQLite-backed payment store for SmartLearn.
Provides minimal persistence for payment upgrade flow.
In production, consider a full ORM and user authentication.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os

DB_PATH = Path(os.getenv('PAYMENTS_DB_PATH', 'payments.db'))

PAYMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    amount REAL NOT NULL,
    session_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    transaction_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    raw_payload TEXT
);
"""

STATUS_COMPLETED = 'completed'
STATUS_PENDING = 'pending'
STATUS_FAILED = 'failed'


def _connect():
    return sqlite3.connect(DB_PATH)


def init_payment_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(PAYMENT_SCHEMA)
        conn.commit()


def create_payment(reference: str, email: str, amount: float, session_id: str):
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO payments(reference,email,amount,session_id,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (reference, email, amount, session_id, STATUS_PENDING, now, now)
        )
        conn.commit()


def update_payment_status(reference: str, status: str, transaction_id: Optional[str] = None, raw_payload: Optional[Dict[str, Any]] = None):
    now = datetime.utcnow().isoformat()
    payload_json = json.dumps(raw_payload) if raw_payload else None
    with _connect() as conn:
        conn.execute(
            "UPDATE payments SET status=?, transaction_id=COALESCE(?, transaction_id), raw_payload=COALESCE(?, raw_payload), updated_at=? WHERE reference=?",
            (status, transaction_id, payload_json, now, reference)
        )
        conn.commit()


def get_payment(reference: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute("SELECT reference,email,amount,session_id,status,transaction_id,created_at,updated_at FROM payments WHERE reference=?", (reference,))
        row = cur.fetchone()
        if not row:
            return None
        keys = ["reference","email","amount","session_id","status","transaction_id","created_at","updated_at"]
        return dict(zip(keys, row))


def list_payments(limit: int = 50) -> List[Dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute("SELECT reference,email,amount,session_id,status,transaction_id,created_at,updated_at FROM payments ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        keys = ["reference","email","amount","session_id","status","transaction_id","created_at","updated_at"]
        return [dict(zip(keys, r)) for r in rows]
