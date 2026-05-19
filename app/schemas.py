from datetime import datetime

from pydantic import BaseModel, Field


class ItemMinimal(BaseModel):
    """JSON enxuto (menos bytes na rede)."""

    i: int = Field(description="ID interno")
    c: int = Field(description="Código estilo IBGE (7 dígitos)")
    n: str = Field(description="Nome")
    u: str = Field(description="UF")


class ItemVerbose(BaseModel):
    """JSON verboso (legibilidade e OpenAPI)."""

    id: int
    codigo_ibge: int
    nome: str
    uf: str
    updated_at: datetime


class PageMeta(BaseModel):
    limit: int
    next_cursor: int | None = Field(
        default=None,
        description="Próximo cursor; omitido se não houver mais páginas.",
    )
    dataset_version: int


class ItemsResponseMinimal(BaseModel):
    data: list[ItemMinimal]
    meta: PageMeta


class ItemsResponseVerbose(BaseModel):
    data: list[ItemVerbose]
    meta: PageMeta


class ItemSingleVerbose(BaseModel):
    id: int
    codigo_ibge: int
    nome: str
    uf: str
    updated_at: datetime
    payload: str | None = None
