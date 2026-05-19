"""
Carrega municípios brasileiros reais a partir da API pública do IBGE.

Fonte: https://servicodados.ibge.gov.br/api/v1/localidades/municipios

Uso (na raiz do projeto):
  python scripts/load_ibge_municipios.py
  python scripts/load_ibge_municipios.py --bump-version

Requer rede (HTTPS). Reutiliza o mesmo SQLite configurado em app.config (data/ibge_api.db).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import DATA_DIR
from app.database import Base, SessionLocal, engine
from app.models import DatasetMeta, Item

IBGE_MUNICIPIOS_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
)
BATCH_SIZE = 500


def _prepare_sqlite_pragmas(session: Session) -> None:
    session.execute(text("PRAGMA journal_mode=WAL"))
    session.execute(text("PRAGMA synchronous=NORMAL"))
    session.execute(text("PRAGMA temp_store=MEMORY"))
    session.commit()


def _extract_uf(m: dict) -> str | None:
    mic = m.get("microrregiao")
    if isinstance(mic, dict):
        try:
            return str(mic["mesorregiao"]["UF"]["sigla"]).upper()[:2]
        except (KeyError, TypeError):
            pass
    ri = m.get("regiao-imediata")
    if isinstance(ri, dict):
        try:
            uf = ri.get("UF", {}).get("sigla")
            if uf:
                return str(uf).upper()[:2]
            inter = ri.get("regiao-intermediaria")
            if isinstance(inter, dict):
                uf2 = inter.get("UF", {}).get("sigla")
                if uf2:
                    return str(uf2).upper()[:2]
        except (KeyError, TypeError):
            pass
    return None


def fetch_municipios() -> list[dict]:
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        r = client.get(IBGE_MUNICIPIOS_URL)
        r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError("Resposta IBGE inesperada: esperado array JSON")
    return data


def load_ibge(*, bump_version: bool) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    print("Baixando municípios do IBGE …")
    t_fetch = time.perf_counter()
    municipios = fetch_municipios()
    print(f"  {len(municipios):,} municípios recebidos em {time.perf_counter() - t_fetch:.1f}s")

    session = SessionLocal()
    try:
        _prepare_sqlite_pragmas(session)
        prev = session.execute(
            select(DatasetMeta.version).where(DatasetMeta.id == 1)
        ).scalar_one_or_none()
        session.execute(delete(Item))
        session.execute(delete(DatasetMeta))
        session.commit()

        if bump_version and prev is not None:
            version = int(prev) + 1
        else:
            version = 1
        session.add(DatasetMeta(id=1, version=version))
        session.commit()

        now = datetime.now(timezone.utc)
        batch: list[dict] = []
        skipped = 0
        t0 = time.perf_counter()

        for m in municipios:
            if not isinstance(m, dict):
                skipped += 1
                continue
            mid = m.get("id")
            nome = m.get("nome")
            uf = _extract_uf(m)
            if mid is None or not nome or not uf:
                skipped += 1
                continue
            nome_s = str(nome).strip()
            if len(nome_s) > 255:
                nome_s = nome_s[:255]
            mic = m.get("microrregiao")
            payload_obj = {
                "fonte": "IBGE API v1 /localidades/municipios",
                "microrregiao": mic.get("nome") if isinstance(mic, dict) else None,
            }
            batch.append(
                {
                    "codigo_ibge": int(mid),
                    "nome": nome_s,
                    "uf": uf,
                    "payload": json.dumps(payload_obj, ensure_ascii=False),
                    "updated_at": now,
                }
            )
            if len(batch) >= BATCH_SIZE:
                session.bulk_insert_mappings(Item, batch)
                session.commit()
                batch.clear()

        if batch:
            session.bulk_insert_mappings(Item, batch)
            session.commit()

        session.execute(text("ANALYZE"))
        session.commit()

        elapsed = time.perf_counter() - t0
        total = len(municipios) - skipped
        print(f"Inseridos: {total:,} registros em {elapsed:.1f}s (ignorados: {skipped})")
        print(f"dataset_meta.version = {version}")
        print(f"Banco: {DATA_DIR / 'ibge_api.db'}")
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carga de municípios reais (API IBGE) no SQLite do projeto",
    )
    parser.add_argument(
        "--bump-version",
        action="store_true",
        help="Incrementa dataset_meta.version em relação à carga anterior.",
    )
    args = parser.parse_args()
    load_ibge(bump_version=args.bump_version)


if __name__ == "__main__":
    main()
