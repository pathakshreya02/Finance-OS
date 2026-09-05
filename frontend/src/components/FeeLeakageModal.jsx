import React, { useState, useEffect } from "react";

const fmt = (n, d = 2) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: d }).format(n || 0);

const METHOD_ICONS = { UPI: "📱", "Credit Card": "💳", "Debit Card": "🏧", Netbanking: "🏦" };
const METHOD_RATES = { UPI: "0.00% (NPCI Mandated)", "Credit Card": "1.95%", "Debit Card": "0.90%", Netbanking: "1.50%" };

export default function FeeLeakageModal({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeMethod, setActiveMethod] = useState(null);

  useEffect(() => {
    fetch("/api/reconcile/fee-analytics")
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box fee-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-loading"><div className="spinner" /><p>Computing fee analytics…</p></div>
      </div>
    </div>
  );

  if (!data) return null;

  const sortedMethods = [...(data.method_breakdown || [])].sort((a, b) => b.leakage - a.leakage);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box fee-modal wide" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-wrap">
            <span className="modal-icon amber">💸</span>
            <div>
              <h2 className="modal-title">MDR Fee Leakage & GST Tax Audit</h2>
              <p className="modal-subtitle">Gateway fee variance analysis with GST Input Tax Credit (ITC) reconciliation</p>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Summary KPIs */}
        <div className="fee-kpi-row">
          <div className="fee-kpi total-vol">
            <div className="fee-kpi-icon">💰</div>
            <div className="fee-kpi-value">₹{fmt(data.total_volume)}</div>
            <div className="fee-kpi-label">Total Payment Volume</div>
          </div>
          <div className="fee-kpi actual-fees">
            <div className="fee-kpi-icon">🏦</div>
            <div className="fee-kpi-value amber">₹{fmt(data.total_actual_fees)}</div>
            <div className="fee-kpi-label">Actual Fees Charged</div>
          </div>
          <div className="fee-kpi expected-fees">
            <div className="fee-kpi-icon">📋</div>
            <div className="fee-kpi-value">₹{fmt(data.total_expected_fees)}</div>
            <div className="fee-kpi-label">Contracted Rate Expected</div>
          </div>
          <div className="fee-kpi leakage" style={{ borderColor: data.total_leakage > 0 ? "var(--rose)" : "var(--emerald)" }}>
            <div className="fee-kpi-icon">⚠️</div>
            <div className="fee-kpi-value rose">₹{fmt(data.total_leakage)}</div>
            <div className="fee-kpi-label">Fee Leakage Detected</div>
          </div>
          <div className="fee-kpi gst-itc">
            <div className="fee-kpi-icon">🇮🇳</div>
            <div className="fee-kpi-value violet">₹{fmt(data.total_gst_itc)}</div>
            <div className="fee-kpi-label">GST ITC Claimable (18%)</div>
          </div>
        </div>

        {/* Method Breakdown */}
        <div className="fee-section-title">Fee Variance by Payment Method</div>
        <div className="fee-method-table">
          <div className="fee-table-header">
            <span>Method</span><span>Transactions</span><span>Volume</span>
            <span>Contracted Rate</span><span>Expected Fee</span><span>Actual Fee</span>
            <span>Leakage</span><span>GST ITC</span>
          </div>
          {sortedMethods.map((m) => (
            <div
              key={m.method}
              className={`fee-table-row ${activeMethod === m.method ? "active" : ""}`}
              onClick={() => setActiveMethod(activeMethod === m.method ? null : m.method)}
            >
              <span className="fee-method-name">{METHOD_ICONS[m.method] || "💳"} {m.method}</span>
              <span>{m.tx_count}</span>
              <span>₹{fmt(m.volume)}</span>
              <span className="fee-contracted">{METHOD_RATES[m.method] || m.effective_rate_pct + "%"}</span>
              <span>₹{fmt(m.expected_fee)}</span>
              <span className={m.actual_fee > m.expected_fee ? "amber" : ""}>₹{fmt(m.actual_fee)}</span>
              <span className={m.leakage > 0 ? "rose" : "emerald"}>
                {m.leakage > 0 ? "▲ " : "✓ "}₹{fmt(m.leakage)}
              </span>
              <span className="violet">₹{fmt(m.gst_itc_claimable)}</span>
            </div>
          ))}
        </div>

        {/* GST Note */}
        <div className="fee-gst-note">
          <div className="gst-note-icon">ℹ️</div>
          <div>
            <strong>GST on Gateway Fees (Section 9, CGST Act):</strong> Gateway providers charge 18% GST on MDR/platform fees.
            As a GST-registered merchant, you are entitled to claim <strong>₹{fmt(data.total_gst_itc)}</strong> as Input Tax Credit (ITC)
            in your periodic GSTR-2B reconciliation. Cross-reference against your gateway's monthly tax invoice.
            <br/><br/>
            <strong>Section 194-O TDS Notice:</strong> E-commerce operators deduct TDS @ 1% on net sales via Section 194-O.
            Validate deductions against Form 26AS / AIS in your income-tax portal before filing advance tax.
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-ghost" onClick={onClose}>Close</button>
          <button className="btn-primary" onClick={() => { window.open("/api/reconcile/export", "_blank"); }}>Export Full Fee Report ↓</button>
        </div>
      </div>
    </div>
  );
}
