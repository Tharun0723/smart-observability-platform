from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker


# Always use the database inside the backend folder.
DATABASE_PATH = Path(__file__).resolve().parents[2] / "cicada.db"

DATABASE_URL = URL.create(
    drivername="sqlite",
    database=str(DATABASE_PATH),
)

engine = create_engine(
    DATABASE_URL,
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
