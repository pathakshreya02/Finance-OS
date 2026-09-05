import React, { useState } from 'react';
import { 
  X, 
  UploadCloud, 
  FileSpreadsheet, 
  Download, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export default function UploadCsvModal({
  isOpen,
  onClose,
  onUploadSubmit,
  isUploading
}) {
  const [ordersFile, setOrdersFile] = useState(null);
  const [paymentsFile, setPaymentsFile] = useState(null);
  const [settlementsFile, setSettlementsFile] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ordersFile || !paymentsFile) {
      setErrorMsg("Please select both Orders CSV and Payments CSV files.");
      return;
    }
    setErrorMsg('');
    const formData = new FormData();
    formData.append("orders_file", ordersFile);
    formData.append("payments_file", paymentsFile);
    if (settlementsFile) {
      formData.append("settlements_file", settlementsFile);
    }
    onUploadSubmit(formData);
  };

  const handleDownloadSample = (type) => {
    window.open(`/api/sample-csv/${type}`, '_blank');
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-container glass-panel modal-md animate-fade-in">
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-badge-row">
              <span className="badge badge-cyan flex-center-gap">
                <UploadCloud size={13} />
                <span>DATA INGESTION STUDIO</span>
              </span>
            </div>
            <h2 className="modal-title">Upload Financial Ledgers</h2>
            <p className="modal-subtitle">
              Import ERP sales orders, Razorpay gateway payment captures, and bank settlement reports.
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body-scroll">
          {errorMsg && (
            <div className="alert-box alert-rose">
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Sample CSV Download Helpers */}
          <div className="sample-csv-banner">
            <span className="text-xs text-muted">Need template files?</span>
            <div className="sample-buttons-row">
              <button 
                type="button" 
                className="btn-sample-download"
                onClick={() => handleDownloadSample('orders')}
              >
                <Download size={12} />
                <span>Sample Orders.csv</span>
              </button>
              <button 
                type="button" 
                className="btn-sample-download"
                onClick={() => handleDownloadSample('payments')}
              >
                <Download size={12} />
                <span>Sample Payments.csv</span>
              </button>
            </div>
          </div>

          {/* File Upload Fields */}
          <div className="upload-fields-stack mt-4">
            {/* 1. Orders File */}
            <div className="file-field-box">
              <label className="file-field-label">
                <span>1. ERP Orders CSV</span>
                <span className="text-rose text-xs">*Required</span>
              </label>
              <input 
                type="file" 
                accept=".csv"
                className="file-input-control"
                onChange={(e) => setOrdersFile(e.target.files[0] || null)}
                required
              />
              <span className="file-hint">Expected columns: order_id, order_amount, customer, created_at</span>
            </div>

            {/* 2. Payments File */}
            <div className="file-field-box mt-3">
              <label className="file-field-label">
                <span>2. Razorpay Gateway Payments CSV</span>
                <span className="text-rose text-xs">*Required</span>
              </label>
              <input 
                type="file" 
                accept=".csv"
                className="file-input-control"
                onChange={(e) => setPaymentsFile(e.target.files[0] || null)}
                required
              />
              <span className="file-hint">Expected columns: payment_id, order_id, payment_amount, gateway_fee, status</span>
            </div>

            {/* 3. Settlements File */}
            <div className="file-field-box mt-3">
              <label className="file-field-label">
                <span>3. Bank Settlements CSV</span>
                <span className="text-muted text-xs">Optional (3-Way Matching)</span>
              </label>
              <input 
                type="file" 
                accept=".csv"
                className="file-input-control"
                onChange={(e) => setSettlementsFile(e.target.files[0] || null)}
              />
              <span className="file-hint">Expected columns: settlement_id, order_id, settled_amount, utr_number</span>
            </div>
          </div>

          <div className="modal-footer-actions mt-5">
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={onClose}
              disabled={isUploading}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-indigo"
              disabled={isUploading}
            >
              {isUploading ? (
                <span className="flex-center-gap">
                  <span className="spinner-border"></span>
                  <span>Reconciling CSVs...</span>
                </span>
              ) : (
                <span className="flex-center-gap">
                  <UploadCloud size={16} />
                  <span>Run Reconciliation</span>
                </span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
