from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DatasetMeta(Base):
    __tablename__ = "dataset_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (Index("ix_items_uf_id", "uf", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    uf: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
