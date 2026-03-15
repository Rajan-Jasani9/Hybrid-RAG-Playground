from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as ingestion_router


app = FastAPI(title="Hybrid RAG Backend")

# Allow all origins for development (remove in production!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(ingestion_router, prefix="/api")

