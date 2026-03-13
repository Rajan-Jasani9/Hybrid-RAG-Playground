import React, { useState } from "react";
import { Microscope } from "lucide-react";
import { RetrievalMode, IngestedDocument } from "../App";

interface SidebarProps {
  onFilesUploaded: (files: FileList | null) => void;
  isUploading: boolean;
  documents: IngestedDocument[];
  selectedModelFamily: string;
  onChangeModelFamily: (value: string) => void;
  selectedModel: string;
  onChangeModel: (value: string) => void;
  apiKey: string;
  onChangeApiKey: (value: string) => void;
  retrievalMode: RetrievalMode;
  onChangeRetrievalMode: (mode: RetrievalMode) => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

type Tab = "data" | "config";

export const Sidebar: React.FC<SidebarProps> = ({
  onFilesUploaded,
  isUploading,
  documents,
  selectedModelFamily,
  onChangeModelFamily,
  selectedModel,
  onChangeModel,
  apiKey,
  onChangeApiKey,
  retrievalMode,
  onChangeRetrievalMode,
  theme,
  onToggleTheme,
}) => {
  const [activeTab, setActiveTab] = useState<Tab>("data");

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">
          <span className="sidebar-logo">
            <Microscope size={18} strokeWidth={2} />
          </span>
          <span>RAG Playground</span>
        </h1>
        <p className="sidebar-subtitle">Data &amp; Configuration</p>
      </div>

      <div className="sidebar-tabs">
        <button
          className={`sidebar-tab ${activeTab === "data" ? "active" : ""}`}
          onClick={() => setActiveTab("data")}
        >
          Data
        </button>
        <button
          className={`sidebar-tab ${activeTab === "config" ? "active" : ""}`}
          onClick={() => setActiveTab("config")}
        >
          Configurations
        </button>
      </div>

      <div className="sidebar-content">
        {activeTab === "data" ? (
          <div className="panel">
            <h2 className="panel-title">Upload documents</h2>
            <p className="panel-description">
              Upload one or more files to index into the Hybrid RAG backend.
            </p>
            <p className="panel-warning">
              Note: This version does not currently support OCR. Only embedded text in
              PDF/DOC/DOCX/TXT files will be indexed.
            </p>

            <label className="upload-area">
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                multiple
                onChange={(e) => onFilesUploaded(e.target.files)}
                disabled={isUploading}
              />
              <span className="upload-title">
                {isUploading ? "Uploading & queuing..." : "Drop files here or click to browse"}
              </span>
              <span className="upload-hint">Supported: PDF, DOC, DOCX, TXT</span>
            </label>

            {documents.length > 0 && (
              <div className="ingestion-list">
                <div className="ingestion-list-header">
                  <span>Recent ingestions</span>
                </div>
                <ul>
                  {documents.slice(-5).map((doc) => (
                    <li key={doc.id} className="ingestion-list-item">
                      <span className="ingestion-filename" title={doc.filename}>
                        {doc.filename}
                      </span>
                      <span className={`ingestion-status ingestion-status-${doc.status}`}>
                        {doc.status}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="panel">
              <h2 className="panel-title">Retrieval configuration</h2>
              <p className="panel-description">
                Configure how documents are scored and retrieved from your index.
              </p>

              <div className="field-group">
                <label className="field-label" htmlFor="retrieval-mode">
                  Retrieval mode
                </label>
                <select
                  id="retrieval-mode"
                  className="field-input"
                  value={retrievalMode}
                  onChange={(e) =>
                    onChangeRetrievalMode(e.target.value as RetrievalMode)
                  }
                >
                  <option value="semantic">Semantic Retrieval</option>
                  <option value="keyword">Keyword Retrieval</option>
                  <option value="hybrid">Hybrid Retrieval</option>
                  <option value="semantic_mmr">Semantic + MMR</option>
                </select>
                <p className="field-hint">
                  Choose between vector search, BM25, or a hybrid strategy.
                </p>
              </div>
            </div>

            <div className="panel" style={{ marginTop: 12 }}>
              <h2 className="panel-title">Chat model configuration</h2>
              <p className="panel-description">
                Optional. If no chat model is set, queries will only run retrieval.
              </p>

              <div className="field-group">
                <label className="field-label" htmlFor="model-family">
                  Chat model family
                </label>
                <select
                  id="model-family"
                  className="field-input"
                  value={selectedModelFamily}
                  onChange={(e) => onChangeModelFamily(e.target.value)}
                >
                  <option value="">Select a model family</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="azure-openai">Azure OpenAI</option>
                </select>
              </div>

              <div className="field-group">
                <label className="field-label" htmlFor="model">
                  Chat model (per family)
                </label>
                <select
                  id="model"
                  className="field-input"
                  value={selectedModel}
                  onChange={(e) => onChangeModel(e.target.value)}
                  disabled={!selectedModelFamily}
                >
                  <option value="">
                    {selectedModelFamily
                      ? "Select a chat model"
                      : "Select a family first"}
                  </option>
                  {selectedModelFamily === "openai" && (
                    <>
                      <option value="gpt-4o-mini">gpt-4o-mini</option>
                      <option value="gpt-4.1-mini">gpt-4.1-mini</option>
                    </>
                  )}
                  {selectedModelFamily === "anthropic" && (
                    <>
                      <option value="claude-3-5-sonnet-20241022">
                        claude-3-5-sonnet-20241022
                      </option>
                      <option value="claude-3-5-haiku-20241022">
                        claude-3-5-haiku-20241022
                      </option>
                      <option value="claude-3-opus-20240229">
                        claude-3-opus-20240229
                      </option>
                    </>
                  )}
                  {selectedModelFamily === "azure-openai" && (
                    <>
                      <option value="gpt-4o-mini-azure">gpt-4o-mini (Azure)</option>
                      <option value="gpt-4.1-mini-azure">
                        gpt-4.1-mini (Azure)
                      </option>
                    </>
                  )}
                </select>
                <p className="field-hint">
                  Only chat-capable models are shown here (no embedding models).
                </p>
              </div>

              <div className="field-group">
                <label className="field-label" htmlFor="api-key">
                  Chat API key for selected family
                </label>
                <input
                  id="api-key"
                  type="password"
                  className="field-input"
                  placeholder="Enter API key"
                  value={apiKey}
                  onChange={(e) => onChangeApiKey(e.target.value)}
                />
                <p className="field-hint">
                  Used only when running chat over retrieved chunks.
                </p>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="sidebar-footer">
        <button
          type="button"
          className="theme-toggle"
          onClick={onToggleTheme}
        >
          <span className="theme-toggle-indicator">
            <span
              className={`theme-toggle-thumb ${
                theme === "dark" ? "theme-toggle-thumb-dark" : ""
              }`}
            />
          </span>
          <span className="theme-toggle-label">
            {theme === "dark" ? "Dark mode" : "Light mode"}
          </span>
        </button>
      </div>
    </aside>
  );
};

