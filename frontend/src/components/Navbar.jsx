import React from 'react';
import { 
  ShieldCheck, 
  Sparkles, 
  UploadCloud, 
  FileSpreadsheet, 
  FileText, 
  History, 
  RefreshCw,
  Download,
  Database
} from 'lucide-react';

export default function Navbar({ 
  onSeedData, 
  isSeeding, 
  onOpenUpload, 
  onOpenCfoBrief, 
  onOpenAuditTrail, 
  onToggleCopilot,
  isCopilotOpen,
  onExportCsv,
  onOpenFeeAudit,
  onSimulateWebhook,
  isSimulatingWebhook,
  summary
}) {
  return (
    <header className="navbar glass-panel">
      <div className="nav-brand-container">
        <div className="brand-logo-glow">
          <div className="brand-icon-box">
            <ShieldCheck className="brand-icon" size={24} />
          </div>
        </div>
        <div>
          <div className="brand-title-row">
            <h1 className="brand-title">DHANSETU</h1>
            <span className="badge badge-indigo">AI CONTROLLER v3.0</span>
            <span className="badge badge-emerald flex-center-gap">
              <Database size={12} />
              <span>PERSISTENT</span>
            </span>
          </div>
          <p className="brand-subtitle">The Autonomous 3-Way Bridge for Payment Reconciliation</p>
        </div>
      </div>

      <div className="nav-actions">
        <button 
          className="btn btn-secondary" 
          onClick={() => onSeedData(150)}
          disabled={isSeeding}
          title="Regenerate synthetic test dataset"
        >
          <RefreshCw size={15} className={isSeeding ? "animate-spin" : ""} />
          <span>{isSeeding ? "Seeding..." : "Seed 150"}</span>
        </button>

        <button 
          className="btn btn-secondary" 
          onClick={onOpenUpload}
          title="Upload custom Orders and Payments CSV files"
        >
          <UploadCloud size={16} />
          <span>Upload CSV</span>
        </button>

        <button 
          className="btn btn-secondary" 
          onClick={onOpenAuditTrail}
          title="View immutable compliance audit ledger"
        >
          <History size={16} />
          <span>Audit Trail</span>
        </button>

        <button 
          className="btn btn-secondary" 
          onClick={onExportCsv}
          title="Export current reconciliation dataset as CSV"
        >
          <Download size={16} />
          <span>Export CSV</span>
        </button>

        <button 
          className="btn btn-fee-audit" 
          onClick={onOpenFeeAudit}
          title="MDR Fee Leakage & GST ITC Audit"
        >
          <span style={{fontSize:'14px'}}>💸</span>
          <span>Fee & Tax Audit</span>
        </button>

        <button 
          className={`btn btn-webhook ${isSimulatingWebhook ? 'loading' : ''}`}
          onClick={onSimulateWebhook}
          disabled={isSimulatingWebhook}
          title="Simulate a live Razorpay payment event"
        >
          <span style={{fontSize:'14px'}}>{isSimulatingWebhook ? '⏳' : '⚡'}</span>
          <span>{isSimulatingWebhook ? 'Injecting...' : 'Live Webhook'}</span>
          {!isSimulatingWebhook && <span className="pulsing-dot" style={{background:'var(--emerald)'}}></span>}
        </button>

        <button 
          className="btn btn-cfo" 
          onClick={onOpenCfoBrief}
          title="Generate Executive CFO Risk & Strategic Brief"
        >
          <FileText size={16} />
          <span>CFO Brief</span>
        </button>

        <button 
          className={`btn btn-ai ${isCopilotOpen ? 'active' : ''}`}
          onClick={onToggleCopilot}
          title="Open AI Finance Copilot"
        >
          <Sparkles size={16} className="ai-sparkle-icon" />
          <span>AI Copilot</span>
          <span className="pulsing-dot"></span>
        </button>
      </div>
    </header>
  );
}
