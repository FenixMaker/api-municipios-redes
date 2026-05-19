from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import DatasetMeta, Item


def get_dataset_version(db: Session) -> int:
    row = db.execute(select(DatasetMeta.version).where(DatasetMeta.id == 1)).scalar_one_or_none()
    if row is None:
        return 0
    return int(row)


def build_items_select(
    *,
    cursor: int | None,
    limit: int,
    uf: str | None,
    q: str | None,
) -> Select:
    stmt = select(Item)
    if cursor is not None and cursor > 0:
        stmt = stmt.where(Item.id > cursor)
    if uf:
        stmt = stmt.where(Item.uf == uf.upper())
    if q:
        stmt = stmt.where(Item.nome.like(f"{q}%"))
    stmt = stmt.order_by(Item.id).limit(limit + 1)
    return stmt
