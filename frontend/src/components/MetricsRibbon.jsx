import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  Activity, 
  DollarSign, 
  PieChart 
} from 'lucide-react';

export default function MetricsRibbon({ summary, isLoading }) {
  if (!summary && isLoading) {
    return (
      <div className="metrics-ribbon-skeleton">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card glass-panel skeleton-card"></div>
        ))}
      </div>
    );
  }

  const matchRate = summary?.match_rate || 0;
  const totalRecords = summary?.total_records || 0;
  const matchedRecords = summary?.matched_records || 0;
  const exceptionsCount = summary?.exceptions_count || 0;
  const totalExposure = summary?.total_unresolved_exposure || 0;
  const highSev = summary?.severity_breakdown?.HIGH || 0;
  const medSev = summary?.severity_breakdown?.MEDIUM || 0;
  const lowSev = summary?.severity_breakdown?.LOW || 0;

  // Format INR currency
  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <div className="metrics-ribbon">
      {/* 1. Reconciled Volume */}
      <div className="metric-card glass-panel">
        <div className="metric-header">
          <span className="metric-label">TOTAL VOLUME</span>
          <div className="metric-icon-bubble bg-indigo">
            <Activity size={18} />
          </div>
        </div>
        <div className="metric-value-row">
          <span className="metric-primary-value mono">{totalRecords}</span>
          <span className="metric-sub-label">Transactions</span>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-badge text-emerald">
            <CheckCircle2 size={13} /> {matchedRecords} Reconciled
          </span>
          <span className="metric-footer-note text-muted">
            {exceptionsCount} Anomaly Flags
          </span>
        </div>
      </div>

      {/* 2. Match Rate */}
      <div className="metric-card glass-panel">
        <div className="metric-header">
          <span className="metric-label">SETTLEMENT MATCH RATE</span>
          <div className="metric-icon-bubble bg-emerald">
            <TrendingUp size={18} />
          </div>
        </div>
        <div className="metric-value-row">
          <span className="metric-primary-value mono text-emerald">{matchRate.toFixed(1)}%</span>
          <span className="metric-sub-label">Verified</span>
        </div>
        <div className="progress-bar-container">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${Math.min(100, Math.max(0, matchRate))}%` }}
          ></div>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-note text-muted">
            Target SLA: &gt;95.0%
          </span>
        </div>
      </div>

      {/* 3. Unresolved Exposure */}
      <div className="metric-card glass-panel">
        <div className="metric-header">
          <span className="metric-label">UNRESOLVED EXPOSURE</span>
          <div className="metric-icon-bubble bg-rose">
            <DollarSign size={18} />
          </div>
        </div>
        <div className="metric-value-row">
          <span className="metric-primary-value mono text-rose">
            {formatINR(totalExposure)}
          </span>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-badge text-rose">
            <AlertTriangle size={13} /> Financial Leakage Risk
          </span>
          <span className="metric-footer-note text-muted">
            Pending Resolution
          </span>
        </div>
      </div>

      {/* 4. Exceptions & Severity */}
      <div className="metric-card glass-panel">
        <div className="metric-header">
          <span className="metric-label">ANOMALIES BY SEVERITY</span>
          <div className="metric-icon-bubble bg-amber">
            <PieChart size={18} />
          </div>
        </div>
        <div className="metric-value-row">
          <span className="metric-primary-value mono">{exceptionsCount}</span>
          <span className="metric-sub-label">Discrepancies</span>
        </div>
        <div className="severity-chips-row">
          <span className="sev-chip sev-chip-high">
            <strong>{highSev}</strong> HIGH
          </span>
          <span className="sev-chip sev-chip-med">
            <strong>{medSev}</strong> MED
          </span>
          <span className="sev-chip sev-chip-low">
            <strong>{lowSev}</strong> LOW
          </span>
        </div>
      </div>
    </div>
  );
}
