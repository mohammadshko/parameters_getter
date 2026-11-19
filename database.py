import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/parameters_getter",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    # Import models so their tables are registered in Base.metadata.
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Add the new optional work_name column to existing installations.
    with engine.begin() as connection:
        connection.execute(text(
            'ALTER TABLE work_orders ADD COLUMN IF NOT EXISTS work_name VARCHAR(255)'
        ))
