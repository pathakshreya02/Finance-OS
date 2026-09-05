import os
import json
from dotenv import load_dotenv
from typing import List, Optional
from openai import OpenAI

from models import (
    TransactionRecord, 
    ReconciliationSummary, 
    InvestigationResponse, 
    ChatMessage, 
    ChatResponse, 
    CfoBriefResponse
)

# Load environment variables
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

class AiFinanceAgent:
    def __init__(self):
        self.model = "gpt-4o-mini"

    def investigate_transaction(self, tx: TransactionRecord) -> InvestigationResponse:
        """Deep root cause analysis for an exception transaction using OpenAI with fallback."""
        if not client or not openai_api_key:
            return self._heuristic_investigation(tx)

        system_prompt = (
            "You are an expert AI Finance Controller specializing in Razorpay payment gateway reconciliation, "
            "bank settlements, and ERP order matching. "
            "Analyze the provided transaction anomaly and return your response in JSON format with fields: "
            "root_cause, evidence_chain (list of strings), financial_impact, recommended_action, journal_entry, urgency."
        )

        user_content = f"""
Transaction Anomaly Details:
- Order ID: {tx.order_id}
- Customer: {tx.customer}
- Expected Amount: ₹{tx.expected_amount:,.2f}
- Gateway Payment ID: {tx.payment_id or 'NONE'}
- Gateway Captured Amount: ₹{tx.payment_amount:,.2f}
- Payment Method: {tx.payment_method}
- Gateway Status: {tx.payment_status}
- Gateway Fee: ₹{tx.gateway_fee:,.2f}
- Bank Settlement ID: {tx.settlement_id or 'NONE'}
- Bank Settled Amount: ₹{tx.settled_amount:,.2f}
- Discrepancy Difference: ₹{tx.difference:+,.2f}
- Unresolved Financial Exposure: ₹{tx.exposure_amount:,.2f}
- Anomaly Classification: {tx.status}
- Severity: {tx.severity}
- Rule Triggered: {tx.rule_code} - {tx.rule_description}
- Audit History:
{chr(10).join(f"  * {h}" for h in tx.audit_history)}

Provide a rigorous corporate finance investigation.
"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            data = json.loads(response.choices[0].message.content)
            return InvestigationResponse(
                transaction_id=tx.id,
                order_id=tx.order_id,
                status=tx.status,
                severity=tx.severity,
                root_cause=data.get("root_cause", "Anomaly identified by reconciliation engine."),
                evidence_chain=data.get("evidence_chain", ["Discrepancy verified against gateway logs."]),
                financial_impact=data.get("financial_impact", f"Unresolved exposure of ₹{tx.exposure_amount:,.2f}."),
                recommended_action=data.get("recommended_action", "Review gateway dashboard and notify operations."),
                journal_entry=data.get("journal_entry", "Dr. Reconciliation Suspense A/c | Cr. Bank Clearing A/c"),
                urgency=data.get("urgency", tx.severity)
            )
        except Exception as e:
            print(f"OpenAI error in investigate_transaction: {e}. Falling back to heuristic.")
            return self._heuristic_investigation(tx)

    def _heuristic_investigation(self, tx: TransactionRecord) -> InvestigationResponse:
        """Deterministic heuristic fallback if OpenAI is unavailable or rate-limited."""
        if tx.status == "MISSING_PAYMENT":
            root_cause = "Checkout abandonment or gateway webhook packet drop prior to payment capture."
            evidence = [
                f"Order {tx.order_id} recorded in ERP with amount ₹{tx.expected_amount:,.2f}.",
                "Zero Razorpay payment event associated with this order ID.",
                "Customer session terminated before entering 3D-Secure / OTP verification."
            ]
            impact = f"Unrealized revenue of ₹{tx.expected_amount:,.2f}. Inventory may be locked in cart reservation."
            action = "Trigger automated Razorpay Orders API status check. If uncaptured, void ERP order and release reserved inventory."
            journal = f"Dr. Accounts Receivable ₹0.00 | Cr. Unearned Revenue ₹{tx.expected_amount:,.2f} (Void Order)"
            urgency = "HIGH" if tx.expected_amount >= 3000 else "MEDIUM"

        elif tx.status == "DUPLICATE_PAYMENT":
            root_cause = "Customer connection timeout caused duplicate payment submission on checkout retry."
            evidence = [
                f"Single order {tx.order_id} mapped to multiple successful Razorpay payment IDs ({tx.payment_id}).",
                f"Total collected: ₹{tx.received_amount:,.2f} against expected ₹{tx.expected_amount:,.2f}.",
                f"Excess credit of ₹{tx.exposure_amount:,.2f} received in merchant settlement account."
            ]
            impact = f"Over-collection liability of ₹{tx.exposure_amount:,.2f}. High risk of customer chargeback fee (₹400+)."
            action = f"Initiate immediate auto-refund of ₹{tx.exposure_amount:,.2f} via Razorpay Refunds API to original payment instrument."
            journal = f"Dr. Cash in Transit / Gateway Clearing ₹{tx.exposure_amount:,.2f} | Cr. Customer Refund Payable ₹{tx.exposure_amount:,.2f}"
            urgency = "IMMEDIATE"

        elif tx.status == "AMOUNT_MISMATCH":
            root_cause = "Unauthorized promotional discount or partial payment capture discrepancy."
            evidence = [
                f"ERP expected ₹{tx.expected_amount:,.2f} but Razorpay captured ₹{tx.payment_amount:,.2f}.",
                f"Net variance of ₹{tx.difference:+,.2f} detected.",
                "Coupon code or tax calculation discrepancy between storefront checkout and gateway payload."
            ]
            impact = f"Gross margin leakage of ₹{tx.exposure_amount:,.2f} affecting order profitability."
            action = "Reconcile storefront discount ledger against Razorpay checkout payload. Adjust invoice or request supplementary payment."
            journal = f"Dr. Sales Discount Variance A/c ₹{tx.exposure_amount:,.2f} | Cr. Accounts Receivable ₹{tx.exposure_amount:,.2f}"
            urgency = tx.severity

        elif tx.status == "UNKNOWN_PAYMENT":
            root_cause = "Orphan gateway transaction. Direct checkout or API webhook failed to pass merchant Order ID."
            evidence = [
                f"Payment {tx.payment_id} of ₹{tx.received_amount:,.2f} received and settled to merchant bank.",
                f"Reference order ID '{tx.order_id}' does not exist in ERP database.",
                "Potential direct payment link generation without backend order linkage."
            ]
            impact = f"Unallocated cash asset of ₹{tx.exposure_amount:,.2f} sitting in clearing account with no customer liability matched."
            action = "Isolate payment in Suspense Account. Query Razorpay customer email/phone and match against open customer support tickets."
            journal = f"Dr. Bank Account ₹{tx.exposure_amount:,.2f} | Cr. Unallocated Suspense Liability ₹{tx.exposure_amount:,.2f}"
            urgency = "HIGH"

        elif tx.status == "SETTLEMENT_MISMATCH":
            root_cause = "Bank settlement shortfall due to unexpected dispute reserve hold or gateway MDR fee tier discrepancy."
            evidence = [
                f"Payment captured at ₹{tx.payment_amount:,.2f} with standard gateway fee ₹{tx.gateway_fee:,.2f}.",
                f"Expected settlement ₹{tx.payment_amount - tx.gateway_fee:,.2f}, actual bank deposit ₹{tx.settled_amount:,.2f}.",
                f"Settlement deficit of ₹{tx.exposure_amount:,.2f}."
            ]
            impact = f"Working capital cash shortfall of ₹{tx.exposure_amount:,.2f} from banking partner deposit."
            action = f"Generate Razorpay Settlement Ledger dispute ticket. Verify whether UTR {tx.settlement_id} includes chargeback deductions."
            journal = f"Dr. Gateway Settlement Receivable ₹{tx.exposure_amount:,.2f} | Cr. Bank Clearing Deficit ₹{tx.exposure_amount:,.2f}"
            urgency = "HIGH"

        else:
            root_cause = "Transaction fully verified across Order, Gateway, and Settlement tiers."
            evidence = ["All 3 tiers balanced within zero variance tolerance."]
            impact = "No financial risk or leakage."
            action = "No action required. Transaction closed in audit book."
            journal = "Standard revenue realization entries posted."
            urgency = "NONE"

        return InvestigationResponse(
            transaction_id=tx.id,
            order_id=tx.order_id,
            status=tx.status,
            severity=tx.severity,
            root_cause=root_cause,
            evidence_chain=evidence,
            financial_impact=impact,
            recommended_action=action,
            journal_entry=journal,
            urgency=urgency
        )

    def chat_with_agent(
        self, 
        messages: List[ChatMessage], 
        summary: ReconciliationSummary, 
        top_exceptions: List[TransactionRecord],
        focus_order: Optional[TransactionRecord] = None
    ) -> ChatResponse:
        """Grounded conversational AI finance agent."""
        
        exceptions_preview = "\n".join([
            f"- {tx.order_id} ({tx.status}, Severity: {tx.severity}): Expected ₹{tx.expected_amount:,.2f}, Received ₹{tx.received_amount:,.2f}, Exposure ₹{tx.exposure_amount:,.2f}, Method: {tx.payment_method}"
            for tx in top_exceptions[:12]
        ])

        focus_context = ""
        if focus_order:
            focus_context = f"""
Currently Focused Order:
- Order ID: {focus_order.order_id}
- Customer: {focus_order.customer}
- Status: {focus_order.status} ({focus_order.severity} Severity)
- Expected: ₹{focus_order.expected_amount:,.2f}, Received: ₹{focus_order.received_amount:,.2f}, Settled: ₹{focus_order.settled_amount:,.2f}
- Exposure: ₹{focus_order.exposure_amount:,.2f}
- Rule: {focus_order.rule_description}
"""

        system_prompt = f"""
You are the Autonomous AI Finance Controller for Razorpay Buildathon Track 04.
You provide executive-level, mathematically accurate answers grounded STRICTLY in the following financial reconciliation metrics:

OVERVIEW:
- Total Transactions Processed: {summary.total_records}
- Successfully Matched: {summary.matched_records}
- Total Exceptions: {summary.exceptions_count}
- Measured Match Rate: {summary.match_rate}%
- Total Unresolved Financial Exposure: ₹{summary.total_unresolved_exposure:,.2f}

EXCEPTIONS BY STATUS:
{json.dumps(summary.status_breakdown, indent=2)}

EXPOSURE BY ANOMALY (₹):
{json.dumps(summary.exposure_by_status, indent=2)}

SEVERITY DISTRIBUTION:
{json.dumps(summary.severity_breakdown, indent=2)}

TOP ACTIVE EXCEPTIONS:
{exceptions_preview}

{focus_context}

INSTRUCTIONS:
1. Always ground your analysis in these real numbers. Reference specific order IDs, ₹ amounts, and percentages.
2. Structure your answers with clear headings, bullet points, and actionable finance-ops steps.
3. Keep answers concise, authoritative, and focused on risk mitigation and cash recovery.
"""

        if not client or not openai_api_key:
            # Smart rule-based responses if OpenAI is not connected
            user_msg = messages[-1].content.lower()
            if "exposure" in user_msg or "risk" in user_msg or "amount" in user_msg:
                reply = (
                    f"### Financial Exposure Summary\n\n"
                    f"Our total unresolved financial exposure stands at **₹{summary.total_unresolved_exposure:,.2f}** "
                    f"across **{summary.exceptions_count} exceptions** (current match rate: **{summary.match_rate}%**).\n\n"
                    f"**Breakdown by Anomaly:**\n"
                )
                for st, exp in summary.exposure_by_status.items():
                    reply += f"- **{st.replace('_', ' ')}**: ₹{exp:,.2f}\n"
                reply += (
                    f"\n**High Severity Risk**: {summary.severity_breakdown.get('HIGH', 0)} transactions require immediate intervention.\n"
                    f"Top priority is resolving duplicate payment liabilities and recovering settlement deficits from banking partners."
                )
            elif "match rate" in user_msg or "throughput" in user_msg:
                reply = (
                    f"### Reconciliation Throughput & Match Rate\n\n"
                    f"- **Total Records Processed**: {summary.total_records}\n"
                    f"- **Reconciled (Matched)**: {summary.matched_records} ({summary.match_rate}%)\n"
                    f"- **Active Exceptions**: {summary.exceptions_count} ({round(100 - summary.match_rate, 2)}%)\n\n"
                    f"To reach an institutional 98%+ match rate, prioritize automating Razorpay webhook retry policies "
                    f"to prevent missing payment drops and set up automated refund pipelines for double debits."
                )
            elif focus_order:
                reply = (
                    f"### Analysis for {focus_order.order_id}\n\n"
                    f"- **Customer**: {focus_order.customer}\n"
                    f"- **Status**: `{focus_order.status}` ({focus_order.severity} Severity)\n"
                    f"- **Discrepancy Exposure**: ₹{focus_order.exposure_amount:,.2f}\n"
                    f"- **Diagnosis**: {focus_order.rule_description}\n\n"
                    f"**Action**: Execute the recommended operational remediation in the transaction inspector."
                )
            else:
                reply = (
                    f"### Autonomous AI Finance Controller Active\n\n"
                    f"I am actively monitoring **{summary.total_records} financial records** with a match rate of **{summary.match_rate}%**. "
                    f"Current unresolved exposure is **₹{summary.total_unresolved_exposure:,.2f}**.\n\n"
                    f"Ask me about specific orders (e.g. *'Analyze ORD_0010'*), financial leakage breakdowns, or recommended CFO actions."
                )
            return ChatResponse(reply=reply, referenced_orders=[tx.order_id for tx in top_exceptions[:5]])

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for m in messages[-6:]:
            formatted_messages.append({"role": m.role, "content": m.content})

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=0.3
            )
            reply = response.choices[0].message.content
            
            # Extract referenced order IDs
            referenced = [tx.order_id for tx in top_exceptions if tx.order_id in reply]
            if focus_order and focus_order.order_id not in referenced:
                referenced.append(focus_order.order_id)
                
            return ChatResponse(reply=reply, referenced_orders=referenced)
        except Exception as e:
            print(f"OpenAI error in chat: {e}")
            return ChatResponse(
                reply=f"AI Controller response (Offline Heuristic): Currently monitoring {summary.total_records} records. Unresolved exposure: ₹{summary.total_unresolved_exposure:,.2f}. High severity exceptions: {summary.severity_breakdown.get('HIGH', 0)}.",
                referenced_orders=[tx.order_id for tx in top_exceptions[:3]]
            )

    def generate_cfo_brief(
        self, 
        summary: ReconciliationSummary, 
        top_exceptions: List[TransactionRecord]
    ) -> CfoBriefResponse:
        """Generates an executive CFO Memorandum with leakage breakdown and strategic actions."""
        
        if not client or not openai_api_key:
            return self._heuristic_cfo_brief(summary, top_exceptions)

        prompt = f"""
You are the Chief Financial Officer (CFO) and Autonomous Finance Controller.
Generate an executive-ready, highly professional CFO Memorandum based on these real reconciliation results:

METRICS:
- Total Records: {summary.total_records}
- Reconciled Matched Records: {summary.matched_records}
- Measured Match Rate: {summary.match_rate}%
- Exceptions Count: {summary.exceptions_count}
- Total Unresolved Exposure: ₹{summary.total_unresolved_exposure:,.2f}
- Exposure by Status: {json.dumps(summary.exposure_by_status)}
- Severity Breakdown: {json.dumps(summary.severity_breakdown)}

Top Exceptions Sample:
{chr(10).join(f"- {tx.order_id} ({tx.status}): Exposure ₹{tx.exposure_amount:,.2f}" for tx in top_exceptions[:8])}

Return a valid JSON object with the following fields:
1. "executive_summary": 2-3 paragraph sharp CFO assessment of cash position, reconciliation efficiency, and financial health.
2. "financial_health_score": e.g. "82/100 (Operational Warning)"
3. "match_rate_analysis": Detailed diagnosis of the {summary.match_rate}% match rate and key drag factors.
4. "unresolved_leakage_breakdown": Clear explanation of where the ₹{summary.total_unresolved_exposure:,.2f} exposure is trapped.
5. "top_vulnerabilities": List of 3-4 specific operational risks (e.g. gateway webhook timeout, bank reserve holds).
6. "strategic_action_items": List of 3 objects with "priority" (P1/P2/P3), "action", and "roi_recovery" (estimated ₹ recovery and timeline).
"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an institutional corporate CFO. Output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            data = json.loads(response.choices[0].message.content)
            return CfoBriefResponse(
                executive_summary=data.get("executive_summary", "Reconciliation completed across payment channels."),
                financial_health_score=data.get("financial_health_score", "75/100 (Requires Review)"),
                match_rate_analysis=data.get("match_rate_analysis", f"Match rate currently at {summary.match_rate}%."),
                unresolved_leakage_breakdown=data.get("unresolved_leakage_breakdown", f"Total exposure of ₹{summary.total_unresolved_exposure:,.2f}."),
                top_vulnerabilities=data.get("top_vulnerabilities", ["Webhook latency", "Duplicate debit risks"]),
                strategic_action_items=data.get("strategic_action_items", [
                    {"priority": "P1", "action": "Automate duplicate payment refunds", "roi_recovery": "₹25,000 within 24h"}
                ]),
                generated_at=summary.last_updated
            )
        except Exception as e:
            print(f"OpenAI error in CFO brief: {e}. Falling back to heuristic.")
            return self._heuristic_cfo_brief(summary, top_exceptions)

    def _heuristic_cfo_brief(
        self, 
        summary: ReconciliationSummary, 
        top_exceptions: List[TransactionRecord]
    ) -> CfoBriefResponse:
        score_val = max(50, min(98, int(summary.match_rate * 0.9)))
        health_status = "Healthy" if score_val > 85 else ("Moderate Risk" if score_val > 70 else "High Alert")

        exec_summary = (
            f"During the latest multi-channel reconciliation cycle, DhanSetu evaluated {summary.total_records} "
            f"transactions across ERP orders, Razorpay gateway receipts, and bank settlement batches. "
            f"The measured match rate closed at {summary.match_rate}%, with {summary.matched_records} fully verified orders. "
            f"However, {summary.exceptions_count} unresolved anomalies represent a total at-risk capital exposure of "
            f"₹{summary.total_unresolved_exposure:,.2f}. "
            f"Immediate focus is required on high-severity duplicate charges and bank settlement deficits."
        )

        match_analysis = (
            f"At {summary.match_rate}%, automated reconciliation efficiency demonstrates robust straight-through processing. "
            f"The {round(100 - summary.match_rate, 2)}% anomaly drag is primarily distributed between uncaptured orders "
            f"(missing payments) and settlement withholding variance from banking partners."
        )

        leakage = (
            f"Total unresolved exposure is ₹{summary.total_unresolved_exposure:,.2f}. "
            f"Duplicate captures represent immediate chargeback liability, while settlement deficits represent trapped "
            f"cash in bank clearing accounts."
        )

        vulnerabilities = [
            "Gateway Webhook Dropping: Customers completing payments while ERP fails to receive capture callback.",
            "Double Debit Friction: Network retry latency prompting customers to pay twice on high-value checkouts.",
            "Settlement Discrepancies: Merchant bank withholding deposits exceeding standard 2% + GST MDR schedules.",
            "Unallocated Funds Liability: Inflow of orphan payments with missing ERP order tags."
        ]

        actions = [
            {
                "priority": "P1 - Critical",
                "action": "Trigger Razorpay Batch Refund API for all flagged DUPLICATE_PAYMENT records to avert chargeback penalties.",
                "roi_recovery": f"Recover / De-risk ~₹{summary.exposure_by_status.get('DUPLICATE_PAYMENT', 0):,.2f} within 2 hours."
            },
            {
                "priority": "P2 - High",
                "action": "File automated Razorpay settlement dispute tickets for all SETTLEMENT_MISMATCH UTR records.",
                "roi_recovery": f"Unlock ~₹{summary.exposure_by_status.get('SETTLEMENT_MISMATCH', 0):,.2f} in trapped working capital within T+2."
            },
            {
                "priority": "P3 - Medium",
                "action": "Execute ERP cart cleanup and send abandoned checkout recovery links for MISSING_PAYMENT records.",
                "roi_recovery": f"Potential revenue recapture of ~₹{summary.exposure_by_status.get('MISSING_PAYMENT', 0):,.2f}."
            }
        ]

        return CfoBriefResponse(
            executive_summary=exec_summary,
            financial_health_score=f"{score_val}/100 ({health_status})",
            match_rate_analysis=match_analysis,
            unresolved_leakage_breakdown=leakage,
            top_vulnerabilities=vulnerabilities,
            strategic_action_items=actions,
            generated_at=summary.last_updated
        )

# Singleton AI Agent
ai_agent = AiFinanceAgent()
