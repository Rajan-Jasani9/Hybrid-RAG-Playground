from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as ingestion_router


app = FastAPI(title="Hybrid RAG Backend")

# Allow local frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(ingestion_router, prefix="/api")

