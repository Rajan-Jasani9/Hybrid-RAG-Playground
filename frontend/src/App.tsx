import React, { useEffect, useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";
import { ResultDrawer } from "./components/ResultDrawer";

export type RetrievalMode =
  | "semantic"
  | "keyword"
  | "hybrid"
  | "semantic_mmr";

export interface RetrievedChunk {
  id: string;
  documentId: string;
  score: number;
  text: string;
}

const App: React.FC = () => {
  const [hasData, setHasData] = useState(false);
  const [selectedModelFamily, setSelectedModelFamily] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [apiKey, setApiKey] = useState<string>("");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("hybrid");
  const [chunks, setChunks] = useState<RetrievedChunk[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.dataset.theme = "dark";
    } else {
      delete document.documentElement.dataset.theme;
    }
  }, [theme]);

  const handleFilesUploaded = (files: FileList | null) => {
    if (files && files.length > 0) {
      setHasData(true);
    }
  };

  const handleRunRetrieval = (query: string) => {
    // Placeholder: in the future this will call your backend hybrid search.
    // For now we just simulate a couple of chunks to visualize the layout.
    const demoChunks: RetrievedChunk[] = [
      {
        id: "1",
        documentId: "demo-doc-1",
        score: 0.92,
        text: "This is a simulated retrieved chunk for query: " + query,
      },
      {
        id: "2",
        documentId: "demo-doc-2",
        score: 0.87,
        text: "Another high-scoring chunk that would normally come from hybrid search.",
      },
    ];
    setChunks(demoChunks);
    setIsDrawerOpen(true);
  };

  return (
    <div className="app-root">
      <Sidebar
        onFilesUploaded={handleFilesUploaded}
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
    </div>
  );
};

export default App;

