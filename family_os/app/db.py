import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

default_path = Path(__file__).resolve().parents[1] / 'data' / 'family_os.db'
db_path = Path(os.getenv('FAMILY_OS_DB_PATH', default_path))
db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f'sqlite:///{db_path}',
    connect_args={'check_same_thread': False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
