import React, { useState } from "react";
import { RetrievalMode } from "../App";

interface ChatAreaProps {
  hasData: boolean;
  retrievalMode: RetrievalMode;
  onRunRetrieval: (query: string) => void;
  hasChatModel: boolean;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  hasData,
  retrievalMode,
  onRunRetrieval,
  hasChatModel,
}) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasData || !query.trim()) return;
    onRunRetrieval(query.trim());
  };

  const retrievalLabel = (() => {
    switch (retrievalMode) {
      case "semantic":
        return "Semantic Retrieval";
      case "keyword":
        return "Keyword Retrieval";
      case "hybrid":
        return "Hybrid Retrieval";
      case "semantic_mmr":
        return "Semantic + MMR";
      default:
        return "Retrieval";
    }
  })();

  return (
    <section className="chat-area">
      <header className="chat-header">
        <div>
          <h2 className="chat-title">RAG Playground</h2>
          <p className="chat-subtitle">
            Welcome to RAG - Playground. Please upload data, test retrieval and chat with your data.
          </p>
        </div>
        <div className="chat-status">
          <span
            className={`status-dot ${hasData ? "online" : "offline"}`}
            aria-hidden="true"
          />
          <span className="status-text">
            {hasData ? "Data available" : "Waiting for uploads"}
          </span>
        </div>
      </header>

      <div className="chat-body">
        {!hasData ? (
          <div className="empty-state">
            <h3>Upload data to begin</h3>
            <p>
              Use the <strong>Data</strong> tab on the left to upload PDF, DOC/DOCX,
              or TXT files. Once indexing is complete, you can run{" "}
              <strong>{retrievalLabel}</strong> experiments here.
            </p>
          </div>
        ) : (
          <div className="chat-log">
            <div className="chat-message system-message">
              Try a question like &ldquo;Summarize the main concepts in my
              documents&rdquo; to test the hybrid search.
            </div>
          </div>
        )}
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder={
            hasData
              ? "Ask a question over your uploaded documents..."
              : "Upload data to enable chat"
          }
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={!hasData}
        />
        <button
          type="submit"
          className="chat-send-button"
          disabled={!hasData || !query.trim()}
        >
          {hasChatModel
            ? `Run ${retrievalLabel} + Chat`
            : `Run ${retrievalLabel}`}
        </button>
      </form>
    </section>
  );
};

