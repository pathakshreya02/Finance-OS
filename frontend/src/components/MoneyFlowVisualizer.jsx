import React, { useMemo } from "react";

const fmt = (n) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n || 0);

export default function MoneyFlowVisualizer({ summary, transactions }) {
  const metrics = useMemo(() => {
    if (!summary || !transactions?.length) return null;
    const grossVolume = transactions.reduce((s, t) => s + (t.order_amount || 0), 0);
    const gatewayCapture = transactions.reduce((s, t) => s + (t.payment_amount || 0), 0);
    const bankSettled = transactions.reduce((s, t) => s + (t.settled_amount || 0), 0);
    const totalFees = transactions.reduce((s, t) => s + (t.gateway_fee || 0), 0);
    const totalExposure = summary.total_unresolved_exposure || 0;
    const captureRate = grossVolume > 0 ? Math.round((gatewayCapture / grossVolume) * 100) : 0;
    const settlementRate = gatewayCapture > 0 ? Math.round((bankSettled / gatewayCapture) * 100) : 0;
    const slaHealth = summary.match_rate || 0;
    return { grossVolume, gatewayCapture, bankSettled, totalFees, totalExposure, captureRate, settlementRate, slaHealth };
  }, [summary, transactions]);

  if (!metrics) return <div className="money-flow-container"><div className="flow-empty">Loading money flow data...</div></div>;

  const { grossVolume, gatewayCapture, bankSettled, totalFees, totalExposure, captureRate, settlementRate, slaHealth } = metrics;
  const slaColor = slaHealth >= 90 ? "var(--emerald)" : slaHealth >= 75 ? "var(--amber)" : "var(--rose)";

  return (
    <div className="money-flow-container">
      <div className="money-flow-header">
        <span className="flow-icon">?</span>
        <h2 className="flow-title">Live Money Flow Pipeline</h2>
        <span className="flow-subtitle">Real-time tracing: Customer Checkout ? Gateway ? Bank Settlement</span>
      </div>
      <div className="money-flow-pipeline">
        <div className="flow-node gross">
          <div className="flow-node-icon">??</div>
          <div className="flow-node-label">Gross Orders</div>
          <div className="flow-node-value">?{fmt(grossVolume)}</div>
          <div className="flow-node-count">{summary.total_records} txns</div>
        </div>
        <div className="flow-arrow-wrap">
          <div className="flow-arrow-bar"><div className="flow-arrow-fill" style={{ width: captureRate + "%" }} /></div>
          <div className="flow-arrow-label">{captureRate}% Captured</div>
          <div className="flow-arrow-chevron">?</div>
        </div>
        <div className="flow-node gateway">
          <div className="flow-node-icon">??</div>
          <div className="flow-node-label">Gateway Captured</div>
          <div className="flow-node-value">?{fmt(gatewayCapture)}</div>
          <div className="flow-node-count">Razorpay</div>
        </div>
        <div className="flow-arrow-wrap">
          <div className="flow-arrow-bar"><div className="flow-arrow-fill" style={{ width: settlementRate + "%", background: "var(--emerald)" }} /></div>
          <div className="flow-arrow-label">{settlementRate}% Settled</div>
          <div className="flow-arrow-chevron">?</div>
        </div>
        <div className="flow-node settled">
          <div className="flow-node-icon">??</div>
          <div className="flow-node-label">Bank Settled</div>
          <div className="flow-node-value emerald">?{fmt(bankSettled)}</div>
          <div className="flow-node-count">Cleared Funds</div>
        </div>
      </div>
      <div className="flow-leakage-row">
        <div className="flow-leakage-item fees">
          <div className="flow-leakage-icon">??</div>
          <div className="flow-leakage-body">
            <span className="flow-leakage-label">MDR & Gateway Fees</span>
            <span className="flow-leakage-val amber">?{fmt(totalFees)}</span>
          </div>
          <div className="flow-leakage-badge amber">Deducted</div>
        </div>
        <div className="flow-leakage-divider">|</div>
        <div className="flow-leakage-item exposure">
          <div className="flow-leakage-icon">??</div>
          <div className="flow-leakage-body">
            <span className="flow-leakage-label">Unresolved Exposure</span>
            <span className="flow-leakage-val rose">?{fmt(totalExposure)}</span>
          </div>
          <div className="flow-leakage-badge rose">At Risk</div>
        </div>
        <div className="flow-leakage-divider">|</div>
        <div className="flow-leakage-item sla">
          <div className="flow-leakage-icon">??</div>
          <div className="flow-leakage-body">
            <span className="flow-leakage-label">Settlement SLA Health</span>
            <div className="sla-gauge-wrap">
              <div className="sla-gauge-track"><div className="sla-gauge-fill" style={{ width: slaHealth + "%", background: slaColor }} /></div>
              <span className="flow-leakage-val" style={{ color: slaColor }}>{slaHealth}%</span>
            </div>
          </div>
          <div className="flow-leakage-badge" style={{ background: slaColor + "22", color: slaColor, border: "1px solid " + slaColor + "44" }}>
            {slaHealth >= 90 ? "T+1 ?" : slaHealth >= 75 ? "T+2 ?" : "SLA Breach ?"}
          </div>
        </div>
      </div>
    </div>
  );
}
