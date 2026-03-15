import React from "react";
import { RetrievedChunk, IngestedDocument } from "../services/api";

interface CitationModalProps {
  open: boolean;
  onClose: () => void;
  chunk: RetrievedChunk | null;
  document: IngestedDocument | null;
}

export const CitationModal: React.FC<CitationModalProps> = ({
  open,
  onClose,
  chunk,
  document,
}) => {
  if (!open || !chunk || !document) return null;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8200";
  const pdfUrl = `${API_BASE_URL}/api/documents/${document.id}/file`;
  const pdfUrlWithPage = chunk.pageNumber 
    ? `${pdfUrl}#page=${chunk.pageNumber}`
    : pdfUrl;

  return (
    <div className="citation-modal-overlay" onClick={onClose}>
      <div className="citation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="citation-modal-header">
          <h2 className="citation-modal-title">Citation Source</h2>
          <button
            className="citation-modal-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        <div className="citation-modal-content">
          <div className="citation-document-info">
            <h3 className="citation-doc-title">{document.filename}</h3>
            {chunk.pageNumber && (
              <span className="citation-page-badge">Page {chunk.pageNumber}</span>
            )}
            {chunk.chunkIndex !== undefined && (
              <span className="citation-chunk-badge">Chunk #{chunk.chunkIndex + 1}</span>
            )}
          </div>

          <div className="citation-chunk-preview">
            <h4 className="citation-section-title">Relevant Text:</h4>
            <div className="citation-chunk-text">
              {chunk.text}
            </div>
          </div>

          <div className="citation-actions">
            <a
              href={pdfUrlWithPage}
              target="_blank"
              rel="noopener noreferrer"
              className="citation-pdf-link"
            >
              {chunk.pageNumber 
                ? `Open PDF at Page ${chunk.pageNumber}`
                : "Open PDF Document"}
            </a>
            {chunk.score !== undefined && (
              <span className="citation-score">
                Relevance Score: {chunk.score.toFixed(3)}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
