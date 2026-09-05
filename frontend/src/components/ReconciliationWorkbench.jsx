import React, { useEffect, useRef } from 'react';
import { 
  Search, 
  Filter, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  ChevronLeft, 
  ChevronRight, 
  ArrowUpDown, 
  FileCheck, 
  RotateCcw,
  CreditCard,
  Building2,
  Zap,
  Wallet,
  Eye,
  SlidersHorizontal
} from 'lucide-react';

export default function ReconciliationWorkbench({
  transactions,
  total,
  skip,
  limit,
  searchTerm,
  setSearchTerm,
  statusFilter,
  setStatusFilter,
  severityFilter,
  setSeverityFilter,
  resolvedFilter,
  setResolvedFilter,
  onPageChange,
  onInvestigate,
  onResolve,
  isLoading
}) {
  const searchInputRef = useRef(null);

  // Keyboard shortcut: Press '/' to focus search input
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '/' && document.activeElement !== searchInputRef.current) {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const statusTabs = [
    { key: "ALL", label: "All Records", icon: "📊" },
    { key: "MATCHED", label: "Matched", icon: "✓" },
    { key: "MISSING_PAYMENT", label: "Missing Payment", icon: "⚠️" },
    { key: "AMOUNT_MISMATCH", label: "Amount Mismatch", icon: "≠" },
    { key: "DUPLICATE_PAYMENT", label: "Duplicate", icon: "⎘" },
    { key: "SETTLEMENT_MISMATCH", label: "Settlement Deficit", icon: "🏦" },
    { key: "UNKNOWN_PAYMENT", label: "Orphan Gateway", icon: "❓" },
  ];

  const formatINR = (val) => {
    if (val === null || val === undefined) return "₹0.00";
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(val);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "MATCHED":
        return <span className="status-badge badge-matched"><span className="status-dot"></span>MATCHED</span>;
      case "MISSING_PAYMENT":
        return <span className="status-badge badge-missing"><span className="status-dot"></span>MISSING PAYMENT</span>;
      case "AMOUNT_MISMATCH":
        return <span className="status-badge badge-mismatch"><span className="status-dot"></span>AMOUNT MISMATCH</span>;
      case "DUPLICATE_PAYMENT":
        return <span className="status-badge badge-duplicate"><span className="status-dot"></span>DUPLICATE CHARGE</span>;
      case "SETTLEMENT_MISMATCH":
        return <span className="status-badge badge-settlement"><span className="status-dot"></span>BANK DEFICIT</span>;
      case "UNKNOWN_PAYMENT":
        return <span className="status-badge badge-unknown"><span className="status-dot"></span>ORPHAN GATEWAY</span>;
      default:
        return <span className="status-badge">{status}</span>;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case "HIGH":
        return <span className="badge badge-rose badge-glow-rose">CRITICAL</span>;
      case "MEDIUM":
        return <span className="badge badge-amber">MED</span>;
      case "LOW":
        return <span className="badge badge-cyan">LOW</span>;
      default:
        return <span className="badge badge-muted">NONE</span>;
    }
  };

  const getPaymentMethodPill = (method) => {
    const m = (method || "").toUpperCase();
    if (m.includes("UPI")) {
      return (
        <span className="payment-method-pill pill-upi">
          <Zap size={10} /> UPI
        </span>
      );
    }
    if (m.includes("CARD") || m.includes("CREDIT") || m.includes("DEBIT")) {
      return (
        <span className="payment-method-pill pill-card">
          <CreditCard size={10} /> Card
        </span>
      );
    }
    if (m.includes("NETBANKING") || m.includes("NET")) {
      return (
        <span className="payment-method-pill pill-netbanking">
          <Building2 size={10} /> Netbanking
        </span>
      );
    }
    return (
      <span className="payment-method-pill pill-wallet">
        <Wallet size={10} /> {method || "Digital"}
      </span>
    );
  };

  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="workbench glass-panel">
      {/* Search and Filters Bar */}
      <div className="workbench-toolbar">
        <div className="search-box">
          <Search size={16} className="search-icon" />
          <input 
            ref={searchInputRef}
            type="text" 
            placeholder="Search Order ID, Customer name, Payment ID, UTR..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          {searchTerm ? (
            <button 
              className="clear-search-btn"
              onClick={() => setSearchTerm("")}
              title="Clear search"
            >
              ✕
            </button>
          ) : (
            <kbd className="kbd-shortcut" title="Press / to focus">/</kbd>
          )}
        </div>

        <div className="toolbar-controls">
          {/* Severity Dropdown */}
          <div className="filter-dropdown-group">
            <span className="control-label">Severity:</span>
            <select 
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="select-input"
            >
              <option value="ALL">All Severities</option>
              <option value="HIGH">Critical / High</option>
              <option value="MEDIUM">Medium Severity</option>
              <option value="LOW">Low Severity</option>
            </select>
          </div>

          {/* Resolution Filter Buttons */}
          <div className="segmented-control">
            <button 
              className={`seg-btn ${resolvedFilter === null ? 'active' : ''}`}
              onClick={() => setResolvedFilter(null)}
            >
              All Status
            </button>
            <button 
              className={`seg-btn ${resolvedFilter === false ? 'active' : ''}`}
              onClick={() => setResolvedFilter(false)}
            >
              Unresolved
            </button>
            <button 
              className={`seg-btn ${resolvedFilter === true ? 'active' : ''}`}
              onClick={() => setResolvedFilter(true)}
            >
              Resolved
            </button>
          </div>
        </div>
      </div>

      {/* Status Category Tabs */}
      <div className="status-tabs-container">
        {statusTabs.map((tab) => (
          <button
            key={tab.key}
            className={`status-tab-btn ${statusFilter === tab.key ? 'active' : ''}`}
            onClick={() => setStatusFilter(tab.key)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Data Table */}
      <div className="table-wrapper">
        <table className="reconcile-table">
          <thead>
            <tr>
              <th>Order ID & Timestamp</th>
              <th>Customer & Method</th>
              <th className="text-right">Order Amount</th>
              <th className="text-right">Gateway Received</th>
              <th className="text-right">Exposure / Diff</th>
              <th>Status Classification</th>
              <th>Severity</th>
              <th>Resolution State</th>
              <th className="text-center">Forensic Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="9" className="text-center py-12 text-muted">
                  <div className="flex-center-gap">
                    <span className="spinner-border"></span>
                    <span>Scanning DhanSetu 3-way reconciliation ledger...</span>
                  </div>
                </td>
              </tr>
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan="9" className="text-center py-12 text-muted empty-state-box">
                  <FileCheck size={36} className="text-muted mb-2 text-indigo" />
                  <p className="font-semibold text-primary">No transactions match the selected filters</p>
                  <p className="text-xs text-muted mt-1">Try resetting your filters or search query.</p>
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr key={tx.id} className={tx.is_resolved ? 'row-resolved' : 'row-active'}>
                  {/* Order ID */}
                  <td>
                    <div className="order-id-cell">
                      <span className="mono font-semibold text-primary">{tx.order_id}</span>
                      <span className="text-xs text-muted mono">{tx.created_at?.slice(0, 16)}</span>
                    </div>
                  </td>

                  {/* Customer & Method */}
                  <td>
                    <div className="customer-cell">
                      <span className="customer-name">{tx.customer}</span>
                      {getPaymentMethodPill(tx.payment_method)}
                    </div>
                  </td>

                  {/* Expected */}
                  <td className="text-right mono font-medium">
                    {formatINR(tx.expected_amount)}
                  </td>

                  {/* Received */}
                  <td className="text-right mono">
                    {tx.received_amount > 0 ? (
                      <span className="text-primary font-medium">{formatINR(tx.received_amount)}</span>
                    ) : (
                      <span className="text-muted">₹0.00</span>
                    )}
                  </td>

                  {/* Exposure / Diff */}
                  <td className="text-right mono">
                    {tx.exposure_amount > 0 ? (
                      <span className="text-rose font-bold exposure-glow">
                        {formatINR(tx.exposure_amount)}
                      </span>
                    ) : tx.difference !== 0 ? (
                      <span className="text-amber font-semibold">
                        {tx.difference > 0 ? `+${formatINR(tx.difference)}` : formatINR(tx.difference)}
                      </span>
                    ) : (
                      <span className="text-emerald font-semibold">₹0.00</span>
                    )}
                  </td>

                  {/* Classification */}
                  <td>
                    {getStatusBadge(tx.status)}
                  </td>

                  {/* Severity */}
                  <td>
                    {getSeverityBadge(tx.severity)}
                  </td>

                  {/* Resolution */}
                  <td>
                    {tx.is_resolved ? (
                      <span className="resolved-pill" title={tx.resolution_note || "Resolved"}>
                        <CheckCircle2 size={12} />
                        <span>Resolved</span>
                      </span>
                    ) : (
                      <span className="unresolved-pill">
                        <span className="pulse-dot-amber"></span>
                        <span>Pending</span>
                      </span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="text-center">
                    <div className="action-buttons-cell">
                      {tx.status !== "MATCHED" && (
                        <button 
                          className="btn-action btn-action-ai"
                          onClick={() => onInvestigate(tx)}
                          title="Run AI Forensic Root Cause Analysis"
                        >
                          <Sparkles size={13} className="ai-sparkle-icon" />
                          <span>AI Investigate</span>
                        </button>
                      )}

                      {!tx.is_resolved && tx.status !== "MATCHED" && (
                        <button 
                          className="btn-action btn-action-resolve"
                          onClick={() => onResolve(tx)}
                          title="Mark exception as resolved with operator note"
                        >
                          <CheckCircle2 size={13} />
                          <span>Resolve</span>
                        </button>
                      )}

                      {tx.status === "MATCHED" && (
                        <button 
                          className="btn-action btn-action-matched"
                          onClick={() => onInvestigate(tx)}
                          title="View 3-Way verification proof"
                        >
                          <Eye size={12} />
                          <span>Verified</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="workbench-pagination">
        <span className="text-sm text-muted">
          Showing <span className="mono font-semibold text-primary">{total > 0 ? skip + 1 : 0}</span> to{' '}
          <span className="mono font-semibold text-primary">{Math.min(total, skip + transactions.length)}</span> of{' '}
          <span className="mono font-semibold text-primary">{total}</span> transactions
        </span>

        <div className="pagination-controls">
          <button 
            className="pagination-btn"
            disabled={currentPage <= 1}
            onClick={() => onPageChange(skip - limit)}
          >
            <ChevronLeft size={16} />
            <span>Prev</span>
          </button>

          <span className="page-indicator mono">
            {currentPage} / {totalPages}
          </span>

          <button 
            className="pagination-btn"
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange(skip + limit)}
          >
            <span>Next</span>
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
