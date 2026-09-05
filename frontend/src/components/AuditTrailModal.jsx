import React, { useState } from 'react';
import { 
  X, 
  History, 
  Search, 
  ShieldCheck, 
  Filter,
  CheckCircle2,
  FileText
} from 'lucide-react';

export default function AuditTrailModal({
  auditLogs,
  isLoading,
  onClose
}) {
  const [filterQuery, setFilterQuery] = useState('');

  const filteredLogs = auditLogs.filter((log) => {
    if (!filterQuery) return true;
    const q = filterQuery.toLowerCase();
    return (
      log.entity_id?.toLowerCase().includes(q) ||
      log.action?.toLowerCase().includes(q) ||
      log.actor?.toLowerCase().includes(q) ||
      log.rule_code?.toLowerCase().includes(q) ||
      log.details?.toLowerCase().includes(q)
    );
  });

  const getActionBadge = (action) => {
    if (action.includes("COMPLETE")) {
      return <span className="badge badge-emerald">{action}</span>;
    }
    if (action.includes("RESOLUTION")) {
      return <span className="badge badge-indigo">{action}</span>;
    }
    if (action.includes("MISMATCH") || action.includes("MISSING")) {
      return <span className="badge badge-rose">{action}</span>;
    }
    return <span className="badge badge-cyan">{action}</span>;
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-container glass-panel modal-lg animate-fade-in">
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-badge-row">
              <span className="badge badge-emerald flex-center-gap">
                <ShieldCheck size={13} />
                <span>COMPLIANCE & SOX AUDIT LOG</span>
              </span>
              <span className="badge badge-muted mono">{auditLogs.length} EVENTS</span>
            </div>
            <h2 className="modal-title">Immutable Financial Audit Trail</h2>
            <p className="modal-subtitle">
              Cryptographically ordered event log tracking automated reconciliation executions and operator interventions.
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Search */}
        <div className="audit-search-bar px-6 pt-3">
          <div className="search-box">
            <Search size={16} className="search-icon" />
            <input 
              type="text"
              placeholder="Search audit trail by entity, actor, or rule..."
              className="search-input"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Body Table */}
        <div className="modal-body-scroll">
          {isLoading ? (
            <div className="text-center py-12 text-muted">
              <span>Loading audit trail...</span>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-12 text-muted">
              <p>No audit events found.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="reconcile-table audit-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Action</th>
                    <th>Entity ID</th>
                    <th>Actor</th>
                    <th>Rule Code</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((log) => (
                    <tr key={log.id}>
                      <td className="mono text-xs text-muted">
                        {log.timestamp}
                      </td>
                      <td>
                        {getActionBadge(log.action)}
                      </td>
                      <td className="mono font-semibold">
                        {log.entity_id}
                      </td>
                      <td className="text-sm">
                        {log.actor}
                      </td>
                      <td className="mono text-xs text-muted">
                        {log.rule_code}
                      </td>
                      <td className="text-sm text-secondary">
                        {log.details}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
