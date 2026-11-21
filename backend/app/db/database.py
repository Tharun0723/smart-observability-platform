import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

database_url = os.getenv("DATABASE_URL", "").strip()

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql://", 1
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )
else:
    # Preserve the existing local SQLite setup.
    database_path = Path(__file__).resolve().parents[2] / "cicada.db"

    sqlite_url = URL.create(
        drivername="sqlite",
        database=str(database_path),
    )

    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
