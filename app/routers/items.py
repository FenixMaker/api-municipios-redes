import os
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.etag import canonical_query_parts, compute_etag
from app.models import Item
from app.schemas import (
    ItemMinimal,
    ItemSingleVerbose,
    ItemVerbose,
    ItemsResponseMinimal,
    ItemsResponseVerbose,
    PageMeta,
)
from app.services.items_query import build_items_select, get_dataset_version

router = APIRouter(prefix="/items", tags=["items"])

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def _cache_headers(etag: str) -> dict[str, str]:
    return {
        "Cache-Control": "private, max-age=60",
        "ETag": etag,
        "Vary": "Accept-Encoding",
    }


@router.get(
    "",
    response_model=ItemsResponseMinimal | ItemsResponseVerbose,
    responses={304: {"description": "Not Modified (corpo vazio)"}},
    summary="Lista paginada (cursor) com filtros",
)
def list_items(
    response: Response,
    db: Session = Depends(get_db),
    cursor: int | None = Query(
        default=None,
        ge=0,
        description="Último `id` visto; omita para a primeira página.",
    ),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    uf: str | None = Query(default=None, min_length=2, max_length=2, description="UF (2 letras)"),
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=128,
        description="Prefixo do nome (usa índice; evita LIKE %% no meio).",
    ),
    fields: str = Query(
        default="minimal",
        pattern="^(minimal|full)$",
        description="minimal = JSON enxuto; full = nomes longos.",
    ),
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
):
    canonical = canonical_query_parts(
        cursor=cursor if cursor and cursor > 0 else None,
        limit=limit,
        uf=uf,
        q=q,
        fields=fields,
    )
    version = get_dataset_version(db)
    etag = compute_etag(dataset_version=version, canonical=canonical)

    if if_none_match and if_none_match.strip() == etag:
        return Response(status_code=304, headers=_cache_headers(etag))

    stmt = build_items_select(cursor=cursor, limit=limit, uf=uf, q=q)
    t0 = time.perf_counter()
    rows = list(db.execute(stmt).scalars().all())
    elapsed_ms = (time.perf_counter() - t0) * 1000

    response.headers["X-Query-Time-Ms"] = f"{elapsed_ms:.3f}"
    for k, v in _cache_headers(etag).items():
        response.headers[k] = v

    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = page[-1].id if has_more and page else None

    meta = PageMeta(limit=limit, next_cursor=next_cursor, dataset_version=version)

    if fields == "full":
        data = [
            ItemVerbose(
                id=r.id,
                codigo_ibge=r.codigo_ibge,
                nome=r.nome,
                uf=r.uf,
                updated_at=r.updated_at,
            )
            for r in page
        ]
        return ItemsResponseVerbose(data=data, meta=meta)

    data = [
        ItemMinimal(i=r.id, c=r.codigo_ibge, n=r.nome, u=r.uf) for r in page
    ]
    return ItemsResponseMinimal(data=data, meta=meta)


@router.get(
    "/debug/offset-page",
    summary="Comparação: paginação por OFFSET (lento em offset alto)",
    include_in_schema=os.environ.get("ENABLE_BENCHMARKS", "").lower() in ("1", "true", "yes"),
)
def list_items_offset(
    response: Response,
    db: Session = Depends(get_db),
    offset: int = Query(ge=0, le=10_000_000),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
):
    if os.environ.get("ENABLE_BENCHMARKS", "").lower() not in ("1", "true", "yes"):
        raise HTTPException(status_code=404, detail="Ative ENABLE_BENCHMARKS=1")

    version = get_dataset_version(db)
    canonical = f"offset:{offset}:limit:{limit}:uf:{uf or ''}"
    etag = compute_etag(dataset_version=version, canonical=canonical)
    for k, v in _cache_headers(etag).items():
        response.headers[k] = v

    stmt = select(Item).order_by(Item.id).offset(offset).limit(limit)
    if uf:
        stmt = select(Item).where(Item.uf == uf.upper()).order_by(Item.id).offset(offset).limit(limit)

    t0 = time.perf_counter()
    rows = list(db.execute(stmt).scalars().all())
    elapsed_ms = (time.perf_counter() - t0) * 1000
    response.headers["X-Query-Time-Ms"] = f"{elapsed_ms:.3f}"

    meta = PageMeta(limit=limit, next_cursor=None, dataset_version=version)
    data = [ItemMinimal(i=r.id, c=r.codigo_ibge, n=r.nome, u=r.uf) for r in rows]
    return ItemsResponseMinimal(data=data, meta=meta)


@router.get(
    "/{item_id}",
    response_model=ItemSingleVerbose,
    summary="Item por ID",
    responses={304: {"description": "Not Modified"}},
)
def get_item(
    item_id: int,
    response: Response,
    db: Session = Depends(get_db),
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
):
    row = db.get(Item, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    version = get_dataset_version(db)
    etag = compute_etag(
        dataset_version=version,
        canonical=f"item:{item_id}:{row.updated_at.isoformat()}",
    )
    if if_none_match and if_none_match.strip() == etag:
        return Response(status_code=304, headers=_cache_headers(etag))

    for k, v in _cache_headers(etag).items():
        response.headers[k] = v

    return ItemSingleVerbose(
        id=row.id,
        codigo_ibge=row.codigo_ibge,
        nome=row.nome,
        uf=row.uf,
        updated_at=row.updated_at,
        payload=row.payload,
    )
