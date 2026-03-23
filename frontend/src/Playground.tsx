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
import { useMediaQuery } from "./hooks/useMediaQuery";

const MOBILE_QUERY = "(max-width: 767px)";

const Playground: React.FC = () => {
  const isMobile = useMediaQuery(MOBILE_QUERY);
  const [sidebarOpen, setSidebarOpen] = useState(false);
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

  useEffect(() => {
    if (apiKey) {
      localStorage.setItem("rag_api_key", apiKey);
    } else {
      localStorage.removeItem("rag_api_key");
    }
  }, [apiKey]);

  useEffect(() => {
    if (selectedModelFamily) {
      localStorage.setItem("rag_model_family", selectedModelFamily);
    } else {
      localStorage.removeItem("rag_model_family");
    }
  }, [selectedModelFamily]);

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
    const loadDocuments = async () => {
      try {
        const loadedDocuments = await apiService.listDocuments();
        if (loadedDocuments.length > 0) {
          setDocuments(loadedDocuments);
          setHasData(true);
        }
      } catch (err) {
        console.error("Error loading documents", err);
      }
    };

    loadDocuments();
  }, []);

  useEffect(() => {
    if (!isMobile) {
      setSidebarOpen(false);
    }
  }, [isMobile]);

  useEffect(() => {
    if (!isMobile || (!sidebarOpen && !isDrawerOpen)) {
      return;
    }
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [isMobile, sidebarOpen, isDrawerOpen]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (isMobile && isDrawerOpen) {
        setIsDrawerOpen(false);
      } else if (isMobile && sidebarOpen) {
        setSidebarOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isMobile, sidebarOpen, isDrawerOpen]);

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
    if (
      !confirm(
        "Are you sure you want to delete this document? This will also delete all associated chunks."
      )
    ) {
      return;
    }

    try {
      await apiService.deleteDocument(documentId);

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

    if (selectedModelFamily && selectedModel && apiKey) {
      return;
    }

    try {
      const retrievedChunks = await apiService.retrieve(
        query,
        retrievalMode,
        10
      );
      setChunks(retrievedChunks);
      setIsDrawerOpen(true);
      if (isMobile) {
        setSidebarOpen(false);
      }
    } catch (err) {
      console.error("Error running retrieval", err);
      addToast("Retrieval failed", "error");
    }
  };

  const handleChat = async (
    query: string,
    onStream: (content: string) => void,
    onChunks: (chunks: RetrievedChunk[]) => void
  ) => {
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

  const rootClass = [
    "app-root",
    isDrawerOpen ? "drawer-open" : "",
    isMobile && sidebarOpen ? "mobile-sidebar-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      {isMobile && sidebarOpen && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Close menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}

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
        isMobile={isMobile}
        onCloseMobile={() => setSidebarOpen(false)}
      />

      <main className="app-main">
        <ChatArea
          hasData={hasData}
          retrievalMode={retrievalMode}
          onRunRetrieval={handleRunRetrieval}
          onChat={handleChat}
          hasChatModel={Boolean(
            selectedModelFamily && selectedModel && apiKey
          )}
          documents={documents}
          isMobile={isMobile}
          onOpenSidebar={() => setSidebarOpen(true)}
        />
      </main>

      {isMobile && isDrawerOpen && (
        <button
          type="button"
          className="result-drawer-overlay"
          aria-label="Close results panel"
          onClick={() => setIsDrawerOpen(false)}
        />
      )}

      <ResultDrawer
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        chunks={chunks}
        isMobile={isMobile}
      />

      <ToastContainer toasts={toasts} onClose={removeToast} />
    </div>
  );
};

export default Playground;
