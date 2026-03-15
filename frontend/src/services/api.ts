/**
 * API Service
 * 
 * Centralized API client for all backend communication.
 * Handles all HTTP requests and response transformations.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8200";

// Types matching backend API responses
interface BackendRetrievedChunk {
  chunk_id: string;
  document_id: string;
  text: string;
  score: number;
  source: string;
  page_number?: number;
  token_count?: number;
  chunk_index?: number;
}

interface BackendRetrievalResponse {
  mode: string;
  top_k: number;
  chunks: BackendRetrievedChunk[];
}

interface BackendIngestItem {
  filename: string;
  document_id: string;
  status: "queued" | "processing" | "completed" | "failed";
}

interface BackendBatchIngestResponse {
  items: BackendIngestItem[];
  count: number;
}

// Frontend types (exported for use in components)
export type RetrievalMode =
  | "semantic"
  | "keyword"
  | "hybrid"
  | "semantic_mmr";

export interface RetrievedChunk {
  id: string;
  documentId: string;
  score?: number;
  text: string;
  pageNumber?: number;
  tokenCount?: number;
  chunkIndex?: number;
}

export interface IngestedDocument {
  id: string;
  filename: string;
  status: "queued" | "processing" | "completed" | "failed";
}

interface RetrievalRequest {
  query: string;
  mode: RetrievalMode;
  top_k?: number;
  document_ids?: string[];
}

/**
 * Transform backend chunk format to frontend format
 */
function transformChunk(backendChunk: BackendRetrievedChunk): RetrievedChunk {
  return {
    id: backendChunk.chunk_id,
    documentId: backendChunk.document_id,
    score: backendChunk.score,
    text: backendChunk.text,
    pageNumber: backendChunk.page_number,
    tokenCount: backendChunk.token_count,
    chunkIndex: backendChunk.chunk_index,
  };
}

/**
 * Transform backend ingest item to frontend format
 */
function transformIngestItem(item: BackendIngestItem): IngestedDocument {
  return {
    id: item.document_id,
    filename: item.filename,
    status: item.status,
  };
}

/**
 * API Client class
 */
class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Upload multiple files for ingestion
   */
  async uploadFiles(files: FileList | File[]): Promise<IngestedDocument[]> {
    const formData = new FormData();
    const fileArray = Array.from(files);
    
    fileArray.forEach((file) => {
      formData.append("files", file);
    });

    const response = await fetch(`${this.baseUrl}/api/ingest/batch`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${errorText}`);
    }

    const data: BackendBatchIngestResponse = await response.json();
    return (data.items ?? []).map(transformIngestItem);
  }

  /**
   * List all uploaded documents
   */
  async listDocuments(): Promise<IngestedDocument[]> {
    const response = await fetch(`${this.baseUrl}/api/documents`);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to list documents: ${errorText}`);
    }

    const data: BackendBatchIngestResponse = await response.json();
    return (data.items ?? []).map(transformIngestItem);
  }

  /**
   * Delete a document and all its chunks
   */
  async deleteDocument(documentId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/documents/${documentId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to delete document: ${errorText}`);
    }
  }

  /**
   * Run retrieval query
   */
  async retrieve(
    query: string,
    mode: RetrievalMode = "hybrid",
    topK: number = 10,
    documentIds?: string[]
  ): Promise<RetrievedChunk[]> {
    const requestBody: RetrievalRequest = {
      query: query.trim(),
      mode,
      top_k: topK,
      document_ids: documentIds,
    };

    const response = await fetch(`${this.baseUrl}/api/retrieve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Retrieval failed: ${errorText}`);
    }

    const data: BackendRetrievalResponse = await response.json();
    return data.chunks.map(transformChunk);
  }

  /**
   * Stream chat response with LLM
   */
  async *streamChat(
    query: string,
    modelFamily: string,
    modelName: string,
    apiKey: string,
    retrievalMode: RetrievalMode = "hybrid",
    topK: number = 10,
    documentIds?: string[],
    onChunks?: (chunks: RetrievedChunk[]) => void
  ): AsyncGenerator<{ content: string; chunks?: RetrievedChunk[] }> {
    const requestBody = {
      query: query.trim(),
      model_family: modelFamily,
      model_name: modelName,
      api_key: apiKey,
      retrieval_mode: retrievalMode,
      top_k: topK,
      document_ids: documentIds,
    };

    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat failed: ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is not readable");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") {
            return;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.chunks && onChunks) {
              onChunks(parsed.chunks.map(transformChunk));
            }
            if (parsed.content) {
              yield { content: parsed.content, chunks: parsed.chunks?.map(transformChunk) };
            }
          } catch (e) {
            console.error("Failed to parse SSE data:", e);
          }
        }
      }
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export class for testing or custom instances
export default ApiService;
