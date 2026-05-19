"""
Gera e carrega registros **sintéticos** (volume alto para teste de carga) no SQLite.

Para dados **reais** do IBGE (municípios oficiais), use:
  python scripts/load_ibge_municipios.py

Uso (sintético):
  python scripts/seed_db.py --count 4000000
  set IBGE_SEED_COUNT=5000 && python scripts/seed_db.py   # Windows: rápido para testes

Requisitos: executar a partir da raiz do projeto (REDES).
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Garante import do pacote `app`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.database import Base, SessionLocal, engine
from app.models import DatasetMeta, Item

UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]

BATCH_SIZE = 8000


def _prepare_sqlite_pragmas(session: Session) -> None:
    session.execute(text("PRAGMA journal_mode=WAL"))
    session.execute(text("PRAGMA synchronous=NORMAL"))
    session.execute(text("PRAGMA temp_store=MEMORY"))
    session.execute(text("PRAGMA cache_size=-200000"))
    session.commit()


def seed(count: int, bump_version: bool) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

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

        rng = random.Random(42)
        t0 = time.perf_counter()
        batch: list[dict] = []
        now = datetime.now(timezone.utc)

        for i in range(1, count + 1):
            uf = UFS[rng.randrange(len(UFS))]
            codigo = 1_000_000 + (i % 8_999_999)
            nome = f"Município sintético {i:07d} {uf}"
            payload = f"reg={i};uf={uf}" if (i % 10 == 0) else None
            batch.append(
                {
                    "codigo_ibge": codigo,
                    "nome": nome,
                    "uf": uf,
                    "payload": payload,
                    "updated_at": now,
                }
            )
            if len(batch) >= BATCH_SIZE:
                session.bulk_insert_mappings(Item, batch)
                session.commit()
                batch.clear()
                if i % (BATCH_SIZE * 25) == 0:
                    elapsed = time.perf_counter() - t0
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"  {i:,} linhas — {rate:,.0f} linhas/s")

        if batch:
            session.bulk_insert_mappings(Item, batch)
            session.commit()

        session.execute(text("ANALYZE"))
        session.commit()
        elapsed = time.perf_counter() - t0
        print(f"Concluído: {count:,} registros em {elapsed:.1f}s ({count / elapsed:,.0f} linhas/s)")
        print(f"dataset_meta.version = {version}")
    finally:
        session.close()


def main() -> None:
    default_count = int(os.environ.get("IBGE_SEED_COUNT", "10000"))
    parser = argparse.ArgumentParser(description="Carga massiva SQLite (IBGE-like)")
    parser.add_argument(
        "--count",
        type=int,
        default=default_count,
        help=f"Número de linhas (padrão: env IBGE_SEED_COUNT ou {default_count})",
    )
    parser.add_argument(
        "--bump-version",
        action="store_true",
        help="Incrementa dataset_meta.version se meta já existir (simula atualização).",
    )
    args = parser.parse_args()
    if args.count < 1:
        raise SystemExit("--count deve ser >= 1")
    print(f"Gerando {args.count:,} registros em {DATA_DIR} …")
    seed(args.count, bump_version=args.bump_version)


if __name__ == "__main__":
    main()
