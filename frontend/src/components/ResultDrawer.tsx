import React from "react";
import { X } from "lucide-react";
import { RetrievedChunk } from "../services/api";

interface ResultDrawerProps {
  open: boolean;
  onClose: () => void;
  chunks: RetrievedChunk[];
  isMobile?: boolean;
}

export const ResultDrawer: React.FC<ResultDrawerProps> = ({
  open,
  onClose,
  chunks,
  isMobile,
}) => {
  return (
    <aside
      className={`result-drawer ${open ? "open" : ""} ${
        isMobile ? "result-drawer-mobile" : ""
      }`}
      aria-hidden={!open}
    >
      <div className="result-drawer-header">
        <h2 id="result-drawer-title">Retrieved chunks</h2>
        <div className="result-drawer-header-actions">
          {isMobile && (
            <button
              type="button"
              className="result-drawer-dismiss"
              onClick={onClose}
            >
              Dismiss
            </button>
          )}
          <button
            type="button"
            className="icon-button icon-button-lg"
            onClick={onClose}
            aria-label="Close drawer"
          >
            <X size={18} strokeWidth={2} aria-hidden />
          </button>
        </div>
      </div>

      {chunks.length === 0 ? (
        <div className="result-empty">
          <p>No chunks retrieved yet. Run a query to see ranked results here.</p>
        </div>
      ) : (
        <ul className="result-list" aria-labelledby="result-drawer-title">
          {chunks.map((chunk) => (
            <li key={chunk.id} className="result-item">
              <div className="result-meta">
                <span className="result-doc-id">{chunk.documentId}</span>
                {chunk.score !== undefined && chunk.score !== null && (
                  <span className="result-score">
                    Score: {chunk.score.toFixed(3)}
                  </span>
                )}
              </div>
              <p className="result-text">{chunk.text}</p>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
};
