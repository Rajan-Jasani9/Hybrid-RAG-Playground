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
  const [selectedModelFamily, setSelectedModelFamily] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [apiKey, setApiKey] = useState<string>("");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("hybrid");
  const [chunks, setChunks] = useState<RetrievedChunk[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [documents, setDocuments] = useState<IngestedDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

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
      // Optionally show error to user
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
          hasChatModel={Boolean(selectedModelFamily && selectedModel)}
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

