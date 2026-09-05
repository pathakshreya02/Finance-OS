import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import MetricsRibbon from './components/MetricsRibbon';
import ReconciliationWorkbench from './components/ReconciliationWorkbench';
import InvestigationModal from './components/InvestigationModal';
import CfoBriefModal from './components/CfoBriefModal';
import AiCopilotDrawer from './components/AiCopilotDrawer';
import UploadCsvModal from './components/UploadCsvModal';
import AuditTrailModal from './components/AuditTrailModal';
import MoneyFlowVisualizer from './components/MoneyFlowVisualizer';
import FeeLeakageModal from './components/FeeLeakageModal';
import './App.css';

export default function App() {
  // Reconciliation Data State
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [skip, setSkip] = useState(0);
  const limit = 50;

  // Filter States
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [resolvedFilter, setResolvedFilter] = useState(null);

  // Loading States
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [isGeneratingBrief, setIsGeneratingBrief] = useState(false);
  const [isChatGenerating, setIsChatGenerating] = useState(false);

  // Modals & Panels State
  const [activeInvestigationTx, setActiveInvestigationTx] = useState(null);
  const [investigationData, setInvestigationData] = useState(null);
  const [isCfoBriefOpen, setIsCfoBriefOpen] = useState(false);
  const [cfoBriefData, setCfoBriefData] = useState(null);
  const [isAuditTrailOpen, setIsAuditTrailOpen] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  // Copilot Chat History
  const [chatMessages, setChatMessages] = useState([]);

  // New Feature States
  const [isFeeAuditOpen, setIsFeeAuditOpen] = useState(false);
  const [isSimulatingWebhook, setIsSimulatingWebhook] = useState(false);
  const [webhookToast, setWebhookToast] = useState(null);

  // Fetch Summary
  const fetchSummary = async () => {
    try {
      const res = await fetch('/api/reconcile/summary');
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error("Failed to fetch summary:", err);
    }
  };

  // Fetch Transactions with Active Filters
  const fetchTransactions = useCallback(async (currentSkip = skip) => {
    setIsLoadingData(true);
    try {
      const params = new URLSearchParams();
      params.set('skip', currentSkip.toString());
      params.set('limit', limit.toString());

      if (searchTerm.trim()) {
        params.set('search', searchTerm.trim());
      }
      if (statusFilter !== 'ALL') {
        params.set('status', statusFilter);
      }
      if (severityFilter !== 'ALL') {
        params.set('severity', severityFilter);
      }
      if (resolvedFilter !== null) {
        params.set('is_resolved', resolvedFilter.toString());
      }

      const res = await fetch(`/api/reconcile/transactions?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setTransactions(data.items || []);
        setTotalRecords(data.total || 0);
      }
    } catch (err) {
      console.error("Failed to fetch transactions:", err);
    } finally {
      setIsLoadingData(false);
    }
  }, [skip, limit, searchTerm, statusFilter, severityFilter, resolvedFilter]);

  // Initial Load
  useEffect(() => {
    fetchSummary();
    fetchTransactions(0);
  }, []);

  // Re-fetch transactions when filters change
  useEffect(() => {
    setSkip(0);
    fetchTransactions(0);
  }, [searchTerm, statusFilter, severityFilter, resolvedFilter]);

  // Handle Page Change
  const handlePageChange = (newSkip) => {
    setSkip(newSkip);
    fetchTransactions(newSkip);
  };

  // Seed Synthetic Data
  const handleSeedData = async (count = 150) => {
    setIsSeeding(true);
    try {
      const res = await fetch(`/api/reconcile/seed?count=${count}`, {
        method: 'POST'
      });
      if (res.ok) {
        const sum = await res.json();
        setSummary(sum);
        setSkip(0);
        await fetchTransactions(0);
      }
    } catch (err) {
      console.error("Failed to seed data:", err);
    } finally {
      setIsSeeding(false);
    }
  };

  // Upload Custom CSVs
  const handleUploadSubmit = async (formData) => {
    setIsUploading(true);
    try {
      const res = await fetch('/api/reconcile/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const sum = await res.json();
        setSummary(sum);
        setIsUploadOpen(false);
        setSkip(0);
        await fetchTransactions(0);
      } else {
        const errorData = await res.json();
        alert(`Upload error: ${errorData.detail || "Failed to parse files"}`);
      }
    } catch (err) {
      console.error("Failed to upload CSV:", err);
      alert("Network error while uploading CSV files.");
    } finally {
      setIsUploading(false);
    }
  };

  // Investigate Transaction with AI
  const handleInvestigate = async (tx) => {
    setActiveInvestigationTx(tx);
    setInvestigationData(null);
    setIsInvestigating(true);

    try {
      const res = await fetch('/api/ai/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_id: tx.id })
      });

      if (res.ok) {
        const data = await res.json();
        setInvestigationData(data);
      } else {
        console.error("AI Investigation failed");
      }
    } catch (err) {
      console.error("Investigation network error:", err);
    } finally {
      setIsInvestigating(false);
    }
  };

  // Resolve Exception
  const handleSubmitResolution = async (txId, note) => {
    setIsResolving(true);
    try {
      const res = await fetch('/api/reconcile/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: txId,
          resolution_note: note
        })
      });

      if (res.ok) {
        const updatedTx = await res.json();
        // Update local list
        setTransactions((prev) => 
          prev.map((t) => (t.id === updatedTx.id ? updatedTx : t))
        );
        if (activeInvestigationTx && activeInvestigationTx.id === updatedTx.id) {
          setActiveInvestigationTx(updatedTx);
        }
        await fetchSummary();
      }
    } catch (err) {
      console.error("Resolution error:", err);
    } finally {
      setIsResolving(false);
    }
  };

  // Open CFO Brief
  const handleOpenCfoBrief = async () => {
    setIsCfoBriefOpen(true);
    if (!cfoBriefData) {
      setIsGeneratingBrief(true);
      try {
        const res = await fetch('/api/ai/cfo-brief', { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          setCfoBriefData(data);
        }
      } catch (err) {
        console.error("CFO brief generation error:", err);
      } finally {
        setIsGeneratingBrief(false);
      }
    }
  };

  // Open Audit Trail
  const handleOpenAuditTrail = async () => {
    setIsAuditTrailOpen(true);
    try {
      const res = await fetch('/api/audit-trail');
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data || []);
      }
    } catch (err) {
      console.error("Audit trail fetch error:", err);
    }
  };

  // AI Copilot Chat
  const handleSendCopilotQuery = async (queryText) => {
    const userMsg = { role: 'user', content: queryText };
    const updatedHistory = [...chatMessages, userMsg];
    setChatMessages(updatedHistory);
    setIsChatGenerating(true);

    try {
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: updatedHistory,
          focus_order_id: activeInvestigationTx?.order_id || null
        })
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
      } else {
        setChatMessages((prev) => [
          ...prev, 
          { role: 'assistant', content: "I encountered an error processing your query. Please retry." }
        ]);
      }
    } catch (err) {
      console.error("Copilot chat error:", err);
      setChatMessages((prev) => [
        ...prev, 
        { role: 'assistant', content: "Network error communicating with AI Finance Controller." }
      ]);
    } finally {
      setIsChatGenerating(false);
    }
  };

  // Export CSV
  const handleExportCsv = () => {
    window.open('/api/reconcile/export', '_blank');
  };

  // Filter Workbench from order mention chip
  const handleSelectOrder = (orderId) => {
    setSearchTerm(orderId);
    setIsCopilotOpen(false);
  };

  // Simulate Live Webhook
  const handleSimulateWebhook = async () => {
    setIsSimulatingWebhook(true);
    const discrepancyTypes = ['NONE', 'NONE', 'NONE', 'AMOUNT_MISMATCH', 'MISSING_PAYMENT', 'SETTLEMENT_MISMATCH'];
    const methods = ['UPI', 'UPI', 'Credit Card', 'Debit Card', 'Netbanking'];
    const randomDisc = discrepancyTypes[Math.floor(Math.random() * discrepancyTypes.length)];
    const randomMethod = methods[Math.floor(Math.random() * methods.length)];
    const randomAmount = Math.round((Math.random() * 9000 + 1000) * 100) / 100;
    try {
      const res = await fetch('/api/webhooks/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: 'payment.captured',
          amount: randomAmount,
          customer: 'Live Gateway User',
          payment_method: randomMethod,
          simulate_discrepancy: randomDisc
        })
      });
      if (res.ok) {
        const data = await res.json();
        const isException = data.reconciled_transaction.status !== 'MATCHED';
        setWebhookToast({
          status: data.reconciled_transaction.status,
          order: data.reconciled_transaction.order_id,
          amount: randomAmount,
          method: randomMethod,
          isException
        });
        setSummary(data.summary);
        setSkip(0);
        await fetchTransactions(0);
        setTimeout(() => setWebhookToast(null), 5000);
      }
    } catch (err) {
      console.error('Webhook simulation error:', err);
    } finally {
      setIsSimulatingWebhook(false);
    }
  };

  // Listen for auto-refresh from action hub
  useEffect(() => {
    const handler = () => { fetchSummary(); fetchTransactions(0); };
    window.addEventListener('finance-refresh', handler);
    return () => window.removeEventListener('finance-refresh', handler);
  }, [fetchTransactions]);

  return (
    <div className="app-container">
      {/* Webhook Toast */}
      {webhookToast && (
        <div className={`webhook-toast ${webhookToast.isException ? 'webhook-toast-warn' : 'webhook-toast-ok'}`}>
          <span className="webhook-toast-icon">{webhookToast.isException ? '⚠️' : '⚡'}</span>
          <div className="webhook-toast-body">
            <strong>Live Webhook Ingested</strong>
            <span>{webhookToast.order} · {webhookToast.method} · ₹{webhookToast.amount.toLocaleString('en-IN')}</span>
            <span className={`webhook-toast-status ${webhookToast.isException ? 'rose' : 'emerald'}`}>{webhookToast.status}</span>
          </div>
          <button className="webhook-toast-close" onClick={() => setWebhookToast(null)}>✕</button>
        </div>
      )}

      {/* Top Navbar */}
      <Navbar 
        onSeedData={handleSeedData}
        isSeeding={isSeeding}
        onOpenUpload={() => setIsUploadOpen(true)}
        onOpenCfoBrief={handleOpenCfoBrief}
        onOpenAuditTrail={handleOpenAuditTrail}
        onToggleCopilot={() => setIsCopilotOpen(!isCopilotOpen)}
        isCopilotOpen={isCopilotOpen}
        onExportCsv={handleExportCsv}
        onOpenFeeAudit={() => setIsFeeAuditOpen(true)}
        onSimulateWebhook={handleSimulateWebhook}
        isSimulatingWebhook={isSimulatingWebhook}
        summary={summary}
      />

      {/* KPI Metrics Ribbon */}
      <MetricsRibbon 
        summary={summary}
        isLoading={isLoadingData && !summary}
      />

      {/* Live Money Flow Visualizer */}
      <MoneyFlowVisualizer summary={summary} transactions={transactions} />

      {/* Primary Reconciliation Workbench */}
      <ReconciliationWorkbench 
        transactions={transactions}
        total={totalRecords}
        skip={skip}
        limit={limit}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        severityFilter={severityFilter}
        setSeverityFilter={setSeverityFilter}
        resolvedFilter={resolvedFilter}
        setResolvedFilter={setResolvedFilter}
        onPageChange={handlePageChange}
        onInvestigate={handleInvestigate}
        onResolve={handleInvestigate}
        isLoading={isLoadingData}
      />

      {/* Investigation & Anomaly Modal */}
      {activeInvestigationTx && (
        <InvestigationModal 
          transaction={activeInvestigationTx}
          investigation={investigationData}
          isLoading={isInvestigating}
          onClose={() => {
            setActiveInvestigationTx(null);
            setInvestigationData(null);
          }}
          onSubmitResolution={handleSubmitResolution}
          isResolving={isResolving}
        />
      )}

      {/* CFO Executive Strategic Brief Modal */}
      {isCfoBriefOpen && (
        <CfoBriefModal 
          brief={cfoBriefData}
          isLoading={isGeneratingBrief}
          onClose={() => setIsCfoBriefOpen(false)}
        />
      )}

      {/* Data Ingestion CSV Studio Modal */}
      <UploadCsvModal 
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSubmit={handleUploadSubmit}
        isUploading={isUploading}
      />

      {/* Audit Trail Modal */}
      {isAuditTrailOpen && (
        <AuditTrailModal 
          auditLogs={auditLogs}
          isLoading={false}
          onClose={() => setIsAuditTrailOpen(false)}
        />
      )}

      {/* Fee Leakage & GST Audit Modal */}
      {isFeeAuditOpen && (
        <FeeLeakageModal onClose={() => setIsFeeAuditOpen(false)} />
      )}

      {/* AI Copilot Side Drawer */}
      <AiCopilotDrawer 
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        onSendQuery={handleSendCopilotQuery}
        chatMessages={chatMessages}
        isGenerating={isChatGenerating}
        onSelectOrder={handleSelectOrder}
      />
    </div>
  );
}
