import json
from dataclasses import dataclass
from pathlib import Path

import redis

from app.config import settings


QUEUE_KEY = "ingestion:tasks"


redis_client = redis.Redis.from_url(settings.REDIS_URL)


@dataclass
class IngestionTask:
  document_id: str
  file_path: str


def enqueue_ingestion_task(document_id: str, file_path: Path) -> None:
  """
  Push a new ingestion task into Redis.
  """
  payload = {
      "document_id": document_id,
      "file_path": str(file_path),
  }
  redis_client.rpush(QUEUE_KEY, json.dumps(payload))


def pop_ingestion_task(block: bool = True, timeout: int = 5) -> IngestionTask | None:
  """
  Pop an ingestion task from Redis. If block=True, uses BRPOP.
  """
  if block:
      result = redis_client.brpop(QUEUE_KEY, timeout=timeout)
      if result is None:
          return None
      _, raw = result
  else:
      raw = redis_client.rpop(QUEUE_KEY)
      if raw is None:
          return None

  data = json.loads(raw)
  return IngestionTask(
      document_id=data["document_id"],
      file_path=data["file_path"],
  )

