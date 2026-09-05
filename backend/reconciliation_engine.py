import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import uuid

from models import (
    TransactionRecord, 
    ReconciliationSummary, 
    AuditLogItem,
    ActionDispatchResponse, 
    FeeBreakdownItem, 
    FeeAnalyticsSummary
)
from database import (
    save_reconciliation_batch, 
    update_transaction_resolution, 
    load_stored_reconciliation
)

class ReconciliationEngine:
    def __init__(self):
        self.transactions: List[TransactionRecord] = []
        self.audit_logs: List[AuditLogItem] = []
        self.last_summary: Optional[ReconciliationSummary] = None
        self.load_from_db()

    def load_from_db(self):
        try:
            txs, summary, logs = load_stored_reconciliation()
            if txs and summary:
                self.transactions = txs
                self.last_summary = summary
                self.audit_logs = logs
                print(f"Loaded {len(self.transactions)} transactions and {len(self.audit_logs)} audit logs from SQLite.")
        except Exception as e:
            print(f"Notice: Initializing fresh state, SQLite load skipped or empty: {e}")

    def log_audit(self, entity_id: str, action: str, actor: str, rule_code: str, details: str):
        log_item = AuditLogItem(
            id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            entity_id=entity_id,
            action=action,
            actor=actor,
            rule_code=rule_code,
            details=details
        )
        self.audit_logs.insert(0, log_item)
        return log_item

    def reconcile(
        self, 
        orders_df: pd.DataFrame, 
        payments_df: pd.DataFrame, 
        settlements_df: Optional[pd.DataFrame] = None
    ) -> Tuple[List[TransactionRecord], ReconciliationSummary]:
        
        # Standardize column names if needed
        orders = orders_df.copy()
        payments = payments_df.copy()
        settlements = settlements_df.copy() if settlements_df is not None else pd.DataFrame()
        
        # Ensure base columns exist
        if "order_id" not in orders.columns:
            orders["order_id"] = pd.Series(dtype="str")
        if "order_amount" not in orders.columns:
            orders["order_amount"] = pd.Series(dtype="float")
        if "customer" not in orders.columns:
            orders["customer"] = "Customer " + orders["order_id"].astype(str) if not orders.empty else pd.Series(dtype="str")
        if "created_at" not in orders.columns:
            orders["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "payment_method" not in orders.columns:
            orders["payment_method"] = "UPI"
            
        if "order_id" not in payments.columns:
            payments["order_id"] = pd.Series(dtype="str")
        if "payment_id" not in payments.columns:
            payments["payment_id"] = pd.Series(dtype="str")
        if "payment_amount" not in payments.columns:
            payments["payment_amount"] = pd.Series(dtype="float")
        if "gateway_fee" not in payments.columns:
            payments["gateway_fee"] = 0.0
        if "status" not in payments.columns:
            payments["status"] = "SUCCESS"
        if "payment_method" not in payments.columns:
            payments["payment_method"] = "UPI"

        # Identify duplicate order_ids in payments
        if not payments.empty and "order_id" in payments.columns:
            duplicate_order_ids = set(
                payments[payments.duplicated(subset=["order_id"], keep=False)]["order_id"].unique()
            )
        else:
            duplicate_order_ids = set()

        results: List[TransactionRecord] = []
        
        # 1. Process all ERP Orders
        for _, order in orders.iterrows():
            order_id = str(order["order_id"])
            customer = str(order["customer"])
            order_amount = float(order["order_amount"])
            created_at = str(order.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            order_method = str(order.get("payment_method", "UPI"))

            matched_payments = payments[payments["order_id"].astype(str) == order_id]
            
            matched_settlements = pd.DataFrame()
            if not settlements.empty and "order_id" in settlements.columns:
                matched_settlements = settlements[settlements["order_id"].astype(str) == order_id]

            # Rule 2: MISSING PAYMENT
            if matched_payments.empty:
                severity = "HIGH" if order_amount >= 3000 else ("MEDIUM" if order_amount >= 1000 else "LOW")
                record = TransactionRecord(
                    id=f"TXN-{order_id}",
                    order_id=order_id,
                    customer=customer,
                    order_amount=order_amount,
                    created_at=created_at,
                    payment_id=None,
                    payment_amount=0.0,
                    payment_method=order_method,
                    payment_status="MISSING",
                    gateway_fee=0.0,
                    settlement_id=None,
                    settled_amount=0.0,
                    settlement_status="UNSETTLED",
                    expected_amount=order_amount,
                    received_amount=0.0,
                    difference=order_amount,
                    exposure_amount=order_amount,
                    status="MISSING_PAYMENT",
                    severity=severity,
                    rule_code="RULE_02_MISSING_PAYMENT",
                    rule_description=f"Order {order_id} recorded in ERP with value ₹{order_amount:,.2f}, but no Razorpay payment event captured.",
                    audit_history=[
                        f"[{created_at}] Order created in ERP for ₹{order_amount:,.2f}",
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reconciliation Engine: No matching payment found in gateway logs. Flagged as MISSING_PAYMENT."
                    ]
                )
                results.append(record)
                self.log_audit(order_id, "FLAG_EXCEPTION", "Reconciliation Engine v2.4", "RULE_02_MISSING_PAYMENT", f"Order {order_id} missing payment of ₹{order_amount:,.2f}")
                continue

            # Rule 4: DUPLICATE PAYMENT
            if order_id in duplicate_order_ids and len(matched_payments) > 1:
                total_received = float(matched_payments["payment_amount"].sum())
                pay_ids = ", ".join(matched_payments["payment_id"].astype(str).tolist())
                methods = matched_payments["payment_method"].iloc[0] if "payment_method" in matched_payments.columns else order_method
                excess = total_received - order_amount
                
                settled_val = float(matched_settlements["settled_amount"].sum()) if not matched_settlements.empty else total_received
                settle_id = str(matched_settlements["settlement_id"].iloc[0]) if not matched_settlements.empty else None

                record = TransactionRecord(
                    id=f"TXN-{order_id}",
                    order_id=order_id,
                    customer=customer,
                    order_amount=order_amount,
                    created_at=created_at,
                    payment_id=pay_ids,
                    payment_amount=total_received,
                    payment_method=methods,
                    payment_status="SUCCESS (DUPLICATE)",
                    gateway_fee=float(matched_payments["gateway_fee"].sum()) if "gateway_fee" in matched_payments.columns else 0.0,
                    settlement_id=settle_id,
                    settled_amount=settled_val,
                    settlement_status="SETTLED",
                    expected_amount=order_amount,
                    received_amount=total_received,
                    difference=excess,
                    exposure_amount=excess,
                    status="DUPLICATE_PAYMENT",
                    severity="HIGH",
                    rule_code="RULE_04_DUPLICATE_PAYMENT",
                    rule_description=f"Multiple successful captures ({len(matched_payments)}) detected. Excess ₹{excess:,.2f} at immediate dispute risk.",
                    audit_history=[
                        f"[{created_at}] Order registered for ₹{order_amount:,.2f}",
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Detected {len(matched_payments)} payment events ({pay_ids}). Total collected: ₹{total_received:,.2f}. Exposure: ₹{excess:,.2f}"
                    ]
                )
                results.append(record)
                self.log_audit(order_id, "FLAG_EXCEPTION", "Reconciliation Engine v2.4", "RULE_04_DUPLICATE_PAYMENT", f"Order {order_id} duplicate captures totaling ₹{total_received:,.2f}")
                continue

            # Single payment present
            single_payment = matched_payments.iloc[0]
            payment_id = str(single_payment["payment_id"])
            payment_amount = float(single_payment["payment_amount"])
            payment_method = str(single_payment.get("payment_method", order_method))
            gateway_fee = float(single_payment.get("gateway_fee", 0.0))
            pay_status = str(single_payment.get("status", "SUCCESS"))

            settled_amount = payment_amount - gateway_fee
            settlement_id = None
            if not matched_settlements.empty:
                settled_amount = float(matched_settlements["settled_amount"].iloc[0])
                settlement_id = str(matched_settlements["settlement_id"].iloc[0])

            # Rule 3: AMOUNT MISMATCH
            if abs(payment_amount - order_amount) > 0.01:
                diff = payment_amount - order_amount
                exposure = abs(diff)
                severity = "HIGH" if exposure >= 1000 else ("MEDIUM" if exposure >= 300 else "LOW")
                record = TransactionRecord(
                    id=f"TXN-{order_id}",
                    order_id=order_id,
                    customer=customer,
                    order_amount=order_amount,
                    created_at=created_at,
                    payment_id=payment_id,
                    payment_amount=payment_amount,
                    payment_method=payment_method,
                    payment_status=pay_status,
                    gateway_fee=gateway_fee,
                    settlement_id=settlement_id,
                    settled_amount=settled_amount,
                    settlement_status="SETTLED",
                    expected_amount=order_amount,
                    received_amount=payment_amount,
                    difference=diff,
                    exposure_amount=exposure,
                    status="AMOUNT_MISMATCH",
                    severity=severity,
                    rule_code="RULE_03_AMOUNT_MISMATCH",
                    rule_description=f"Order amount (₹{order_amount:,.2f}) does not match captured gateway amount (₹{payment_amount:,.2f}). Variance: ₹{diff:+,.2f}.",
                    audit_history=[
                        f"[{created_at}] Order logged at ₹{order_amount:,.2f}",
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Gateway captured ₹{payment_amount:,.2f} for {payment_id}. Delta of ₹{diff:+,.2f} flagged."
                    ]
                )
                results.append(record)
                self.log_audit(order_id, "FLAG_EXCEPTION", "Reconciliation Engine v2.4", "RULE_03_AMOUNT_MISMATCH", f"Amount mismatch on {order_id}: Expected ₹{order_amount:,.2f}, got ₹{payment_amount:,.2f}")
                continue

            # Rule 6: SETTLEMENT MISMATCH (Bank deposit lower than payment - fee)
            expected_settlement = round(payment_amount - gateway_fee, 2)
            if (expected_settlement - settled_amount) > 5.0: # Tolerance of ₹5 for rounding
                settle_diff = round(expected_settlement - settled_amount, 2)
                severity = "HIGH" if settle_diff >= 1000 else "MEDIUM"
                record = TransactionRecord(
                    id=f"TXN-{order_id}",
                    order_id=order_id,
                    customer=customer,
                    order_amount=order_amount,
                    created_at=created_at,
                    payment_id=payment_id,
                    payment_amount=payment_amount,
                    payment_method=payment_method,
                    payment_status=pay_status,
                    gateway_fee=gateway_fee,
                    settlement_id=settlement_id,
                    settled_amount=settled_amount,
                    settlement_status="SETTLEMENT_DEFICIT",
                    expected_amount=order_amount,
                    received_amount=payment_amount,
                    difference=settle_diff,
                    exposure_amount=settle_diff,
                    status="SETTLEMENT_MISMATCH",
                    severity=severity,
                    rule_code="RULE_06_SETTLEMENT_MISMATCH",
                    rule_description=f"Payment of ₹{payment_amount:,.2f} was captured, but Bank settlement was ₹{settled_amount:,.2f} instead of ₹{expected_settlement:,.2f} (shortfall of ₹{settle_diff:,.2f}).",
                    audit_history=[
                        f"[{created_at}] Order captured ₹{payment_amount:,.2f} via {payment_method}",
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bank settlement audit: Expected ₹{expected_settlement:,.2f} after fees, received ₹{settled_amount:,.2f}. Deficit ₹{settle_diff:,.2f}."
                    ]
                )
                results.append(record)
                self.log_audit(order_id, "FLAG_EXCEPTION", "Reconciliation Engine v2.4", "RULE_06_SETTLEMENT_MISMATCH", f"Settlement shortfall on {order_id}: Deficit ₹{settle_diff:,.2f}")
                continue

            # Rule 1: EXACT MATCH
            record = TransactionRecord(
                id=f"TXN-{order_id}",
                order_id=order_id,
                customer=customer,
                order_amount=order_amount,
                created_at=created_at,
                payment_id=payment_id,
                payment_amount=payment_amount,
                payment_method=payment_method,
                payment_status=pay_status,
                gateway_fee=gateway_fee,
                settlement_id=settlement_id,
                settled_amount=settled_amount,
                settlement_status="SETTLED",
                expected_amount=order_amount,
                received_amount=payment_amount,
                difference=0.0,
                exposure_amount=0.0,
                status="MATCHED",
                severity="NONE",
                rule_code="RULE_01_EXACT_MATCH",
                rule_description="Complete 3-way match verified across ERP order, Razorpay gateway payment, and bank settlement.",
                audit_history=[
                    f"[{created_at}] Order created for ₹{order_amount:,.2f}",
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 3-Way verification PASSED (Payment {payment_id}, Settlement {settlement_id or 'Auto'})."
                ]
            )
            results.append(record)

        # 2. Rule 5: UNKNOWN PAYMENTS (Payments present in PG/Bank with no ERP order)
        known_order_ids = set(orders["order_id"].astype(str).unique())
        unknown_payments = payments[~payments["order_id"].astype(str).isin(known_order_ids)]
        
        for _, unk in unknown_payments.iterrows():
            unk_order_id = str(unk["order_id"])
            unk_pay_id = str(unk["payment_id"])
            unk_amount = float(unk["payment_amount"])
            unk_method = str(unk.get("payment_method", "UPI"))
            unk_fee = float(unk.get("gateway_fee", 0.0))
            unk_time = str(unk.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            unk_settle_amount = unk_amount - unk_fee
            unk_settle_id = None
            if not settlements.empty and "order_id" in settlements.columns:
                m_settle = settlements[settlements["order_id"].astype(str) == unk_order_id]
                if not m_settle.empty:
                    unk_settle_amount = float(m_settle["settled_amount"].iloc[0])
                    unk_settle_id = str(m_settle["settlement_id"].iloc[0])

            severity = "HIGH" if unk_amount >= 3000 else "MEDIUM"
            record = TransactionRecord(
                id=f"TXN-{unk_pay_id}",
                order_id=unk_order_id,
                customer="Unassigned / External",
                order_amount=0.0,
                created_at=unk_time,
                payment_id=unk_pay_id,
                payment_amount=unk_amount,
                payment_method=unk_method,
                payment_status="SUCCESS",
                gateway_fee=unk_fee,
                settlement_id=unk_settle_id,
                settled_amount=unk_settle_amount,
                settlement_status="SETTLED",
                expected_amount=0.0,
                received_amount=unk_amount,
                difference=-unk_amount,
                exposure_amount=unk_amount,
                status="UNKNOWN_PAYMENT",
                severity=severity,
                rule_code="RULE_05_UNKNOWN_PAYMENT",
                rule_description=f"Orphan payment {unk_pay_id} received in Razorpay account without corresponding ERP Order.",
                audit_history=[
                    f"[{unk_time}] Gateway captured payment {unk_pay_id} for ₹{unk_amount:,.2f}",
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reconciliation Engine: No ERP record for {unk_order_id}. Flagged as UNKNOWN_PAYMENT liability."
                ]
            )
            results.append(record)
            self.log_audit(unk_order_id, "FLAG_EXCEPTION", "Reconciliation Engine v2.4", "RULE_05_UNKNOWN_PAYMENT", f"Orphan payment {unk_pay_id} of ₹{unk_amount:,.2f}")

        # Compute summary metrics
        total_records = len(results)
        matched_records = len([r for r in results if r.status == "MATCHED"])
        exceptions_count = total_records - matched_records
        match_rate = round((matched_records / total_records * 100.0), 2) if total_records > 0 else 0.0
        
        # Exposure: only unresolved non-matched
        total_exposure = round(sum(r.exposure_amount for r in results if r.status != "MATCHED" and not r.is_resolved), 2)

        status_breakdown = {}
        for r in results:
            status_breakdown[r.status] = status_breakdown.get(r.status, 0) + 1

        severity_breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for r in results:
            if r.status != "MATCHED" and not r.is_resolved:
                if r.severity in severity_breakdown:
                    severity_breakdown[r.severity] += 1

        exposure_by_status = {}
        for r in results:
            if r.status != "MATCHED" and not r.is_resolved:
                exposure_by_status[r.status] = round(exposure_by_status.get(r.status, 0.0) + r.exposure_amount, 2)

        method_breakdown = {}
        for r in results:
            m = r.payment_method or "UPI"
            if m not in method_breakdown:
                method_breakdown[m] = {"MATCHED": 0, "EXCEPTION": 0}
            if r.status == "MATCHED":
                method_breakdown[m]["MATCHED"] += 1
            else:
                method_breakdown[m]["EXCEPTION"] += 1

        summary = ReconciliationSummary(
            total_records=total_records,
            matched_records=matched_records,
            exceptions_count=exceptions_count,
            match_rate=match_rate,
            total_unresolved_exposure=total_exposure,
            status_breakdown=status_breakdown,
            severity_breakdown=severity_breakdown,
            exposure_by_status=exposure_by_status,
            method_breakdown=method_breakdown,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self.transactions = results
        self.last_summary = summary
        
        self.log_audit(
            "BATCH_RUN", 
            "RECONCILIATION_COMPLETE", 
            "Reconciliation Engine v2.4", 
            "ENGINE_EXECUTE", 
            f"Processed {total_records} records. Match rate: {match_rate}%. Exceptions: {exceptions_count}. Unresolved Exposure: ₹{total_exposure:,.2f}"
        )

        try:
            save_reconciliation_batch(self.transactions, self.last_summary, self.audit_logs)
        except Exception as e:
            print(f"Database save error: {e}")
        
        return results, summary

    def resolve_exception(self, transaction_id: str, note: str) -> Optional[TransactionRecord]:
        for r in self.transactions:
            if r.id == transaction_id or r.order_id == transaction_id:
                r.is_resolved = True
                r.resolution_note = note
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                r.audit_history.append(f"[{timestamp}] RESOLVED by Finance Controller. Note: {note}")
                
                # Recompute exposure
                if self.last_summary:
                    self.last_summary.total_unresolved_exposure = round(
                        sum(tx.exposure_amount for tx in self.transactions if tx.status != "MATCHED" and not tx.is_resolved), 2
                    )
                    # Update severity breakdown
                    self.last_summary.severity_breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
                    for tx in self.transactions:
                        if tx.status != "MATCHED" and not tx.is_resolved and tx.severity in self.last_summary.severity_breakdown:
                            self.last_summary.severity_breakdown[tx.severity] += 1
                            
                    # Update exposure by status
                    self.last_summary.exposure_by_status = {}
                    for tx in self.transactions:
                        if tx.status != "MATCHED" and not tx.is_resolved:
                            self.last_summary.exposure_by_status[tx.status] = round(
                                self.last_summary.exposure_by_status.get(tx.status, 0.0) + tx.exposure_amount, 2
                            )
                
                audit_entry = self.log_audit(
                    r.order_id, 
                    "MANUAL_RESOLUTION", 
                    "Finance Controller (User)", 
                    r.rule_code, 
                    f"Resolved exception for {r.order_id}. Note: {note}"
                )
                try:
                    update_transaction_resolution(r.id, note, r.audit_history, audit_entry)
                    if self.last_summary:
                        save_reconciliation_batch(self.transactions, self.last_summary, self.audit_logs)
                except Exception as e:
                    print(f"Database resolution update error: {e}")
                return r
        return None

    def get_fee_analytics(self) -> FeeAnalyticsSummary:
        contracted_rates = {
            "UPI": 0.0,
            "Debit Card": 0.009,
            "Credit Card": 0.0195,
            "Netbanking": 0.015
        }
        method_stats: Dict[str, Dict[str, float]] = {}
        for m in ["UPI", "Credit Card", "Debit Card", "Netbanking"]:
            method_stats[m] = {
                "count": 0,
                "volume": 0.0,
                "actual_fee": 0.0,
                "expected_fee": 0.0,
                "leakage": 0.0,
                "gst_itc": 0.0
            }
            
        for tx in self.transactions:
            m = tx.payment_method if tx.payment_method in method_stats else "UPI"
            vol = tx.payment_amount or tx.order_amount or 0.0
            act_fee = tx.gateway_fee or 0.0
            rate = contracted_rates.get(m, 0.015)
            exp_fee = round(vol * rate, 2)
            leakage = max(0.0, round(act_fee - exp_fee, 2))
            gst_itc = round(act_fee * 0.18 / 1.18, 2) if act_fee > 0 else 0.0
            
            method_stats[m]["count"] += 1
            method_stats[m]["volume"] += vol
            method_stats[m]["actual_fee"] += act_fee
            method_stats[m]["expected_fee"] += exp_fee
            method_stats[m]["leakage"] += leakage
            method_stats[m]["gst_itc"] += gst_itc
            
        items: List[FeeBreakdownItem] = []
        tot_vol = 0.0
        tot_act_fee = 0.0
        tot_exp_fee = 0.0
        tot_leakage = 0.0
        tot_gst_itc = 0.0
        
        for m, stats in method_stats.items():
            vol = round(stats["volume"], 2)
            act = round(stats["actual_fee"], 2)
            exp = round(stats["expected_fee"], 2)
            lk = round(stats["leakage"], 2)
            gst = round(stats["gst_itc"], 2)
            eff_rate = round((act / vol * 100), 2) if vol > 0 else 0.0
            
            tot_vol += vol
            tot_act_fee += act
            tot_exp_fee += exp
            tot_leakage += lk
            tot_gst_itc += gst
            
            items.append(FeeBreakdownItem(
                method=m,
                tx_count=int(stats["count"]),
                volume=vol,
                actual_fee=act,
                expected_fee=exp,
                leakage=lk,
                effective_rate_pct=eff_rate,
                gst_itc_claimable=gst
            ))
            
        return FeeAnalyticsSummary(
            total_volume=round(tot_vol, 2),
            total_actual_fees=round(tot_act_fee, 2),
            total_expected_fees=round(tot_exp_fee, 2),
            total_leakage=round(tot_leakage, 2),
            total_gst_itc=round(tot_gst_itc, 2),
            method_breakdown=items,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def dispatch_action(
        self, 
        transaction_id: str, 
        action_type: str, 
        note: Optional[str] = None, 
        amount: Optional[float] = None
    ) -> ActionDispatchResponse:
        target_tx: Optional[TransactionRecord] = None
        for t in self.transactions:
            if t.id == transaction_id or t.order_id == transaction_id:
                target_tx = t
                break
                
        if not target_tx:
            return ActionDispatchResponse(
                success=False,
                action_type=action_type,
                transaction_id=transaction_id,
                message=f"Transaction {transaction_id} not found."
            )
            
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if action_type == "REFUND_DISPATCH":
            refund_id = f"rfnd_{uuid.uuid4().hex[:14]}"
            refund_amt = round(amount if amount is not None else (target_tx.exposure_amount or target_tx.payment_amount or 0.0), 2)
            target_tx.is_resolved = True
            target_tx.resolution_note = f"Automated Refund of ₹{refund_amt:,.2f} dispatched via Razorpay Payments API (Ref: {refund_id}). Note: {note or 'Approved remediation'}"
            target_tx.audit_history.append(f"[{timestamp_str}] REFUND_DISPATCHED ({refund_id}) for ₹{refund_amt:,.2f}. Note: {note or ''}")
            
            # Recalculate exposure
            if self.last_summary:
                self.last_summary.total_unresolved_exposure = round(
                    sum(tx.exposure_amount for tx in self.transactions if tx.status != "MATCHED" and not tx.is_resolved), 2
                )
                self.last_summary.exposure_by_status[target_tx.status] = round(
                    max(0.0, self.last_summary.exposure_by_status.get(target_tx.status, 0.0) - target_tx.exposure_amount), 2
                )
                
            audit_item = self.log_audit(
                target_tx.order_id,
                "REFUND_DISPATCHED",
                "Autonomous Finance Controller",
                target_tx.rule_code,
                f"Dispatched Razorpay refund {refund_id} for ₹{refund_amt:,.2f}. Linked to order {target_tx.order_id}."
            )
            
            try:
                update_transaction_resolution(target_tx.id, target_tx.resolution_note, target_tx.audit_history, audit_item)
                if self.last_summary:
                    save_reconciliation_batch(self.transactions, self.last_summary, self.audit_logs)
            except Exception as e:
                print(f"Action dispatch DB error: {e}")
                
            return ActionDispatchResponse(
                success=True,
                action_type=action_type,
                transaction_id=target_tx.id,
                message=f"Refund {refund_id} for ₹{refund_amt:,.2f} dispatched successfully.",
                updated_record=target_tx,
                audit_item=audit_item,
                artifacts={
                    "refund_id": refund_id,
                    "amount": refund_amt,
                    "status": "PROCESSED",
                    "gateway": "Razorpay Payments API v2",
                    "dispatched_at": timestamp_str
                }
            )
            
        elif action_type == "DISPUTE_EMAIL":
            subject = f"[FINANCE OPS DISPUTE] Settlement Discrepancy Notice — Order {target_tx.order_id} (Ref: {target_tx.payment_id or 'N/A'})"
            recipient = "settlements-ops@razorpay.com, nodal-officer@bankpartner.in"
            body = f"""To: Settlements & Dispute Operations <settlements-ops@razorpay.com>
From: Finance Controller Office <finance-ops@enterprise.internal>
Date: {datetime.now().strftime("%d %b %Y, %H:%M:%S IST")}
Subject: {subject}

Dear Banking & Gateway Operations Team,

During our autonomous 3-way financial reconciliation audit cycle, an unresolved variance was detected on your ledger:

══════════════════════════════════════════════════════════════════════
TRANSACTION RECONCILIATION SUMMARY
══════════════════════════════════════════════════════════════════════
• Internal Order ID:       {target_tx.order_id}
• Customer Name:           {target_tx.customer}
• Transaction Timestamp:   {target_tx.created_at}
• Payment Gateway ID:      {target_tx.payment_id or "MISSING / NOT CAPTURED"}
• Bank Settlement ID:      {target_tx.settlement_id or "PENDING SETTLEMENT"}
• ERP Expected Amount:     ₹{target_tx.order_amount:,.2f}
• Gateway Captured Amount: ₹{target_tx.payment_amount or 0.0:,.2f}
• Bank Settled Amount:     ₹{target_tx.settled_amount or 0.0:,.2f}
• Discrepancy Variance:    ₹{target_tx.difference:,.2f}
• Financial Exposure:      ₹{target_tx.exposure_amount:,.2f}
• Violation Code:          {target_tx.rule_code} ({target_tx.status})
══════════════════════════════════════════════════════════════════════

Root Cause Analysis:
{target_tx.rule_description}

Operator Context / Instructions:
{note or "Discrepancy exceeds automatic tolerance limits. Please audit the corresponding settlement batch credit, reconcile fee deductions, and reverse or credit the variance."}

Please acknowledge receipt of this dispute notice and provide the UTR / remittance reference within 24 business hours.

Sincerely,
Autonomous Finance Controller
DhanSetu — Enterprise Financial Operations
"""
            audit_item = self.log_audit(
                target_tx.order_id,
                "DISPUTE_EMAIL_DRAFTED",
                "Finance Controller (User)",
                target_tx.rule_code,
                f"Generated formal dispute notice for {target_tx.order_id} addressed to {recipient}."
            )
            
            return ActionDispatchResponse(
                success=True,
                action_type=action_type,
                transaction_id=target_tx.id,
                message="Banking operations dispute email drafted and recorded.",
                updated_record=target_tx,
                audit_item=audit_item,
                artifacts={
                    "subject": subject,
                    "recipient": recipient,
                    "body": body,
                    "drafted_at": timestamp_str
                }
            )

        elif action_type == "ERP_JOURNAL_EXPORT":
            je_id = f"JE-{uuid.uuid4().hex[:8].upper()}"
            debit_acct = "Bank Clearing Variance A/c" if target_tx.status == "SETTLEMENT_MISMATCH" else "Sales Discount & Discrepancy A/c"
            credit_acct = "Gateway In-Transit Clearing A/c" if target_tx.status == "SETTLEMENT_MISMATCH" else "Accounts Receivable (Online Orders)"
            
            erp_payload = {
                "journal_entry_id": je_id,
                "posting_date": datetime.now().strftime("%Y-%m-%d"),
                "currency": "INR",
                "reference_document": target_tx.order_id,
                "source_system": "FINANCE_OS_RECONCILER",
                "rule_code": target_tx.rule_code,
                "lines": [
                    {
                        "account_name": debit_acct,
                        "posting_type": "DEBIT",
                        "amount": round(target_tx.exposure_amount or target_tx.order_amount, 2),
                        "description": f"Variance offset for order {target_tx.order_id}"
                    },
                    {
                        "account_name": credit_acct,
                        "posting_type": "CREDIT",
                        "amount": round(target_tx.exposure_amount or target_tx.order_amount, 2),
                        "description": f"Credit adjustment for order {target_tx.order_id}"
                    }
                ],
                "memo": f"Automated 3-way reconciliation journal adjustment. Exception: {target_tx.status}. Operator Note: {note or 'Standard ERP sync'}"
            }
            
            audit_item = self.log_audit(
                target_tx.order_id,
                "ERP_JOURNAL_EXPORTED",
                "Finance Controller (User)",
                target_tx.rule_code,
                f"Exported ERP Journal Entry {je_id} for order {target_tx.order_id}."
            )
            
            return ActionDispatchResponse(
                success=True,
                action_type=action_type,
                transaction_id=target_tx.id,
                message=f"ERP Journal Entry {je_id} generated successfully.",
                updated_record=target_tx,
                audit_item=audit_item,
                artifacts={
                    "journal_entry_id": je_id,
                    "erp_payload": erp_payload,
                    "formatted_preview": f"Dr. {debit_acct} ₹{target_tx.exposure_amount:,.2f} | Cr. {credit_acct} ₹{target_tx.exposure_amount:,.2f}"
                }
            )
            
        return ActionDispatchResponse(
            success=False,
            action_type=action_type,
            transaction_id=target_tx.id,
            message=f"Unsupported action type: {action_type}"
        )

    def ingest_event(
        self,
        event_type: str = "payment.captured",
        amount: float = 1500.0,
        customer: str = "Live Webhook User",
        payment_method: str = "UPI",
        simulate_discrepancy: str = "NONE"
    ) -> Tuple[TransactionRecord, ReconciliationSummary]:
        idx = len(self.transactions) + 1
        order_id = f"ORD_LIVE_{idx:04d}"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        order_amount = amount
        payment_id = f"pay_live_{uuid.uuid4().hex[:10]}"
        settlement_id = f"set_live_{uuid.uuid4().hex[:10]}"
        payment_amount = amount
        settled_amount = amount
        gateway_fee = round(amount * (0.02 if payment_method == "Credit Card" else 0.0), 2)
        status = "MATCHED"
        severity = "NONE"
        rule_code = "RULE_01_MATCH"
        rule_desc = "Order amount matches payment captured and bank settlement exactly."
        diff = 0.0
        exposure = 0.0
        
        if simulate_discrepancy == "AMOUNT_MISMATCH":
            payment_amount = round(amount * 0.85, 2)
            settled_amount = payment_amount
            diff = round(order_amount - payment_amount, 2)
            exposure = diff
            status = "AMOUNT_MISMATCH"
            severity = "HIGH" if exposure >= 1000 else "MEDIUM"
            rule_code = "RULE_03_AMT_DIFF"
            rule_desc = f"Payment amount (₹{payment_amount}) differs from ERP order (₹{order_amount})."
            
        elif simulate_discrepancy == "MISSING_PAYMENT":
            payment_id = None
            payment_amount = 0.0
            settlement_id = None
            settled_amount = 0.0
            diff = order_amount
            exposure = order_amount
            status = "MISSING_PAYMENT"
            severity = "HIGH"
            rule_code = "RULE_02_NO_PAY"
            rule_desc = "Order registered in ERP but no matching payment captured by gateway."
            
        elif simulate_discrepancy == "SETTLEMENT_MISMATCH":
            settled_amount = round(payment_amount - 150.0, 2)
            diff = 150.0
            exposure = diff
            status = "SETTLEMENT_MISMATCH"
            severity = "MEDIUM"
            rule_code = "RULE_06_SETTLE_DIFF"
            rule_desc = f"Bank settled amount differs from gateway capture by ₹{diff}."
            
        rec = TransactionRecord(
            id=f"TXN-{order_id}",
            order_id=order_id,
            customer=customer,
            order_amount=order_amount,
            created_at=created_at,
            payment_id=payment_id,
            payment_amount=payment_amount,
            payment_method=payment_method,
            payment_status="SUCCESS" if payment_id else "FAILED",
            gateway_fee=gateway_fee,
            settlement_id=settlement_id,
            settled_amount=settled_amount,
            settlement_status="SETTLED" if settlement_id else "PENDING",
            expected_amount=order_amount,
            received_amount=payment_amount,
            difference=diff,
            exposure_amount=exposure,
            status=status,
            severity=severity,
            rule_code=rule_code,
            rule_description=rule_desc,
            is_resolved=False,
            resolution_note=None,
            audit_history=[f"[{created_at}] LIVE INGESTION via Razorpay Webhook ({event_type})"]
        )
        
        self.transactions.insert(0, rec)
        
        tot = len(self.transactions)
        matched = sum(1 for t in self.transactions if t.status == "MATCHED")
        exceptions = tot - matched
        match_rate = round((matched / tot) * 100, 2) if tot > 0 else 0.0
        unresolved_exposure = round(sum(t.exposure_amount for t in self.transactions if t.status != "MATCHED" and not t.is_resolved), 2)
        
        status_bd: Dict[str, int] = {}
        for t in self.transactions:
            status_bd[t.status] = status_bd.get(t.status, 0) + 1
            
        sev_bd = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for t in self.transactions:
            if t.status != "MATCHED" and not t.is_resolved and t.severity in sev_bd:
                sev_bd[t.severity] += 1
                
        exp_by_status: Dict[str, float] = {}
        for t in self.transactions:
            if t.status != "MATCHED" and not t.is_resolved:
                exp_by_status[t.status] = round(exp_by_status.get(t.status, 0.0) + t.exposure_amount, 2)
                
        method_bd: Dict[str, Dict[str, int]] = {}
        for t in self.transactions:
            m = t.payment_method or "UPI"
            if m not in method_bd:
                method_bd[m] = {"MATCHED": 0, "EXCEPTION": 0}
            if t.status == "MATCHED":
                method_bd[m]["MATCHED"] += 1
            else:
                method_bd[m]["EXCEPTION"] += 1
                
        self.last_summary = ReconciliationSummary(
            total_records=tot,
            matched_records=matched,
            exceptions_count=exceptions,
            match_rate=match_rate,
            total_unresolved_exposure=unresolved_exposure,
            status_breakdown=status_bd,
            severity_breakdown=sev_bd,
            exposure_by_status=exp_by_status,
            method_breakdown=method_bd,
            last_updated=created_at
        )
        
        self.log_audit(
            order_id,
            "WEBHOOK_INGESTED",
            "Razorpay Webhook Stream v2",
            rule_code,
            f"Ingested live {event_type} event for {order_id}. Status: {status}. Exposure: ₹{exposure:,.2f}"
        )
        
        try:
            save_reconciliation_batch(self.transactions, self.last_summary, self.audit_logs)
        except Exception as e:
            print(f"Webhook save error: {e}")
            
        return rec, self.last_summary


# Singleton instance
engine = ReconciliationEngine()
