import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from reconciliation_engine import ReconciliationEngine
from models import TransactionRecord
from ai_agent import AiFinanceAgent
from main import app

@pytest.fixture
def clean_engine():
    """Returns a fresh ReconciliationEngine instance without interfering with db."""
    eng = ReconciliationEngine()
    eng.transactions = []
    eng.audit_logs = []
    eng.last_summary = None
    return eng

def test_matched_transaction(clean_engine):
    orders = pd.DataFrame([{
        "order_id": "ORD_TEST_1",
        "customer": "Test User",
        "order_amount": 1000.0,
        "payment_method": "UPI",
        "created_at": "2026-03-01 10:00:00"
    }])
    payments = pd.DataFrame([{
        "payment_id": "pay_test_1",
        "order_id": "ORD_TEST_1",
        "payment_amount": 1000.0,
        "payment_method": "UPI",
        "status": "SUCCESS",
        "gateway_fee": 5.0,
        "timestamp": "2026-03-01 10:00:10"
    }])
    settlements = pd.DataFrame([{
        "settlement_id": "set_test_1",
        "payment_id": "pay_test_1",
        "order_id": "ORD_TEST_1",
        "settled_amount": 995.0,
        "bank_status": "SETTLED"
    }])

    txs, summary = clean_engine.reconcile(orders, payments, settlements)
    assert len(txs) == 1
    assert txs[0].status == "MATCHED"
    assert txs[0].severity == "NONE"
    assert txs[0].exposure_amount == 0.0
    assert summary.matched_records == 1
    assert summary.exceptions_count == 0
    assert summary.match_rate == 100.0

def test_missing_payment(clean_engine):
    orders = pd.DataFrame([{
        "order_id": "ORD_TEST_MISSING",
        "customer": "Abandoned User",
        "order_amount": 2500.0,
        "payment_method": "UPI",
        "created_at": "2026-03-01 11:00:00"
    }])
    payments = pd.DataFrame()
    settlements = pd.DataFrame()

    txs, summary = clean_engine.reconcile(orders, payments, settlements)
    assert len(txs) == 1
    assert txs[0].status == "MISSING_PAYMENT"
    assert txs[0].severity == "MEDIUM"
    assert txs[0].exposure_amount == 2500.0
    assert summary.exceptions_count == 1
    assert summary.match_rate == 0.0

def test_amount_mismatch(clean_engine):
    orders = pd.DataFrame([{
        "order_id": "ORD_TEST_MISMATCH",
        "customer": "Mismatch User",
        "order_amount": 1500.0,
        "payment_method": "Credit Card",
        "created_at": "2026-03-01 12:00:00"
    }])
    payments = pd.DataFrame([{
        "payment_id": "pay_test_mismatch",
        "order_id": "ORD_TEST_MISMATCH",
        "payment_amount": 1200.0, # 300 short
        "payment_method": "Credit Card",
        "status": "SUCCESS",
        "gateway_fee": 28.32,
        "timestamp": "2026-03-01 12:01:00"
    }])
    
    txs, summary = clean_engine.reconcile(orders, payments, pd.DataFrame())
    assert len(txs) == 1
    assert txs[0].status == "AMOUNT_MISMATCH"
    assert txs[0].exposure_amount == 300.0
    assert txs[0].difference == -300.0

def test_duplicate_payment(clean_engine):
    orders = pd.DataFrame([{
        "order_id": "ORD_TEST_DUP",
        "customer": "Duplicate User",
        "order_amount": 500.0,
        "payment_method": "UPI",
        "created_at": "2026-03-01 13:00:00"
    }])
    payments = pd.DataFrame([
        {
            "payment_id": "pay_dup_1",
            "order_id": "ORD_TEST_DUP",
            "payment_amount": 500.0,
            "payment_method": "UPI",
            "status": "SUCCESS",
            "gateway_fee": 2.5,
            "timestamp": "2026-03-01 13:00:05"
        },
        {
            "payment_id": "pay_dup_2",
            "order_id": "ORD_TEST_DUP",
            "payment_amount": 500.0,
            "payment_method": "UPI",
            "status": "SUCCESS",
            "gateway_fee": 2.5,
            "timestamp": "2026-03-01 13:00:10"
        }
    ])

    txs, summary = clean_engine.reconcile(orders, payments, pd.DataFrame())
    assert len(txs) == 1
    assert txs[0].status == "DUPLICATE_PAYMENT"
    assert txs[0].exposure_amount == 500.0 # Customer double-charged

def test_unknown_payment(clean_engine):
    orders = pd.DataFrame()
    payments = pd.DataFrame([{
        "payment_id": "pay_orphan_99",
        "order_id": "ORD_UNKNOWN_99",
        "payment_amount": 800.0,
        "payment_method": "Netbanking",
        "status": "SUCCESS",
        "gateway_fee": 18.88,
        "timestamp": "2026-03-01 14:00:00"
    }])

    txs, summary = clean_engine.reconcile(orders, payments, pd.DataFrame())
    assert len(txs) == 1
    assert txs[0].status == "UNKNOWN_PAYMENT"
    assert txs[0].order_id == "ORD_UNKNOWN_99"
    assert txs[0].received_amount == 800.0
    assert txs[0].exposure_amount == 800.0

def test_settlement_mismatch(clean_engine):
    orders = pd.DataFrame([{
        "order_id": "ORD_TEST_SETTLE",
        "customer": "Settle User",
        "order_amount": 2000.0,
        "payment_method": "UPI",
        "created_at": "2026-03-01 15:00:00"
    }])
    payments = pd.DataFrame([{
        "payment_id": "pay_settle_1",
        "order_id": "ORD_TEST_SETTLE",
        "payment_amount": 2000.0,
        "payment_method": "UPI",
        "status": "SUCCESS",
        "gateway_fee": 10.0,
        "timestamp": "2026-03-01 15:00:05"
    }])
    settlements = pd.DataFrame([{
        "settlement_id": "set_settle_1",
        "payment_id": "pay_settle_1",
        "order_id": "ORD_TEST_SETTLE",
        "settled_amount": 1600.0, # Expected: 2000 - 10 = 1990. Delta = 390.
        "bank_status": "SETTLED"
    }])

    txs, summary = clean_engine.reconcile(orders, payments, settlements)
    assert len(txs) == 1
    assert txs[0].status == "SETTLEMENT_MISMATCH"
    assert txs[0].exposure_amount == 390.0

def test_resolution_and_exposure_recalc(clean_engine):
    orders = pd.DataFrame([{
        "order_id": "ORD_RESOLVE_ME",
        "customer": "Fixable User",
        "order_amount": 1000.0,
        "payment_method": "UPI",
        "created_at": "2026-03-01 16:00:00"
    }])
    payments = pd.DataFrame()
    clean_engine.reconcile(orders, payments)
    
    assert clean_engine.last_summary.total_unresolved_exposure == 1000.0
    
    resolved = clean_engine.resolve_exception("ORD_RESOLVE_ME", "Order was cancelled by customer, refunded.")
    assert resolved is not None
    assert resolved.is_resolved is True
    assert clean_engine.last_summary.total_unresolved_exposure == 0.0

def test_ai_fallback_heuristics():
    agent = AiFinanceAgent()
    tx = TransactionRecord(
        id="TX-TEST-001",
        order_id="ORD-TEST-001",
        customer="Test Heuristic",
        order_amount=1200.0,
        created_at="2026-03-01 17:00:00",
        payment_id=None,
        payment_amount=None,
        payment_method="UPI",
        payment_status="NONE",
        gateway_fee=0.0,
        settlement_id=None,
        settled_amount=None,
        settlement_status=None,
        expected_amount=1200.0,
        received_amount=0.0,
        difference=-1200.0,
        exposure_amount=1200.0,
        status="MISSING_PAYMENT",
        severity="MEDIUM",
        rule_code="RULE_02_MISSING_PAYMENT",
        rule_description="Order exists without payment capture event.",
        is_resolved=False,
        resolution_note=None,
        audit_history=[]
    )
    res = agent._heuristic_investigation(tx)
    assert res.transaction_id == "TX-TEST-001"
    assert len(res.evidence_chain) > 0
    assert "Dr." in res.journal_entry and "Cr." in res.journal_entry
    assert res.root_cause != ""

def test_fastapi_client():
    client = TestClient(app)
    
    summary_res = client.get("/api/reconcile/summary")
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert "match_rate" in data
    assert "total_records" in data

    tx_res = client.get("/api/reconcile/transactions?limit=10")
    assert tx_res.status_code == 200
    tx_data = tx_res.json()
    assert "items" in tx_data
    assert len(tx_data["items"]) <= 10

    export_res = client.get("/api/reconcile/export")
    assert export_res.status_code == 200
    assert "Order ID" in export_res.text
    assert "Transaction ID" in export_res.text

    sample_orders = client.get("/api/sample-csv/orders")
    assert sample_orders.status_code == 200
    assert "order_id" in sample_orders.text
