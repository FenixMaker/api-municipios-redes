"""Testes com SQLite temporário; `DATABASE_URL` deve ser definida antes de importar `app`."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_fd, _path = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = "sqlite:///" + _path.replace("\\", "/")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import DatasetMeta, Item

Base.metadata.create_all(bind=engine)
_sess = SessionLocal()
_sess.add(DatasetMeta(id=1, version=1))
for i in range(1, 121):
    _sess.add(
        Item(
            codigo_ibge=1_000_000 + i,
            nome=f"Município teste {i:03d}",
            uf="SP" if i % 2 == 0 else "MG",
        )
    )
_sess.commit()
_sess.close()

client = TestClient(app)


def test_root_returns_html_with_links() -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "/docs" in r.text
    assert "Swagger" in r.text


def test_favicon_no_content() -> None:
    r = client.get("/favicon.ico")
    assert r.status_code == 204


def test_list_returns_etag_and_data() -> None:
    r = client.get("/items", params={"limit": 10})
    assert r.status_code == 200
    assert "ETag" in r.headers
    assert r.headers.get("Cache-Control", "").startswith("private")
    body = r.json()
    assert len(body["data"]) == 10
    assert "meta" in body
    assert body["meta"]["dataset_version"] == 1


def test_conditional_get_304() -> None:
    r1 = client.get("/items", params={"limit": 5, "fields": "minimal"})
    assert r1.status_code == 200
    etag = r1.headers["ETag"]
    r2 = client.get(
        "/items",
        params={"limit": 5, "fields": "minimal"},
        headers={"If-None-Match": etag},
    )
    assert r2.status_code == 304
    assert r2.content == b""


def test_cursor_pagination() -> None:
    r1 = client.get("/items", params={"limit": 10})
    nxt = r1.json()["meta"]["next_cursor"]
    assert nxt is not None
    r2 = client.get("/items", params={"limit": 10, "cursor": nxt})
    assert r2.status_code == 200
    ids1 = [x["i"] for x in r1.json()["data"]]
    ids2 = [x["i"] for x in r2.json()["data"]]
    assert max(ids1) < min(ids2)


def test_filter_uf() -> None:
    r = client.get("/items", params={"limit": 50, "uf": "SP"})
    assert r.status_code == 200
    for row in r.json()["data"]:
        assert row["u"] == "SP"


def test_get_item_304() -> None:
    r1 = client.get("/items/1")
    assert r1.status_code == 200
    etag = r1.headers["ETag"]
    r2 = client.get("/items/1", headers={"If-None-Match": etag})
    assert r2.status_code == 304
