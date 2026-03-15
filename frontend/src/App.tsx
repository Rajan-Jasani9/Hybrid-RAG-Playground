import React, { useEffect, useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";
import { ResultDrawer } from "./components/ResultDrawer";
import { ToastContainer, Toast } from "./components/Toast";
import {
  apiService,
  RetrievalMode,
  RetrievedChunk,
  IngestedDocument,
} from "./services/api";

const App: React.FC = () => {
  const [hasData, setHasData] = useState(false);
  const [selectedModelFamily, setSelectedModelFamily] = useState<string>(() => {
    return localStorage.getItem("rag_model_family") || "";
  });
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    return localStorage.getItem("rag_model_name") || "";
  });
  const [apiKey, setApiKey] = useState<string>(() => {
    return localStorage.getItem("rag_api_key") || "";
  });
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("hybrid");
  const [chunks, setChunks] = useState<RetrievedChunk[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [documents, setDocuments] = useState<IngestedDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Save API key to localStorage when it changes
  useEffect(() => {
    if (apiKey) {
      localStorage.setItem("rag_api_key", apiKey);
    } else {
      localStorage.removeItem("rag_api_key");
    }
  }, [apiKey]);

  // Save model family to localStorage when it changes
  useEffect(() => {
    if (selectedModelFamily) {
      localStorage.setItem("rag_model_family", selectedModelFamily);
    } else {
      localStorage.removeItem("rag_model_family");
    }
  }, [selectedModelFamily]);

  // Save model name to localStorage when it changes
  useEffect(() => {
    if (selectedModel) {
      localStorage.setItem("rag_model_name", selectedModel);
    } else {
      localStorage.removeItem("rag_model_name");
    }
  }, [selectedModel]);

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.dataset.theme = "dark";
    } else {
      delete document.documentElement.dataset.theme;
    }
  }, [theme]);

  useEffect(() => {
    // Load documents on mount
    const loadDocuments = async () => {
      try {
        const loadedDocuments = await apiService.listDocuments();
        if (loadedDocuments.length > 0) {
          setDocuments(loadedDocuments);
          setHasData(true);
        }
      } catch (err) {
        console.error("Error loading documents", err);
        // Don't show error toast on initial load to avoid noise
      }
    };

    loadDocuments();
  }, []);

  const addToast = (message: string, type: Toast["type"] = "info") => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const handleFilesUploaded = async (files: FileList | null) => {
    if (!files || files.length === 0 || isUploading) return;

    try {
      setIsUploading(true);
      const uploadedDocuments = await apiService.uploadFiles(files);

      if (uploadedDocuments.length > 0) {
        // Refresh the full document list from the server
        const allDocuments = await apiService.listDocuments();
        setDocuments(allDocuments);
        setHasData(allDocuments.length > 0);
        
        addToast(
          `Successfully uploaded ${uploadedDocuments.length} file(s)`,
          "success"
        );
      } else {
        addToast("No files were uploaded", "error");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to upload files";
      addToast(errorMessage, "error");
      console.error("Error uploading files", err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm("Are you sure you want to delete this document? This will also delete all associated chunks.")) {
      return;
    }

    try {
      await apiService.deleteDocument(documentId);
      
      // Refresh the document list
      const allDocuments = await apiService.listDocuments();
      setDocuments(allDocuments);
      setHasData(allDocuments.length > 0);
      
      addToast("Document deleted successfully", "success");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to delete document";
      addToast(errorMessage, "error");
      console.error("Error deleting document", err);
    }
  };

  const handleRunRetrieval = async (query: string) => {
    if (!query.trim()) return;

    // If chat model is configured, use chat endpoint
    if (selectedModelFamily && selectedModel && apiKey) {
      // This will be handled by ChatArea for streaming
      return;
    }

    // Otherwise, just run retrieval
    try {
      const retrievedChunks = await apiService.retrieve(
        query,
        retrievalMode,
        10
      );
      setChunks(retrievedChunks);
      setIsDrawerOpen(true);
    } catch (err) {
      console.error("Error running retrieval", err);
      addToast("Retrieval failed", "error");
    }
  };

  const handleChat = async (query: string, onStream: (content: string) => void, onChunks: (chunks: RetrievedChunk[]) => void) => {
    if (!selectedModelFamily || !selectedModel || !apiKey) {
      addToast("Please configure a chat model and API key", "error");
      return;
    }

    try {
      let retrievedChunks: RetrievedChunk[] = [];
      for await (const chunk of apiService.streamChat(
        query,
        selectedModelFamily,
        selectedModel,
        apiKey,
        retrievalMode,
        10,
        undefined,
        (chunks) => {
          retrievedChunks = chunks;
          onChunks(chunks);
        }
      )) {
        if (chunk.content) {
          onStream(chunk.content);
        }
      }
      if (retrievedChunks.length > 0) {
        setChunks(retrievedChunks);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Chat failed";
      addToast(errorMessage, "error");
      console.error("Error in chat", err);
    }
  };

  return (
    <div className={`app-root ${isDrawerOpen ? "drawer-open" : ""}`}>
      <Sidebar
        onFilesUploaded={handleFilesUploaded}
        isUploading={isUploading}
        documents={documents}
        onDeleteDocument={handleDeleteDocument}
        selectedModelFamily={selectedModelFamily}
        onChangeModelFamily={setSelectedModelFamily}
        selectedModel={selectedModel}
        onChangeModel={setSelectedModel}
        apiKey={apiKey}
        onChangeApiKey={setApiKey}
        retrievalMode={retrievalMode}
        onChangeRetrievalMode={setRetrievalMode}
        theme={theme}
        onToggleTheme={() =>
          setTheme((prev) => (prev === "light" ? "dark" : "light"))
        }
      />

      <main className="app-main">
        <ChatArea
          hasData={hasData}
          retrievalMode={retrievalMode}
          onRunRetrieval={handleRunRetrieval}
          onChat={handleChat}
          hasChatModel={Boolean(selectedModelFamily && selectedModel && apiKey)}
          documents={documents}
        />
      </main>

      <ResultDrawer
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        chunks={chunks}
      />

      <ToastContainer toasts={toasts} onClose={removeToast} />
    </div>
  );
};

export default App;

