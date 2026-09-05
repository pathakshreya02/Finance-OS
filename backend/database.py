import sqlite3
import json
import os
from typing import List, Optional, Tuple
from models import TransactionRecord, ReconciliationSummary, AuditLogItem

DB_PATH = os.path.join(os.path.dirname(__file__), "finance_os.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            customer TEXT NOT NULL,
            order_amount REAL NOT NULL,
            created_at TEXT NOT NULL,
            payment_id TEXT,
            payment_amount REAL,
            payment_method TEXT,
            payment_status TEXT,
            gateway_fee REAL,
            settlement_id TEXT,
            settled_amount REAL,
            settlement_status TEXT,
            expected_amount REAL NOT NULL,
            received_amount REAL NOT NULL,
            difference REAL NOT NULL,
            exposure_amount REAL NOT NULL,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            rule_code TEXT NOT NULL,
            rule_description TEXT NOT NULL,
            is_resolved INTEGER NOT NULL DEFAULT 0,
            resolution_note TEXT,
            audit_history TEXT
        )
    """)

    # 2. Audit logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            rule_code TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)

    # 3. Reconciliation summary snapshot table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_summary (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_records INTEGER NOT NULL,
            matched_records INTEGER NOT NULL,
            exceptions_count INTEGER NOT NULL,
            match_rate REAL NOT NULL,
            total_unresolved_exposure REAL NOT NULL,
            status_breakdown TEXT NOT NULL,
            severity_breakdown TEXT NOT NULL,
            exposure_by_status TEXT NOT NULL,
            method_breakdown TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def save_reconciliation_batch(
    transactions: List[TransactionRecord], 
    summary: ReconciliationSummary, 
    audit_logs: List[AuditLogItem]
):
    """Atomically replaces current transactions, summary, and stores audit logs."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Clear previous transaction snapshot
        cursor.execute("DELETE FROM transactions")
        
        # Insert all transactions
        for t in transactions:
            cursor.execute("""
                INSERT INTO transactions (
                    id, order_id, customer, order_amount, created_at,
                    payment_id, payment_amount, payment_method, payment_status, gateway_fee,
                    settlement_id, settled_amount, settlement_status,
                    expected_amount, received_amount, difference, exposure_amount,
                    status, severity, rule_code, rule_description,
                    is_resolved, resolution_note, audit_history
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.id, t.order_id, t.customer, t.order_amount, t.created_at,
                t.payment_id, t.payment_amount, t.payment_method, t.payment_status, t.gateway_fee,
                t.settlement_id, t.settled_amount, t.settlement_status,
                t.expected_amount, t.received_amount, t.difference, t.exposure_amount,
                t.status, t.severity, t.rule_code, t.rule_description,
                1 if t.is_resolved else 0, t.resolution_note, json.dumps(t.audit_history)
            ))

        # Upsert summary
        cursor.execute("""
            INSERT INTO reconciliation_summary (
                id, total_records, matched_records, exceptions_count, match_rate,
                total_unresolved_exposure, status_breakdown, severity_breakdown,
                exposure_by_status, method_breakdown, last_updated
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                total_records=excluded.total_records,
                matched_records=excluded.matched_records,
                exceptions_count=excluded.exceptions_count,
                match_rate=excluded.match_rate,
                total_unresolved_exposure=excluded.total_unresolved_exposure,
                status_breakdown=excluded.status_breakdown,
                severity_breakdown=excluded.severity_breakdown,
                exposure_by_status=excluded.exposure_by_status,
                method_breakdown=excluded.method_breakdown,
                last_updated=excluded.last_updated
        """, (
            summary.total_records, summary.matched_records, summary.exceptions_count, summary.match_rate,
            summary.total_unresolved_exposure, json.dumps(summary.status_breakdown),
            json.dumps(summary.severity_breakdown), json.dumps(summary.exposure_by_status),
            json.dumps(summary.method_breakdown), summary.last_updated
        ))

        # Insert audit logs if not already existing
        for log in audit_logs:
            cursor.execute("""
                INSERT OR IGNORE INTO audit_logs (
                    id, timestamp, entity_id, action, actor, rule_code, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log.id, log.timestamp, log.entity_id, log.action, log.actor, log.rule_code, log.details
            ))

        conn.commit()
    finally:
        conn.close()

def update_transaction_resolution(
    transaction_id: str, 
    resolution_note: str, 
    audit_history: List[str],
    audit_log: AuditLogItem
) -> bool:
    """Updates a single transaction's resolution state and logs audit record."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE transactions
            SET is_resolved = 1,
                resolution_note = ?,
                audit_history = ?
            WHERE id = ? OR order_id = ?
        """, (resolution_note, json.dumps(audit_history), transaction_id, transaction_id))
        
        if cursor.rowcount > 0:
            cursor.execute("""
                INSERT OR IGNORE INTO audit_logs (
                    id, timestamp, entity_id, action, actor, rule_code, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_log.id, audit_log.timestamp, audit_log.entity_id, 
                audit_log.action, audit_log.actor, audit_log.rule_code, audit_log.details
            ))
            conn.commit()
            return True
        return False
    finally:
        conn.close()

def load_stored_reconciliation() -> Tuple[List[TransactionRecord], Optional[ReconciliationSummary], List[AuditLogItem]]:
    """Loads current state from SQLite if present."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    transactions: List[TransactionRecord] = []
    summary: Optional[ReconciliationSummary] = None
    audit_logs: List[AuditLogItem] = []

    try:
        # Load transactions
        cursor.execute("SELECT * FROM transactions")
        rows = cursor.fetchall()
        for r in rows:
            tx = TransactionRecord(
                id=r["id"],
                order_id=r["order_id"],
                customer=r["customer"],
                order_amount=r["order_amount"],
                created_at=r["created_at"],
                payment_id=r["payment_id"],
                payment_amount=r["payment_amount"],
                payment_method=r["payment_method"],
                payment_status=r["payment_status"],
                gateway_fee=r["gateway_fee"],
                settlement_id=r["settlement_id"],
                settled_amount=r["settled_amount"],
                settlement_status=r["settlement_status"],
                expected_amount=r["expected_amount"],
                received_amount=r["received_amount"],
                difference=r["difference"],
                exposure_amount=r["exposure_amount"],
                status=r["status"],
                severity=r["severity"],
                rule_code=r["rule_code"],
                rule_description=r["rule_description"],
                is_resolved=bool(r["is_resolved"]),
                resolution_note=r["resolution_note"],
                audit_history=json.loads(r["audit_history"] or "[]")
            )
            transactions.append(tx)

        # Load summary
        cursor.execute("SELECT * FROM reconciliation_summary WHERE id = 1")
        sum_row = cursor.fetchone()
        if sum_row:
            summary = ReconciliationSummary(
                total_records=sum_row["total_records"],
                matched_records=sum_row["matched_records"],
                exceptions_count=sum_row["exceptions_count"],
                match_rate=sum_row["match_rate"],
                total_unresolved_exposure=sum_row["total_unresolved_exposure"],
                status_breakdown=json.loads(sum_row["status_breakdown"]),
                severity_breakdown=json.loads(sum_row["severity_breakdown"]),
                exposure_by_status=json.loads(sum_row["exposure_by_status"]),
                method_breakdown=json.loads(sum_row["method_breakdown"]),
                last_updated=sum_row["last_updated"]
            )

        # Load audit logs
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
        log_rows = cursor.fetchall()
        for lr in log_rows:
            audit_logs.append(AuditLogItem(
                id=lr["id"],
                timestamp=lr["timestamp"],
                entity_id=lr["entity_id"],
                action=lr["action"],
                actor=lr["actor"],
                rule_code=lr["rule_code"],
                details=lr["details"]
            ))

        return transactions, summary, audit_logs
    finally:
        conn.close()
