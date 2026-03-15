import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { RetrievalMode, RetrievedChunk, IngestedDocument } from "../services/api";
import { parseCitations, TextSegment } from "../utils/citations";
import { CitationModal } from "./CitationModal";

interface ChatAreaProps {
  hasData: boolean;
  retrievalMode: RetrievalMode;
  onRunRetrieval: (query: string) => void | Promise<void>;
  onChat: (query: string, onStream: (content: string) => void, onChunks: (chunks: RetrievedChunk[]) => void) => Promise<void>;
  hasChatModel: boolean;
  documents: IngestedDocument[];
}

interface Message {
  id: string;
  type: "user" | "assistant" | "system";
  content: string;
  chunks?: RetrievedChunk[];
  timestamp: Date;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  hasData,
  retrievalMode,
  onRunRetrieval,
  onChat,
  hasChatModel,
  documents,
}) => {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStreamingContent, setCurrentStreamingContent] = useState("");
  const [citationModalOpen, setCitationModalOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<{
    chunk: RetrievedChunk;
    document: IngestedDocument;
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatLogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentStreamingContent, isProcessing]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasData || !query.trim()) return;

    const userQuery = query.trim();
    setQuery("");

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: userQuery,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    if (hasChatModel) {
      // Use chat with streaming
      setIsProcessing(true);
      setIsStreaming(true);
      setCurrentStreamingContent("");

      let chunks: RetrievedChunk[] = [];
      let finalContent = "";

      try {
        await onChat(
          userQuery,
          (content: string) => {
            finalContent += content;
            setCurrentStreamingContent(finalContent);
            setIsProcessing(false); // Hide loading indicator once content starts streaming
          },
          (retrievedChunks: RetrievedChunk[]) => {
            chunks = retrievedChunks;
          }
        );

        // Add assistant message with full content
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "assistant",
          content: finalContent,
          chunks,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setCurrentStreamingContent("");
      } finally {
        setIsStreaming(false);
        setIsProcessing(false);
      }
    } else {
      // Just run retrieval
      onRunRetrieval(userQuery);
    }
  };

  const handleCitationClick = (label: string, chunks: RetrievedChunk[]) => {
    // Find the chunk with this label (A=0, B=1, etc.)
    const index = label.charCodeAt(0) - 65; // A=0, B=1, etc.
    if (index >= 0 && index < chunks.length) {
      const chunk = chunks[index];
      // Find the document
      const document = documents.find((doc) => doc.id === chunk.documentId);
      if (document) {
        setSelectedCitation({ chunk, document });
        setCitationModalOpen(true);
      }
    }
  };

  const renderMessageContent = (content: string, chunks?: RetrievedChunk[]) => {
    // Replace citation markers with clickable links, then render as markdown
    let processedContent = content;
    const segments = parseCitations(content);
    
    // Build content with clickable citation links
    let markdownContent = "";
    for (const segment of segments) {
      if (segment.isCitation && segment.citations && chunks) {
        const label = segment.citations[0];
        const index = label.charCodeAt(0) - 65;
        if (index >= 0 && index < chunks.length) {
          // Replace [[A]] with a clickable markdown link
          markdownContent += `[${label}](#citation-${label})`;
        } else {
          markdownContent += segment.text;
        }
      } else {
        markdownContent += segment.text;
      }
    }

    // Create citation click handlers
    const handleCitationLinkClick = (e: React.MouseEvent, label: string) => {
      e.preventDefault();
      if (chunks) {
        handleCitationClick(label, chunks);
      }
    };

    return (
      <div className="message-content">
        <ReactMarkdown
          components={{
            a: ({ node, href, children, ...props }) => {
              // Check if this is a citation link
              if (href && href.startsWith("#citation-")) {
                const label = href.replace("#citation-", "");
                return (
                  <a
                    {...props}
                    href={href}
                    className="citation-link"
                    onClick={(e) => handleCitationLinkClick(e, label)}
                    title={`Click to view source ${label}`}
                  >
                    [{label}]
                  </a>
                );
              }
              // Regular links
              return <a {...props} href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
            },
          }}
        >
          {markdownContent}
        </ReactMarkdown>
      </div>
    );
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

      <div className="chat-body" ref={chatLogRef}>
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
            {messages.length === 0 && (
              <div className="chat-message system-message">
                {hasChatModel
                  ? "Ask a question to get an AI-powered answer with citations from your documents."
                  : "Try a question like &ldquo;Summarize the main concepts in my documents&rdquo; to test the hybrid search."}
              </div>
            )}
            {messages.map((message) => (
              <div key={message.id} className={`chat-message ${message.type}-message`}>
                {renderMessageContent(message.content, message.chunks)}
              </div>
            ))}
            {isProcessing && !currentStreamingContent && (
              <div className="loading-indicator">
                <div className="loading-dots">
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                </div>
                <span className="loading-text">Processing your request...</span>
              </div>
            )}
            {isStreaming && currentStreamingContent && (
              <div className="chat-message assistant-message">
                {renderMessageContent(currentStreamingContent)}
                <span className="streaming-cursor">▋</span>
              </div>
            )}
            <div ref={messagesEndRef} />
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

      <CitationModal
        open={citationModalOpen}
        onClose={() => {
          setCitationModalOpen(false);
          setSelectedCitation(null);
        }}
        chunk={selectedCitation?.chunk || null}
        document={selectedCitation?.document || null}
      />
    </section>
  );
};

