import React, { useState, useRef, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  Send, 
  Bot, 
  User, 
  Lightbulb, 
  Check, 
  ExternalLink 
} from 'lucide-react';

export default function AiCopilotDrawer({
  isOpen,
  onClose,
  onSendQuery,
  chatMessages,
  isGenerating,
  onSelectOrder
}) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const suggestedPrompts = [
    "What is our largest financial exposure right now?",
    "Why are missing payments occurring in UPI?",
    "List top 3 anomalies requiring immediate CFO action",
    "How does the reconciliation engine handle gateway fees?"
  ];

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isGenerating) return;
    onSendQuery(inputValue);
    setInputValue('');
  };

  const handlePromptClick = (prompt) => {
    onSendQuery(prompt);
  };

  // Helper to render text with clickable order references
  const renderMessageContent = (content) => {
    // Regex matches ORD_XXXX or ORD-XXXX
    const parts = content.split(/(ORD[_-]\w+)/g);
    return parts.map((part, index) => {
      if (/^ORD[_-]\w+$/i.test(part)) {
        return (
          <button
            key={index}
            className="order-link-chip mono"
            onClick={() => onSelectOrder && onSelectOrder(part)}
            title={`Filter by ${part}`}
          >
            <span>{part}</span>
            <ExternalLink size={10} />
          </button>
        );
      }
      return part;
    });
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-container glass-panel animate-fade-in" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-title-row">
            <div className="copilot-avatar">
              <Sparkles size={18} className="text-indigo" />
            </div>
            <div>
              <h3 className="drawer-title">AI Finance Copilot</h3>
              <p className="drawer-subtitle">Grounded in live general ledger & gateway metrics</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Messages Scroll Area */}
        <div className="drawer-messages">
          {chatMessages.length === 0 ? (
            <div className="copilot-welcome-box">
              <div className="copilot-hero-icon">
                <Bot size={36} className="text-indigo" />
              </div>
              <h4 className="font-semibold text-lg text-primary">Autonomous Finance Intelligence</h4>
              <p className="text-sm text-muted mt-1 text-center">
                Ask any question regarding payment gateway settlement delays, missing webhooks, customer duplicate deductions, or accounting adjustments.
              </p>

              <div className="suggested-prompts-box mt-4">
                <div className="flex-center-gap text-xs text-muted mb-2">
                  <Lightbulb size={13} className="text-amber" />
                  <span>SUGGESTED QUERIES</span>
                </div>
                <div className="prompts-list">
                  {suggestedPrompts.map((prompt, i) => (
                    <button
                      key={i}
                      className="prompt-chip-btn"
                      onClick={() => handlePromptClick(prompt)}
                      disabled={isGenerating}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            chatMessages.map((msg, i) => (
              <div 
                key={i} 
                className={`chat-bubble-row ${msg.role === 'user' ? 'chat-row-user' : 'chat-row-ai'}`}
              >
                <div className="chat-avatar">
                  {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div className="chat-bubble">
                  <div className="chat-bubble-content">
                    {renderMessageContent(msg.content)}
                  </div>
                </div>
              </div>
            ))
          )}

          {isGenerating && (
            <div className="chat-bubble-row chat-row-ai">
              <div className="chat-avatar">
                <Bot size={14} />
              </div>
              <div className="chat-bubble">
                <div className="flex-center-gap text-muted text-sm">
                  <Sparkles size={14} className="animate-spin text-indigo" />
                  <span>Analyzing ledger & transaction logs...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSubmit} className="drawer-input-form">
          <input 
            type="text"
            className="drawer-input"
            placeholder="Ask AI Finance Controller anything..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isGenerating}
          />
          <button 
            type="submit" 
            className="btn-send"
            disabled={!inputValue.trim() || isGenerating}
            title="Send Message"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
