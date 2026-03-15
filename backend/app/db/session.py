import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

logger = logging.getLogger(__name__)

# Convert asyncpg URL to psycopg2 for synchronous operations
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql+asyncpg"):
    logger.info("Converting asyncpg URL to psycopg2 for synchronous SQLAlchemy")
    database_url = database_url.replace(
        "postgresql+asyncpg",
        "postgresql+psycopg2"
    )
    logger.info(f"Converted DATABASE_URL: {database_url[:50]}...")

engine = create_engine(database_url, echo=True, future=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()