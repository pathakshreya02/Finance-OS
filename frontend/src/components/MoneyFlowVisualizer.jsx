import React, { useMemo } from "react";
import { 
  ShoppingCart, 
  CreditCard, 
  Building2, 
  ArrowRight, 
  ShieldAlert, 
  Percent, 
  Activity, 
  CheckCircle2, 
  Sparkles,
  ExternalLink,
  Zap
} from "lucide-react";

const fmt = (n) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n || 0);

export default function MoneyFlowVisualizer({ 
  summary, 
  transactions, 
  onFilterStatus, 
  onOpenFeeAudit,
  activeFilter
}) {
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

  if (!metrics) {
    return (
      <div className="money-flow-container glass-panel">
        <div className="flow-empty">
          <Activity size={20} className="animate-spin text-muted" />
          <span>Synchronizing 3-Way Bridge Telemetry...</span>
        </div>
      </div>
    );
  }

  const { grossVolume, gatewayCapture, bankSettled, totalFees, totalExposure, captureRate, settlementRate, slaHealth } = metrics;
  const isHealthy = slaHealth >= 90;
  const slaColor = isHealthy ? "var(--emerald-500)" : slaHealth >= 75 ? "var(--amber-500)" : "var(--rose-500)";

  return (
    <div className="money-flow-container glass-panel">
      {/* Visualizer Header */}
      <div className="money-flow-header">
        <div className="flow-title-group">
          <div className="flow-title-icon-box">
            <Zap size={18} className="text-indigo" />
          </div>
          <div>
            <div className="flex-center-gap">
              <h2 className="flow-title">DhanSetu 3-Way Reconciliation Pipeline</h2>
              <span className="badge badge-indigo flex-center-gap">
                <Sparkles size={11} />
                <span>CONTINUOUS SYNC</span>
              </span>
            </div>
            <p className="flow-subtitle">Real-time capital flow: ERP Orders ➔ Razorpay Gateway ➔ Bank Settlement UTR</p>
          </div>
        </div>

        <div className="flow-legend">
          <span className="legend-item"><span className="legend-dot bg-indigo"></span> Ingested</span>
          <span className="legend-item"><span className="legend-dot bg-cyan"></span> Captured</span>
          <span className="legend-item"><span className="legend-dot bg-emerald"></span> Settled</span>
        </div>
      </div>

      {/* 3-Way Interactive Pipeline */}
      <div className="money-flow-pipeline">
        {/* Node 1: ERP Orders */}
        <div 
          className={`flow-node gross interactive ${activeFilter === 'ALL' ? 'active-node' : ''}`}
          onClick={() => onFilterStatus && onFilterStatus('ALL')}
          title="Click to view all ingested orders"
        >
          <div className="flow-node-header">
            <div className="flow-node-icon-circle bg-indigo-subtle">
              <ShoppingCart size={20} className="text-indigo" />
            </div>
            <span className="flow-stage-step">STAGE 01</span>
          </div>
          <div className="flow-node-label">ERP Ingested Orders</div>
          <div className="flow-node-value">₹{fmt(grossVolume)}</div>
          <div className="flow-node-meta">
            <span>{summary.total_records} Orders Logged</span>
          </div>
          <div className="node-click-hint">Click to filter table ↓</div>
        </div>

        {/* Bridge Connector 1 */}
        <div className="flow-arrow-wrap">
          <div className="flow-connector-track">
            <div className="flow-connector-fill bg-gradient-indigo" style={{ width: `${captureRate}%` }} />
            <div className="flow-connector-pulse"></div>
          </div>
          <div className="flow-arrow-badge">
            <span className="connector-rate">{captureRate}%</span>
            <span className="connector-label">Captured</span>
          </div>
          <div className="flow-arrow-indicator">
            <ArrowRight size={14} className="text-muted" />
          </div>
        </div>

        {/* Node 2: Razorpay Gateway */}
        <div 
          className="flow-node gateway interactive"
          onClick={() => onFilterStatus && onFilterStatus('ALL')}
          title="Click to view gateway transactions"
        >
          <div className="flow-node-header">
            <div className="flow-node-icon-circle bg-cyan-subtle">
              <CreditCard size={20} className="text-cyan" />
            </div>
            <span className="flow-stage-step">STAGE 02</span>
          </div>
          <div className="flow-node-label">Razorpay Gateway</div>
          <div className="flow-node-value text-cyan">₹{fmt(gatewayCapture)}</div>
          <div className="flow-node-meta">
            <span>Auth & Captured</span>
          </div>
          <div className="node-click-hint">Gateway Records ↓</div>
        </div>

        {/* Bridge Connector 2 */}
        <div className="flow-arrow-wrap">
          <div className="flow-connector-track">
            <div className="flow-connector-fill bg-gradient-emerald" style={{ width: `${settlementRate}%` }} />
            <div className="flow-connector-pulse"></div>
          </div>
          <div className="flow-arrow-badge">
            <span className="connector-rate text-emerald">{settlementRate}%</span>
            <span className="connector-label">Deposited</span>
          </div>
          <div className="flow-arrow-indicator">
            <ArrowRight size={14} className="text-muted" />
          </div>
        </div>

        {/* Node 3: Bank Settlement UTR */}
        <div 
          className={`flow-node settled interactive ${activeFilter === 'MATCHED' ? 'active-node' : ''}`}
          onClick={() => onFilterStatus && onFilterStatus('MATCHED')}
          title="Click to view fully reconciled bank settlements"
        >
          <div className="flow-node-header">
            <div className="flow-node-icon-circle bg-emerald-subtle">
              <Building2 size={20} className="text-emerald" />
            </div>
            <span className="flow-stage-step">STAGE 03</span>
          </div>
          <div className="flow-node-label">Bank Settlement (UTR)</div>
          <div className="flow-node-value text-emerald">₹{fmt(bankSettled)}</div>
          <div className="flow-node-meta">
            <span>{summary.matched_records} Matched Deposits</span>
          </div>
          <div className="node-click-hint">View Reconciled ↓</div>
        </div>
      </div>

      {/* Sentinel Insights Bar */}
      <div className="flow-leakage-row">
        {/* MDR Leakage & Tax Audit */}
        <div 
          className="flow-leakage-item fees interactive-leakage"
          onClick={onOpenFeeAudit}
          title="Click to open MDR Fee & GST Tax Audit Workbench"
        >
          <div className="flow-leakage-icon-box bg-amber-subtle">
            <Percent size={18} className="text-amber" />
          </div>
          <div className="flow-leakage-body">
            <span className="flow-leakage-label">MDR & Gateway Deductions</span>
            <span className="flow-leakage-val text-amber">₹{fmt(totalFees)}</span>
          </div>
          <div className="flow-leakage-action">
            <span className="leakage-action-btn">Audit GST & Fees <ExternalLink size={12} /></span>
          </div>
        </div>

        <div className="flow-leakage-divider" />

        {/* At-Risk Capital Exposure */}
        <div 
          className="flow-leakage-item exposure interactive-leakage"
          onClick={() => onFilterStatus && onFilterStatus('EXCEPTIONS')}
          title="Click to filter to high-risk anomaly records"
        >
          <div className="flow-leakage-icon-box bg-rose-subtle">
            <ShieldAlert size={18} className="text-rose" />
            {totalExposure > 0 && <span className="pulsing-beacon-mini"></span>}
          </div>
          <div className="flow-leakage-body">
            <div className="flex-center-gap">
              <span className="flow-leakage-label">At-Risk Capital Exposure</span>
              <span className="badge badge-rose text-xs">{summary.exceptions_count} Flags</span>
            </div>
            <span className="flow-leakage-val text-rose">₹{fmt(totalExposure)}</span>
          </div>
          <div className="flow-leakage-action">
            <span className="leakage-action-btn text-rose">Resolve Exceptions ↓</span>
          </div>
        </div>

        <div className="flow-leakage-divider" />

        {/* Settlement SLA Health */}
        <div className="flow-leakage-item sla">
          <div className="flow-leakage-icon-box" style={{ background: `${slaColor}1a` }}>
            <Activity size={18} style={{ color: slaColor }} />
          </div>
          <div className="flow-leakage-body">
            <span className="flow-leakage-label">Reconciliation Straight-Through</span>
            <div className="sla-gauge-wrap">
              <div className="sla-gauge-track">
                <div 
                  className="sla-gauge-fill" 
                  style={{ width: `${slaHealth}%`, background: slaColor }} 
                />
              </div>
              <span className="flow-leakage-val" style={{ color: slaColor }}>{slaHealth}%</span>
            </div>
          </div>
          <div 
            className="flow-leakage-badge" 
            style={{ background: `${slaColor}18`, color: slaColor, border: `1px solid ${slaColor}40` }}
          >
            {isHealthy ? "T+1 SLA HEALTHY" : slaHealth >= 75 ? "T+2 EXTENDED" : "SLA AT RISK"}
          </div>
        </div>
      </div>
    </div>
  );
}
