import React from 'react';
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
  RotateCcw
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
  const statusTabs = [
    { key: "ALL", label: "All Records" },
    { key: "MATCHED", label: "Matched" },
    { key: "MISSING_PAYMENT", label: "Missing Payment" },
    { key: "AMOUNT_MISMATCH", label: "Amount Mismatch" },
    { key: "DUPLICATE_PAYMENT", label: "Duplicate" },
    { key: "SETTLEMENT_MISMATCH", label: "Settlement Mismatch" },
    { key: "UNKNOWN_PAYMENT", label: "Unknown Gateway" },
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
        return <span className="status-badge badge-matched">MATCHED</span>;
      case "MISSING_PAYMENT":
        return <span className="status-badge badge-missing">MISSING PAYMENT</span>;
      case "AMOUNT_MISMATCH":
        return <span className="status-badge badge-mismatch">AMOUNT MISMATCH</span>;
      case "DUPLICATE_PAYMENT":
        return <span className="status-badge badge-duplicate">DUPLICATE</span>;
      case "SETTLEMENT_MISMATCH":
        return <span className="status-badge badge-settlement">SETTLE MISMATCH</span>;
      case "UNKNOWN_PAYMENT":
        return <span className="status-badge badge-unknown">UNKNOWN EVENT</span>;
      default:
        return <span className="status-badge">{status}</span>;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case "HIGH":
        return <span className="badge badge-rose">HIGH</span>;
      case "MEDIUM":
        return <span className="badge badge-amber">MED</span>;
      case "LOW":
        return <span className="badge badge-cyan">LOW</span>;
      default:
        return <span className="badge badge-muted">NONE</span>;
    }
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
            type="text" 
            placeholder="Search Order ID, Customer, Payment ID..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
            }}
            className="search-input"
          />
          {searchTerm && (
            <button 
              className="clear-search-btn"
              onClick={() => setSearchTerm("")}
            >
              ✕
            </button>
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
              <option value="HIGH">High Severity</option>
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
              All
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
            {tab.label}
          </button>
        ))}
      </div>

      {/* Data Table */}
      <div className="table-wrapper">
        <table className="reconcile-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer & Method</th>
              <th className="text-right">Expected</th>
              <th className="text-right">Received</th>
              <th className="text-right">Exposure / Diff</th>
              <th>Classification</th>
              <th>Severity</th>
              <th>Resolution</th>
              <th className="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="9" className="text-center py-12 text-muted">
                  <div className="flex-center-gap">
                    <span className="spinner-border"></span>
                    <span>Scanning reconciliation records...</span>
                  </div>
                </td>
              </tr>
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan="9" className="text-center py-12 text-muted empty-state-box">
                  <FileCheck size={32} className="text-muted mb-2" />
                  <p>No transactions match the selected filters.</p>
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr key={tx.id} className={tx.is_resolved ? 'row-resolved' : ''}>
                  {/* Order ID */}
                  <td>
                    <div className="order-id-cell">
                      <span className="mono font-semibold">{tx.order_id}</span>
                      <span className="text-xs text-muted mono">{tx.created_at?.slice(0, 16)}</span>
                    </div>
                  </td>

                  {/* Customer & Method */}
                  <td>
                    <div className="customer-cell">
                      <span className="customer-name">{tx.customer}</span>
                      <span className="payment-method-pill">{tx.payment_method}</span>
                    </div>
                  </td>

                  {/* Expected */}
                  <td className="text-right mono">
                    {formatINR(tx.expected_amount)}
                  </td>

                  {/* Received */}
                  <td className="text-right mono">
                    {tx.received_amount > 0 ? (
                      formatINR(tx.received_amount)
                    ) : (
                      <span className="text-muted">₹0.00</span>
                    )}
                  </td>

                  {/* Exposure / Diff */}
                  <td className="text-right mono">
                    {tx.exposure_amount > 0 ? (
                      <span className="text-rose font-semibold">
                        {formatINR(tx.exposure_amount)}
                      </span>
                    ) : tx.difference !== 0 ? (
                      <span className="text-amber">
                        {tx.difference > 0 ? `+${formatINR(tx.difference)}` : formatINR(tx.difference)}
                      </span>
                    ) : (
                      <span className="text-emerald">₹0.00</span>
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
                        <CheckCircle2 size={13} />
                        <span>Resolved</span>
                      </span>
                    ) : (
                      <span className="unresolved-pill">Pending</span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="text-center">
                    <div className="action-buttons-cell">
                      {tx.status !== "MATCHED" && (
                        <button 
                          className="btn-action btn-action-ai"
                          onClick={() => onInvestigate(tx)}
                          title="Run AI Root Cause Analysis"
                        >
                          <Sparkles size={13} />
                          <span>AI Investigate</span>
                        </button>
                      )}

                      {!tx.is_resolved && tx.status !== "MATCHED" && (
                        <button 
                          className="btn-action btn-action-resolve"
                          onClick={() => onResolve(tx)}
                          title="Mark exception as resolved"
                        >
                          <CheckCircle2 size={13} />
                          <span>Resolve</span>
                        </button>
                      )}

                      {tx.status === "MATCHED" && (
                        <span className="text-xs text-muted">Verified</span>
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
          Showing <span className="mono font-semibold text-primary">{Math.min(total, skip + 1)}</span> to{' '}
          <span className="mono font-semibold text-primary">{Math.min(total, skip + transactions.length)}</span> of{' '}
          <span className="mono font-semibold text-primary">{total}</span> records
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
