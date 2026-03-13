
## Hybrid RAG – Full‑Stack Retrieval‑Augmented App

A full‑stack playground for building and experimenting with **hybrid retrieval‑augmented generation (RAG)**: a modern frontend for chat and exploration, backed by a flexible embedding / retrieval / fusion pipeline.

---

### What this project is about

- **Hybrid retrieval**: combine multiple retrievers (e.g. dense + sparse, or multiple vector stores) and fuse their results.
- **RAG workflows**: plug in large language models with your own data via embeddings and retrieval.
- **End‑to‑end demo**: one repo that includes both **frontend** UI and **backend** APIs, so you can run, tweak, and extend everything in one place.

---

### Architecture at a glance

- **Frontend** (`frontend/`)
  - Modern **React + TypeScript** app (bundled with **Vite**).
  - Chat interface, sidebar, and styling tailored for RAG use cases.
  - Talks to the backend over HTTP/JSON APIs.

- **Backend** (`backend/`)
  - **Python** API exposing endpoints for:
    - Embedding and indexing content.
    - Retrieving documents via multiple strategies.
    - Running hybrid fusion (e.g. RRF) and returning context + answers.
  - Pluggable embedding backends and fusion strategies.

---

### Key features

- **Unified UX**: one polished chat + sidebar interface for exploration.
- **Hybrid RAG pipeline**:
  - Multiple retrievers, configurable weighting/fusion.
  - Embedding abstractions so you can swap models without rewriting the app.
- **Developer‑friendly**:
  - Separate `frontend/` and `backend/` folders, shared README and concepts.
  - Vite dev server for fast UI iteration.
  - Python service layer for experimenting with retrieval logic.

---

### Tech stack

- **Frontend**
  - React + TypeScript
  - Vite
  - Custom CSS for layout, typography, and components

- **Backend**
  - Python 3.x
  - HTTP API framework (e.g. FastAPI / similar)
  - Embedding services and retrieval logic (e.g. E5 embeddings, RRF fusion)

- **Tooling**
  - Node.js package manager (npm / pnpm / yarn)
  - `pip` + virtual environment for Python dependencies
  - Git for version control

---

### Getting started

#### 1. Prerequisites

- **Node.js** (LTS recommended)
- **npm** (or `pnpm` / `yarn`)
- **Python 3.10+** (recommended)
- **Git**

On Windows, use **PowerShell** or **Command Prompt**; on macOS/Linux, use your shell of choice.

---

#### 2. Clone the repository

```bash
git clone <your-repo-url> hybrid-rag
cd hybrid-rag
```

#### 3. Backend setup (`backend/`)

From the project root:

```bash
cd backend
```

Create and activate a virtual environment (Windows):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Or on macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional: copy env template if available:

```bash
cp .env.example .env
```

Run the API server (adapt command to your framework if needed):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

By default the backend will be available at:

`http://localhost:8000`

---

#### 4. Frontend setup (`frontend/`)

In a new terminal, from the project root:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
# or
pnpm install
# or
yarn
```

Start the dev server:

```bash
npm run dev
```

Vite will usually start the app at:

`http://localhost:5173`

---

### Running the full stack

- **Backend**: run the Python API (e.g. with `uvicorn`) on port `8000`.
- **Frontend**: run `npm run dev` (Vite) on port `5173`.

Open the frontend URL in your browser. The app should automatically call the backend API.

If you change ports or hosts, update the frontend API base URL (e.g. in an `.env` file or config constant).

---

### Project structure (high level)

```text
hybrid-rag/
  frontend/   # React + Vite app (chat UI, sidebar, styling, etc.)
  backend/    # Python API, embeddings, retrieval, fusion logic
  .gitignore
  README.md   # This file
```

Inside each subfolder:

- `frontend/`
  - `src/App.tsx` – main React app shell.
  - `src/components/Sidebar.tsx` – sidebar navigation, settings, etc.
  - `src/components/ChatArea.tsx` – chat UI and message history.
  - `src/styles.css` – global styles and layout.

- `backend/`
  - `app/services/embedding/` – embedding implementations and factory.
  - `fusion/` – fusion strategies (e.g. RRF).
  - `app/main.py` (or similar) – API entrypoint.

(Exact file names may vary slightly depending on your setup.)

---

### Environment configuration

Typical configuration is done via environment variables in `.env` files (not committed to Git). Common settings might include:

- **Model / provider configuration**
  - Model names, API keys, and endpoints.
- **Retrieval & fusion parameters**
  - Number of candidates from each retriever.
  - Weights or hyperparameters for fusion algorithms (e.g. RRF `k` value).
- **App settings**
  - CORS origins, log levels, ports, etc.

Check the backend for config, `.env.example`, or service factory files to see what variables are expected.

---

### Common workflows

- **Add a new embedding model**
  - Implement a new class in `app/services/embedding/`.
  - Register it in the embedding factory so it can be selected by name.
  - Wire a configuration flag to choose it at runtime.

- **Tune hybrid retrieval**
  - Modify fusion parameters (e.g. in `fusion/rrf.py`).
  - Adjust per‑retriever cutoffs (top‑k).
  - Inspect logs or debug output to compare retrieved documents.

- **Customize the UI**
  - Update `Sidebar.tsx` to surface new options (e.g. model, top‑k, fusion mode).
  - Update `ChatArea.tsx` to render additional context (e.g. document sources).
  - Refine `styles.css` for layout, theming, and responsiveness.
