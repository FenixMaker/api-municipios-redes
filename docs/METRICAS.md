# Medições: compressão, latência e OFFSET vs cursor

Execute a API (`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`) após popular o banco. Para **dados reais do IBGE**: `python scripts/load_ibge_municipios.py`. Para **milhões de linhas sintéticas**: `python scripts/seed_db.py --count 4000000`.

## Tamanho da resposta (Gzip/Brotli)

O servidor comprime respostas JSON acima de 500 bytes conforme `Accept-Encoding` (Brotli `br` ou Gzip `gzip`).

```bash
curl -sS -o /dev/null -w "%{size_download}\n" "http://127.0.0.1:8000/items?limit=200&fields=full"
curl -sS -H "Accept-Encoding: gzip" -o /dev/null -w "%{size_download}\n" "http://127.0.0.1:8000/items?limit=200&fields=full"
curl -sS -H "Accept-Encoding: br" -o /dev/null -w "%{size_download}\n" "http://127.0.0.1:8000/items?limit=200&fields=full"
```

No Windows PowerShell, use `curl.exe` ou grave o corpo em arquivo e compare tamanhos.

Em produção, também é comum habilitar `br` no **proxy/CDN** (nginx, Caddy) para aliviar CPU da aplicação.

## Cabeçalho `X-Query-Time-Ms`

Cada `GET /items` inclui tempo aproximado da consulta ao SQLite no servidor (útil para gráficos OFFSET vs cursor).

## Comparação OFFSET vs cursor

1. **Cursor (recomendado):** `GET /items?limit=50&cursor=<id>` — tempo estável com índice em `id`.
2. **OFFSET (benchmark):** defina `ENABLE_BENCHMARKS=1` e chame  
   `GET /items/debug/offset-page?offset=<alto>&limit=50`  
   Com dataset **real** (~5,5 mil municípios), use `offset` próximo do fim (ex.: `5000`). Com dataset **sintético** de milhões, use `offset` alto (ex.: `3800000`); compare `X-Query-Time-Ms` com `offset=0`.

## JSON enxuto vs verboso

- `fields=minimal` → chaves curtas (`i`, `c`, `n`, `u`).
- `fields=full` → nomes longos e `updated_at`.

Compare tamanho do corpo (com e sem gzip) para o mesmo `limit`.

## ETag e 304

Segunda requisição idêntica com `If-None-Match: "<etag>"` deve retornar **304** sem corpo, evitando reenviar a página inteira quando `dataset_meta.version` e os parâmetros da consulta não mudaram.

Para simular mudança de dados global: `python scripts/load_ibge_municipios.py --bump-version` ou, com dados sintéticos, `python scripts/seed_db.py --count <n> --bump-version`.
