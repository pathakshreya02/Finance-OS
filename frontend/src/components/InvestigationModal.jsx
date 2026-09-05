import React, { useState } from 'react';
import { 
  X, 
  Sparkles, 
  AlertTriangle, 
  CheckCircle2, 
  Copy, 
  Check, 
  BookOpen, 
  ShieldAlert, 
  ArrowRight,
  Database,
  Building2,
  CreditCard
} from 'lucide-react';

export default function InvestigationModal({
  transaction,
  investigation,
  isLoading,
  onClose,
  onSubmitResolution,
  isResolving
}) {
  const [resolutionNote, setResolutionNote] = useState('');
  const [copiedJournal, setCopiedJournal] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [actionResult, setActionResult] = useState(null);
  const [showEmailPreview, setShowEmailPreview] = useState(false);
  const [showErpPreview, setShowErpPreview] = useState(false);
  const [copiedAction, setCopiedAction] = useState(null);

  if (!transaction) return null;

  const handleCopyJournal = () => {
    if (investigation?.journal_entry) {
      navigator.clipboard.writeText(investigation.journal_entry);
      setCopiedJournal(true);
      setTimeout(() => setCopiedJournal(false), 2000);
    }
  };

  const handleResolveSubmit = (e) => {
    e.preventDefault();
    if (!resolutionNote.trim()) return;
    onSubmitResolution(transaction.id, resolutionNote);
  };

  const handleDispatchAction = async (actionType, extraNote) => {
    setActionLoading(actionType);
    setActionResult(null);
    try {
      const res = await fetch('/api/actions/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_id: transaction.id, action_type: actionType, note: extraNote || resolutionNote || null })
      });
      const data = await res.json();
      setActionResult({ type: actionType, data });
      if (actionType === 'REFUND_DISPATCH' && data.success) {
        // auto-refresh parent
        onSubmitResolution && setTimeout(() => window.dispatchEvent(new Event('finance-refresh')), 800);
      }
    } catch (err) {
      setActionResult({ type: actionType, error: 'Network error dispatching action.' });
    } finally {
      setActionLoading(null);
    }
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedAction(key);
    setTimeout(() => setCopiedAction(null), 2000);
  };

  const formatINR = (val) => {
    if (val === null || val === undefined) return "₹0.00";
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(val);
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-container glass-panel modal-lg animate-fade-in">
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-badge-row">
              <span className="badge badge-indigo flex-center-gap">
                <Sparkles size={13} />
                <span>AI ROOT CAUSE INVESTIGATION</span>
              </span>
              <span className={`badge ${
                transaction.severity === 'HIGH' ? 'badge-rose' : 
                transaction.severity === 'MEDIUM' ? 'badge-amber' : 'badge-cyan'
              }`}>
                {transaction.severity} SEVERITY
              </span>
              {transaction.is_resolved && (
                <span className="badge badge-emerald">RESOLVED</span>
              )}
            </div>
            <h2 className="modal-title">
              Anomaly Analysis: <span className="mono text-indigo">{transaction.order_id}</span>
            </h2>
            <p className="modal-subtitle">
              Customer: <strong>{transaction.customer}</strong> • Rule Code: <span className="mono">{transaction.rule_code}</span>
            </p>
          </div>

          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body-scroll">
          {/* 3-Way Match Comparison Card */}
          <div className="ledger-compare-box">
            <h3 className="section-label">3-WAY LEDGER AUDIT COMPARISON</h3>
            <div className="ledger-grid">
              {/* ERP Order */}
              <div className="ledger-col">
                <div className="ledger-col-header">
                  <Database size={16} className="text-cyan" />
                  <span>1. ERP Order Ledger</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Order ID:</span>
                  <span className="mono val">{transaction.order_id}</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Order Amount:</span>
                  <span className="mono val font-semibold">{formatINR(transaction.order_amount)}</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Timestamp:</span>
                  <span className="mono val">{transaction.created_at}</span>
                </div>
              </div>

              {/* Gateway Payment */}
              <div className="ledger-col">
                <div className="ledger-col-header">
                  <CreditCard size={16} className="text-indigo" />
                  <span>2. Razorpay Gateway</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Payment ID:</span>
                  <span className="mono val">{transaction.payment_id || <span className="text-rose font-bold">MISSING</span>}</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Captured:</span>
                  <span className="mono val font-semibold">{formatINR(transaction.payment_amount || 0)}</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Fee / Status:</span>
                  <span className="mono val">{formatINR(transaction.gateway_fee || 0)} ({transaction.payment_status || 'N/A'})</span>
                </div>
              </div>

              {/* Bank Settlement */}
              <div className="ledger-col">
                <div className="ledger-col-header">
                  <Building2 size={16} className="text-emerald" />
                  <span>3. Bank Settlement</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Settlement ID:</span>
                  <span className="mono val">{transaction.settlement_id || <span className="text-muted">NONE</span>}</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Settled Amount:</span>
                  <span className="mono val font-semibold">{formatINR(transaction.settled_amount || 0)}</span>
                </div>
                <div className="ledger-data-item">
                  <span className="label">Variance:</span>
                  <span className="mono val text-rose font-semibold">{formatINR(transaction.exposure_amount)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* AI Intelligence Output */}
          {isLoading ? (
            <div className="ai-loading-box">
              <div className="ai-spinner">
                <Sparkles className="animate-spin text-indigo" size={28} />
              </div>
              <p className="font-medium">Synthesizing Gateway Events & ERP Transaction Records...</p>
              <span className="text-xs text-muted">Running autonomous corporate finance diagnosis</span>
            </div>
          ) : investigation ? (
            <div className="ai-results-container">
              {/* Root Cause Card */}
              <div className="ai-card root-cause-card">
                <div className="ai-card-header">
                  <ShieldAlert size={18} className="text-rose" />
                  <h4>Root Cause Diagnosis</h4>
                </div>
                <p className="ai-narrative-text">{investigation.root_cause}</p>
              </div>

              {/* Evidence Chain */}
              <div className="ai-card">
                <div className="ai-card-header">
                  <BookOpen size={18} className="text-indigo" />
                  <h4>Audit Evidence Chain</h4>
                </div>
                <ul className="evidence-list">
                  {investigation.evidence_chain?.map((ev, i) => (
                    <li key={i} className="evidence-item">
                      <span className="evidence-index mono">{i + 1}</span>
                      <span>{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Financial Impact & Recommended Action */}
              <div className="two-col-grid">
                <div className="ai-card">
                  <span className="text-xs text-muted font-bold tracking-wider">FINANCIAL EXPOSURE</span>
                  <p className="ai-narrative-text font-semibold text-rose mt-1">
                    {investigation.financial_impact}
                  </p>
                </div>
                <div className="ai-card">
                  <span className="text-xs text-muted font-bold tracking-wider">RECOMMENDED ACTION</span>
                  <p className="ai-narrative-text mt-1">
                    {investigation.recommended_action}
                  </p>
                </div>
              </div>

              {/* Accounting Journal Entry */}
              {investigation.journal_entry && (
                <div className="journal-entry-box">
                  <div className="journal-header">
                    <span className="journal-title">PROPOSED DOUBLE-ENTRY JOURNAL ADJUSTMENT</span>
                    <button 
                      className="btn-copy-journal"
                      onClick={handleCopyJournal}
                      title="Copy journal entry to clipboard"
                    >
                      {copiedJournal ? (
                        <>
                          <Check size={14} className="text-emerald" />
                          <span className="text-emerald">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy size={14} />
                          <span>Copy Entry</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="journal-code-block mono">
                    {investigation.journal_entry}
                  </div>
                </div>
              )}
            </div>
          ) : null}

          {/* Resolution Box */}
          <div className="resolution-section">
            <h3 className="section-label">⚡ AUTONOMOUS ACTION HUB — Self-Healing Controls</h3>
            {transaction.status !== 'MATCHED' && !transaction.is_resolved && (
              <div className="action-hub">
                <div className="action-hub-subtitle">Execute remediation actions with full audit trail logging</div>
                <div className="action-hub-grid">
                  {/* Refund Dispatch */}
                  {['DUPLICATE_PAYMENT', 'AMOUNT_MISMATCH', 'UNKNOWN_PAYMENT'].includes(transaction.status) && (
                    <button
                      className="action-btn action-btn-rose"
                      disabled={actionLoading === 'REFUND_DISPATCH'}
                      onClick={() => handleDispatchAction('REFUND_DISPATCH')}
                    >
                      <span className="action-btn-icon">💸</span>
                      <div className="action-btn-body">
                        <span className="action-btn-title">{actionLoading === 'REFUND_DISPATCH' ? 'Dispatching…' : 'Dispatch Razorpay Refund'}</span>
                        <span className="action-btn-desc">Initiate refund via Payments API v2</span>
                      </div>
                    </button>
                  )}
                  {/* ERP Export */}
                  <button
                    className="action-btn action-btn-violet"
                    disabled={actionLoading === 'ERP_JOURNAL_EXPORT'}
                    onClick={() => handleDispatchAction('ERP_JOURNAL_EXPORT')}
                  >
                    <span className="action-btn-icon">📊</span>
                    <div className="action-btn-body">
                      <span className="action-btn-title">{actionLoading === 'ERP_JOURNAL_EXPORT' ? 'Generating…' : 'Export ERP Journal Entry'}</span>
                      <span className="action-btn-desc">Dr / Cr JSON for QuickBooks / Zoho / SAP</span>
                    </div>
                  </button>
                  {/* Dispute Email */}
                  <button
                    className="action-btn action-btn-amber"
                    disabled={actionLoading === 'DISPUTE_EMAIL'}
                    onClick={() => handleDispatchAction('DISPUTE_EMAIL')}
                  >
                    <span className="action-btn-icon">✉️</span>
                    <div className="action-btn-body">
                      <span className="action-btn-title">{actionLoading === 'DISPUTE_EMAIL' ? 'Drafting…' : 'Draft Dispute Email'}</span>
                      <span className="action-btn-desc">Formal banking ops notice to gateway</span>
                    </div>
                  </button>
                </div>

                {/* Action Result */}
                {actionResult && (
                  <div className={`action-result ${actionResult.error ? 'action-result-error' : 'action-result-success'}`}>
                    {actionResult.error ? (
                      <span>❌ {actionResult.error}</span>
                    ) : (
                      <div className="action-result-content">
                        <div className="action-result-header">
                          <span>✅ {actionResult.data?.message}</span>
                          {actionResult.type === 'DISPUTE_EMAIL' && (
                            <div className="action-result-btns">
                              <button className="mini-btn" onClick={() => setShowEmailPreview(v => !v)}>👁 {showEmailPreview ? 'Hide' : 'Preview'}</button>
                              <button className="mini-btn" onClick={() => copyToClipboard(actionResult.data?.artifacts?.body, 'email')}>
                                {copiedAction === 'email' ? '✓ Copied' : '📋 Copy'}
                              </button>
                            </div>
                          )}
                          {actionResult.type === 'ERP_JOURNAL_EXPORT' && (
                            <div className="action-result-btns">
                              <button className="mini-btn" onClick={() => setShowErpPreview(v => !v)}>👁 {showErpPreview ? 'Hide' : 'Preview'}</button>
                              <button className="mini-btn" onClick={() => copyToClipboard(JSON.stringify(actionResult.data?.artifacts?.erp_payload, null, 2), 'erp')}>
                                {copiedAction === 'erp' ? '✓ Copied' : '📋 Copy JSON'}
                              </button>
                            </div>
                          )}
                          {actionResult.type === 'REFUND_DISPATCH' && (
                            <div className="action-result-meta">
                              Refund ID: <code>{actionResult.data?.artifacts?.refund_id}</code> | ₹{actionResult.data?.artifacts?.amount}
                            </div>
                          )}
                        </div>
                        {showEmailPreview && actionResult.type === 'DISPUTE_EMAIL' && (
                          <pre className="artifact-preview">{actionResult.data?.artifacts?.body}</pre>
                        )}
                        {showErpPreview && actionResult.type === 'ERP_JOURNAL_EXPORT' && (
                          <div>
                            <div className="je-preview">{actionResult.data?.artifacts?.formatted_preview}</div>
                            <pre className="artifact-preview">{JSON.stringify(actionResult.data?.artifacts?.erp_payload, null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            <h3 className="section-label" style={{marginTop: '1.25rem'}}>OPERATOR RESOLUTION WORKFLOW</h3>
            {transaction.is_resolved ? (
              <div className="resolved-status-box">
                <CheckCircle2 size={20} className="text-emerald" />
                <div>
                  <div className="font-semibold text-emerald">Exception Marked as Resolved</div>
                  <p className="text-sm text-muted mt-0.5">
                    <strong>Note:</strong> {transaction.resolution_note || "No resolution note provided."}
                  </p>
                </div>
              </div>
            ) : (
              <form onSubmit={handleResolveSubmit} className="resolution-form">
                <label className="resolution-label">
                  Resolution Justification / Accounting Reference:
                </label>
                <textarea 
                  className="resolution-textarea"
                  rows={3}
                  placeholder="e.g., Refund issued via Razorpay Dashboard #rfnd_91823. Voided ERP sales order..."
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  required
                />
                <div className="resolution-footer">
                  <span className="text-xs text-muted">
                    Resolving updates the general ledger exposure and generates a signed audit trail record.
                  </span>
                  <button 
                    type="submit" 
                    className="btn btn-emerald"
                    disabled={isResolving || !resolutionNote.trim()}
                  >
                    {isResolving ? (
                      <span className="flex-center-gap">
                        <span className="spinner-border"></span>
                        <span>Saving...</span>
                      </span>
                    ) : (
                      <span className="flex-center-gap">
                        <CheckCircle2 size={16} />
                        <span>Sign & Resolve Exception</span>
                      </span>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
