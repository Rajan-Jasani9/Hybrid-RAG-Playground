import React from "react";
import { RetrievedChunk } from "../App";

interface ResultDrawerProps {
  open: boolean;
  onClose: () => void;
  chunks: RetrievedChunk[];
}

export const ResultDrawer: React.FC<ResultDrawerProps> = ({
  open,
  onClose,
  chunks,
}) => {
  return (
    <aside className={`result-drawer ${open ? "open" : ""}`}>
      <div className="result-drawer-header">
        <h2>Retrieved chunks</h2>
        <button className="icon-button" onClick={onClose} aria-label="Close drawer">
          ✕
        </button>
      </div>

      {chunks.length === 0 ? (
        <div className="result-empty">
          <p>No chunks retrieved yet. Run a query to see ranked results here.</p>
        </div>
      ) : (
        <ul className="result-list">
          {chunks.map((chunk) => (
            <li key={chunk.id} className="result-item">
              <div className="result-meta">
                <span className="result-doc-id">{chunk.documentId}</span>
                <span className="result-score">
                  Score: {chunk.score.toFixed(3)}
                </span>
              </div>
              <p className="result-text">{chunk.text}</p>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
};

