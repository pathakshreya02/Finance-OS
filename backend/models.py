from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class TransactionRecord(BaseModel):
    id: str
    order_id: str
    customer: str
    order_amount: float
    created_at: str
    payment_id: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_method: Optional[str] = "UPI"
    payment_status: Optional[str] = "SUCCESS"
    gateway_fee: Optional[float] = 0.0
    settlement_id: Optional[str] = None
    settled_amount: Optional[float] = None
    settlement_status: Optional[str] = "SETTLED"
    expected_amount: float
    received_amount: float
    difference: float
    exposure_amount: float
    status: str  # MATCHED, MISSING_PAYMENT, AMOUNT_MISMATCH, DUPLICATE_PAYMENT, UNKNOWN_PAYMENT, SETTLEMENT_MISMATCH
    severity: str  # NONE, LOW, MEDIUM, HIGH
    rule_code: str
    rule_description: str
    is_resolved: bool = False
    resolution_note: Optional[str] = None
    audit_history: List[str] = Field(default_factory=list)

class ReconciliationSummary(BaseModel):
    total_records: int
    matched_records: int
    exceptions_count: int
    match_rate: float
    total_unresolved_exposure: float
    status_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
    exposure_by_status: Dict[str, float]
    method_breakdown: Dict[str, Dict[str, int]]
    last_updated: str

class InvestigationRequest(BaseModel):
    transaction_id: str

class InvestigationResponse(BaseModel):
    transaction_id: str
    order_id: str
    status: str
    severity: str
    root_cause: str
    evidence_chain: List[str]
    financial_impact: str
    recommended_action: str
    journal_entry: str
    urgency: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    focus_order_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    referenced_orders: List[str] = Field(default_factory=list)

class CfoBriefResponse(BaseModel):
    executive_summary: str
    financial_health_score: str
    match_rate_analysis: str
    unresolved_leakage_breakdown: str
    top_vulnerabilities: List[str]
    strategic_action_items: List[Dict[str, str]]
    generated_at: str

class ResolveRequest(BaseModel):
    transaction_id: str
    resolution_note: str

class AuditLogItem(BaseModel):
    id: str
    timestamp: str
    entity_id: str
    action: str
    actor: str
    rule_code: str
    details: str

class ActionDispatchRequest(BaseModel):
    transaction_id: str
    action_type: str  # REFUND_DISPATCH, DISPUTE_EMAIL, ERP_JOURNAL_EXPORT
    note: Optional[str] = None
    amount: Optional[float] = None

class ActionDispatchResponse(BaseModel):
    success: bool
    action_type: str
    transaction_id: str
    message: str
    updated_record: Optional[TransactionRecord] = None
    audit_item: Optional[AuditLogItem] = None
    artifacts: Dict[str, Any] = Field(default_factory=dict)

class FeeBreakdownItem(BaseModel):
    method: str
    tx_count: int
    volume: float
    actual_fee: float
    expected_fee: float
    leakage: float
    effective_rate_pct: float
    gst_itc_claimable: float

class FeeAnalyticsSummary(BaseModel):
    total_volume: float
    total_actual_fees: float
    total_expected_fees: float
    total_leakage: float
    total_gst_itc: float
    method_breakdown: List[FeeBreakdownItem]
    generated_at: str

class WebhookSimulationRequest(BaseModel):
    event_type: str = "payment.captured"
    amount: Optional[float] = 1500.0
    customer: Optional[str] = "Live Webhook User"
    payment_method: Optional[str] = "UPI"
    simulate_discrepancy: Optional[str] = "NONE"  # NONE, AMOUNT_MISMATCH, MISSING_PAYMENT

class WebhookSimulationResponse(BaseModel):
    event_id: str
    event_type: str
    reconciled_transaction: TransactionRecord
    summary: ReconciliationSummary
    message: str

