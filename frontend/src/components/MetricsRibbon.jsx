import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  Activity, 
  IndianRupee, 
  PieChart,
  ShieldAlert,
  ArrowUpRight,
  ShieldCheck,
  Zap
} from 'lucide-react';

export default function MetricsRibbon({ 
  summary, 
  isLoading,
  onFilterSeverity,
  onFilterStatus,
  activeSeverity
}) {
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

  // Radial Gauge Calculations
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, matchRate)) / 100) * circumference;

  // Format INR currency
  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  return (
    <div className="metrics-ribbon">
      {/* 1. Reconciled Volume */}
      <div 
        className="metric-card glass-panel interactive-card"
        onClick={() => onFilterStatus && onFilterStatus('ALL')}
        title="Click to view all ingested transactions"
      >
        <div className="metric-header">
          <span className="metric-label">INGESTED VOLUME</span>
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
            100% Ingested
          </span>
        </div>
        <div className="metric-hover-indicator">Filter All Orders <ArrowUpRight size={12} /></div>
      </div>

      {/* 2. Radial Match Rate Gauge */}
      <div 
        className="metric-card glass-panel interactive-card"
        onClick={() => onFilterStatus && onFilterStatus('MATCHED')}
        title="Click to view fully matched transactions"
      >
        <div className="metric-header">
          <span className="metric-label">SETTLEMENT MATCH RATE</span>
          <div className="metric-icon-bubble bg-emerald">
            <TrendingUp size={18} />
          </div>
        </div>
        <div className="radial-metric-row">
          <div className="radial-gauge-container">
            <svg className="radial-svg" width="76" height="76" viewBox="0 0 76 76">
              <circle
                className="radial-track"
                cx="38"
                cy="38"
                r={radius}
                strokeWidth="6"
              />
              <circle
                className="radial-progress"
                cx="38"
                cy="38"
                r={radius}
                strokeWidth="6"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="radial-center-text">
              <span className="radial-val mono text-emerald">{matchRate.toFixed(1)}%</span>
            </div>
          </div>
          <div className="radial-details">
            <div className="radial-status-text">
              <span className="badge badge-emerald-subtle">
                <ShieldCheck size={11} /> {matchRate >= 90 ? "SLA OPTIMAL" : "SLA WARNING"}
              </span>
            </div>
            <p className="radial-hint text-muted">Target SLA: &gt;95.0% Straight-Through</p>
          </div>
        </div>
        <div className="metric-hover-indicator text-emerald">View Matched <ArrowUpRight size={12} /></div>
      </div>

      {/* 3. Unresolved Exposure */}
      <div 
        className="metric-card glass-panel metric-card-danger interactive-card"
        onClick={() => onFilterStatus && onFilterStatus('EXCEPTIONS')}
        title="Click to inspect all active discrepancies"
      >
        <div className="metric-header">
          <div className="flex-center-gap">
            <span className="metric-label">CAPITAL AT RISK (EXPOSURE)</span>
            {totalExposure > 0 && <span className="pulsing-beacon-sm"></span>}
          </div>
          <div className="metric-icon-bubble bg-rose">
            <ShieldAlert size={18} />
          </div>
        </div>
        <div className="metric-value-row">
          <span className="metric-primary-value mono text-rose">
            {formatINR(totalExposure)}
          </span>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-badge text-rose">
            <AlertTriangle size={13} /> {exceptionsCount} Exceptions
          </span>
          <span className="metric-footer-note text-muted">
            Requires Action
          </span>
        </div>
        <div className="metric-hover-indicator text-rose">Resolve Discrepancies <ArrowUpRight size={12} /></div>
      </div>

      {/* 4. Exceptions & Severity Chips */}
      <div className="metric-card glass-panel">
        <div className="metric-header">
          <span className="metric-label">ANOMALIES BY SEVERITY</span>
          <div className="metric-icon-bubble bg-amber">
            <PieChart size={18} />
          </div>
        </div>
        <div className="metric-value-row">
          <span className="metric-primary-value mono">{exceptionsCount}</span>
          <span className="metric-sub-label">Active Flags</span>
        </div>
        <div className="severity-chips-row">
          <button 
            className={`sev-chip sev-chip-high ${activeSeverity === 'HIGH' ? 'active-chip' : ''}`}
            onClick={() => onFilterSeverity && onFilterSeverity(activeSeverity === 'HIGH' ? 'ALL' : 'HIGH')}
            title="Filter to High severity exceptions"
          >
            <strong>{highSev}</strong> CRITICAL
          </button>
          <button 
            className={`sev-chip sev-chip-med ${activeSeverity === 'MEDIUM' ? 'active-chip' : ''}`}
            onClick={() => onFilterSeverity && onFilterSeverity(activeSeverity === 'MEDIUM' ? 'ALL' : 'MEDIUM')}
            title="Filter to Medium severity exceptions"
          >
            <strong>{medSev}</strong> MED
          </button>
          <button 
            className={`sev-chip sev-chip-low ${activeSeverity === 'LOW' ? 'active-chip' : ''}`}
            onClick={() => onFilterSeverity && onFilterSeverity(activeSeverity === 'LOW' ? 'ALL' : 'LOW')}
            title="Filter to Low severity exceptions"
          >
            <strong>{lowSev}</strong> LOW
          </button>
        </div>
      </div>
    </div>
  );
}
