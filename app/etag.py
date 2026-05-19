import hashlib
from urllib.parse import urlencode


def canonical_query_parts(
    *,
    cursor: int | None,
    limit: int,
    uf: str | None,
    q: str | None,
    fields: str,
) -> str:
    parts: dict[str, str] = {
        "limit": str(limit),
        "fields": fields,
    }
    if cursor is not None:
        parts["cursor"] = str(cursor)
    if uf is not None:
        parts["uf"] = uf.upper()
    if q is not None:
        parts["q"] = q
    return urlencode(sorted(parts.items()))


def compute_etag(*, dataset_version: int, canonical: str) -> str:
    raw = f"{dataset_version}:{canonical}".encode()
    digest = hashlib.sha256(raw).hexdigest()
    return f'"{digest}"'
