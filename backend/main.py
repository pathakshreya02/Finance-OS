import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import pandas as pd
import io
from typing import Optional, List

from models import (
    TransactionRecord,
    ReconciliationSummary,
    InvestigationRequest,
    InvestigationResponse,
    ChatRequest,
    ChatResponse,
    CfoBriefResponse,
    ResolveRequest,
    AuditLogItem,
    ActionDispatchRequest,
    ActionDispatchResponse,
    FeeAnalyticsSummary,
    WebhookSimulationRequest,
    WebhookSimulationResponse
)
from reconciliation_engine import engine
from synthetic_data import generate_synthetic_finance_data
from ai_agent import ai_agent

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes with database state if present, else seeds with 150 records."""
    if not engine.transactions or not engine.last_summary:
        orders_df, payments_df, settlements_df = generate_synthetic_finance_data(num_records=150, seed=42)
        engine.reconcile(orders_df, payments_df, settlements_df)
        print(f"Startup: Reconciled {len(engine.transactions)} records from fresh seed. Match rate: {engine.last_summary.match_rate}%")
    else:
        print(f"Startup: Loaded {len(engine.transactions)} records from persistent database. Match rate: {engine.last_summary.match_rate}%")
    yield

app = FastAPI(
    title="DhanSetu — The Autonomous 3-Way Bridge for Payment Reconciliation API",
    description="Backend API for Razorpay Buildathon Track 04",
    version="3.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/reconcile/seed", response_model=ReconciliationSummary)
async def seed_data(count: int = Query(150, ge=50, le=500)):
    """Generate 100 to 500 synthetic records and run reconciliation loop."""
    orders_df, payments_df, settlements_df = generate_synthetic_finance_data(num_records=count, seed=42)
    _, summary = engine.reconcile(orders_df, payments_df, settlements_df)
    return summary

@app.post("/api/reconcile/upload", response_model=ReconciliationSummary)
async def upload_csvs(
    orders_file: UploadFile = File(...),
    payments_file: UploadFile = File(...),
    settlements_file: Optional[UploadFile] = File(None)
):
    """Upload custom Orders and Payments CSV files for reconciliation."""
    try:
        orders_content = await orders_file.read()
        orders_df = pd.read_csv(io.BytesIO(orders_content))
        
        payments_content = await payments_file.read()
        payments_df = pd.read_csv(io.BytesIO(payments_content))
        
        settlements_df = None
        if settlements_file:
            settlements_content = await settlements_file.read()
            settlements_df = pd.read_csv(io.BytesIO(settlements_content))
            
        _, summary = engine.reconcile(orders_df, payments_df, settlements_df)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV files: {str(e)}")

@app.get("/api/reconcile/summary", response_model=ReconciliationSummary)
async def get_summary():
    """Retrieve current financial metrics and match rates."""
    if not engine.last_summary:
        raise HTTPException(status_code=404, detail="No reconciliation data found.")
    return engine.last_summary

@app.get("/api/reconcile/transactions")
async def get_transactions(
    search: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 150
):
    """Filterable and searchable transaction list."""
    txs = engine.transactions
    
    if search:
        s = search.strip().lower()
        txs = [
            t for t in txs 
            if s in t.order_id.lower() 
            or s in t.customer.lower() 
            or (t.payment_id and s in t.payment_id.lower())
        ]
        
    if status and status != "ALL":
        txs = [t for t in txs if t.status == status]
        
    if severity and severity != "ALL":
        txs = [t for t in txs if t.severity == severity]
        
    if is_resolved is not None:
        txs = [t for t in txs if t.is_resolved == is_resolved]

    total = len(txs)
    paginated = txs[skip : skip + limit]
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": paginated
    }

@app.get("/api/reconcile/transactions/{tx_id}", response_model=TransactionRecord)
async def get_transaction(tx_id: str):
    """Deep-dive into a single transaction by ID or order_id."""
    for t in engine.transactions:
        if t.id == tx_id or t.order_id == tx_id:
            return t
    raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found.")

@app.post("/api/reconcile/resolve", response_model=TransactionRecord)
async def resolve_transaction(req: ResolveRequest):
    """Manually mark an exception as resolved with an operator note."""
    updated = engine.resolve_exception(req.transaction_id, req.resolution_note)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return updated

@app.post("/api/ai/investigate", response_model=InvestigationResponse)
async def ai_investigate(req: InvestigationRequest):
    """AI investigation for a specific transaction."""
    target_tx = None
    for t in engine.transactions:
        if t.id == req.transaction_id or t.order_id == req.transaction_id:
            target_tx = t
            break
            
    if not target_tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
        
    investigation = ai_agent.investigate_transaction(target_tx)
    return investigation

@app.post("/api/ai/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    """Interactive chat with Autonomous AI Finance Controller grounded on current data."""
    if not engine.last_summary:
        raise HTTPException(status_code=400, detail="Reconciliation data is empty.")
        
    top_exceptions = [t for t in engine.transactions if t.status != "MATCHED" and not t.is_resolved]
    top_exceptions.sort(key=lambda x: x.exposure_amount, reverse=True)
    
    focus_order = None
    if req.focus_order_id:
        for t in engine.transactions:
            if t.order_id == req.focus_order_id:
                focus_order = t
                break
                
    response = ai_agent.chat_with_agent(
        messages=req.messages,
        summary=engine.last_summary,
        top_exceptions=top_exceptions,
        focus_order=focus_order
    )
    return response

@app.post("/api/ai/cfo-brief", response_model=CfoBriefResponse)
async def ai_cfo_brief():
    """Generates an executive CFO Risk & Strategic Action Brief."""
    if not engine.last_summary:
        raise HTTPException(status_code=400, detail="Reconciliation data is empty.")
        
    top_exceptions = [t for t in engine.transactions if t.status != "MATCHED" and not t.is_resolved]
    top_exceptions.sort(key=lambda x: x.exposure_amount, reverse=True)
    
    brief = ai_agent.generate_cfo_brief(engine.last_summary, top_exceptions)
    return brief

@app.get("/api/audit-trail", response_model=List[AuditLogItem])
async def get_audit_trail():
    """Returns the immutable compliance audit trail."""
    return engine.audit_logs

@app.get("/api/sample-csv/orders", response_class=PlainTextResponse)
async def get_sample_orders():
    """Download sample orders CSV."""
    df, _, _ = generate_synthetic_finance_data(num_records=20, seed=101)
    return df.to_csv(index=False)

@app.get("/api/sample-csv/payments", response_class=PlainTextResponse)
async def get_sample_payments():
    """Download sample payments CSV."""
    _, df, _ = generate_synthetic_finance_data(num_records=20, seed=101)
    return df.to_csv(index=False)

@app.get("/api/reconcile/export", response_class=PlainTextResponse)
async def export_transactions():
    """Export current reconciled transactions with resolution status to CSV."""
    if not engine.transactions:
        raise HTTPException(status_code=404, detail="No transactions to export.")
    
    rows = []
    for t in engine.transactions:
        rows.append({
            "Transaction ID": t.id,
            "Order ID": t.order_id,
            "Customer": t.customer,
            "Created At": t.created_at,
            "Order Amount": t.order_amount,
            "Payment ID": t.payment_id or "",
            "Payment Amount": t.payment_amount or 0.0,
            "Payment Method": t.payment_method,
            "Gateway Status": t.payment_status,
            "Gateway Fee": t.gateway_fee or 0.0,
            "Settlement ID": t.settlement_id or "",
            "Settled Amount": t.settled_amount or 0.0,
            "Difference": t.difference,
            "Exposure Amount": t.exposure_amount,
            "Status": t.status,
            "Severity": t.severity,
            "Rule Code": t.rule_code,
            "Rule Description": t.rule_description,
            "Is Resolved": "YES" if t.is_resolved else "NO",
            "Resolution Note": t.resolution_note or ""
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)

@app.post("/api/actions/dispatch", response_model=ActionDispatchResponse)
async def dispatch_action(req: ActionDispatchRequest):
    """Execute an agentic self-healing action on a transaction."""
    if not engine.transactions:
        raise HTTPException(status_code=400, detail="No reconciliation data available.")
    result = engine.dispatch_action(
        transaction_id=req.transaction_id,
        action_type=req.action_type,
        note=req.note,
        amount=req.amount
    )
    if not result.success and "not found" in result.message:
        raise HTTPException(status_code=404, detail=result.message)
    return result

@app.get("/api/reconcile/fee-analytics", response_model=FeeAnalyticsSummary)
async def get_fee_analytics():
    """Retrieve MDR fee leakage and GST ITC reconciliation summary."""
    if not engine.transactions:
        raise HTTPException(status_code=404, detail="No reconciliation data found.")
    return engine.get_fee_analytics()

@app.post("/api/webhooks/simulate", response_model=WebhookSimulationResponse)
async def simulate_webhook(req: WebhookSimulationRequest):
    """Simulate a live Razorpay payment/settlement webhook event for real-time ingestion demo."""
    import uuid
    rec, summary = engine.ingest_event(
        event_type=req.event_type,
        amount=req.amount or 1500.0,
        customer=req.customer or "Live Webhook User",
        payment_method=req.payment_method or "UPI",
        simulate_discrepancy=req.simulate_discrepancy or "NONE"
    )
    return WebhookSimulationResponse(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        event_type=req.event_type,
        reconciled_transaction=rec,
        summary=summary,
        message=f"Live {req.event_type} event ingested and reconciled. Status: {rec.status}."
    )

@app.post("/api/webhooks/razorpay")
async def razorpay_webhook(request_body: dict):
    """Production Razorpay webhook receiver with HMAC SHA256 signature validation (stub)."""
    import hmac, hashlib
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    # In production: validate X-Razorpay-Signature header against HMAC SHA256 of body
    event_type = request_body.get("event", "payment.captured")
    payload = request_body.get("payload", {})
    amount_raw = payload.get("payment", {}).get("entity", {}).get("amount", 150000)  # paise
    amount = round(amount_raw / 100, 2)  # convert to rupees
    customer = payload.get("payment", {}).get("entity", {}).get("description", "Razorpay Webhook Customer")
    method = payload.get("payment", {}).get("entity", {}).get("method", "upi").replace("upi", "UPI").replace("card", "Credit Card")
    rec, summary = engine.ingest_event(
        event_type=event_type,
        amount=amount,
        customer=customer,
        payment_method=method
    )
    return {"status": "acknowledged", "reconciled_order": rec.order_id, "reconciliation_status": rec.status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
