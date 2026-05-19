# Apresentação — API REST, cache e ETag (REDES)

> Use estes títulos no PowerPoint/Google Slides ou exporte com [Marp](https://marp.app/). Duração sugerida: 10–12 min.

---

## 1. Problema

- Disponibilizar **~4 milhões** de registros (cenário tipo IBGE) via **HTTP/REST**
- Risco: memória, CPU, timeouts, saturar o servidor
- Objetivo: respostas **rápidas** e **seguras** por requisição

---

## 2. Abordagem (visão geral)

- **Paginação** (nunca “tudo num JSON só”)
- **Filtros** na query string, amigáveis a índice
- **Compressão** (Gzip/Brotli via `Accept-Encoding`; em produção pode ser no proxy/CDN)
- **Cache + revalidação**: `Cache-Control`, `ETag`, **304**

---

## 3. Paginação: OFFSET vs cursor

| OFFSET + LIMIT | Cursor (`id > ?`) |
|----------------|-------------------|
| Páginas profundas: custo cresce | Tempo mais **estável** com índice |
| “Pular” para página N é simples | Melhor para consumo **sequencial** |

Figura sugerida: gráfico `X-Query-Time-Ms` vs `offset` (endpoint de benchmark).

---

## 4. Compressão e JSON

- **Gzip** reduz bytes em JSON repetitivo
- **JSON enxuto** (`i`, `c`, `n`, `u`) vs **verboso** (`codigo_ibge`, …)
- Slide com números: tamanho **com/sem** `Accept-Encoding: gzip`

---

## 5. Cache HTTP

- `Cache-Control: private, max-age=60` — frescor curto no cliente
- **ETag**: “impressão digital” da representação
- **304 Not Modified**: mesma URL + `If-None-Match` → **sem corpo**

---

## 6. ETag em larga escala (ideia-chave)

- Não calcular hash sobre **4M linhas** por request
- **Versão global** (`dataset_meta.version`) + parâmetros canônicos → SHA-256 → `ETag`
- Mudou o dataset? **Bump** na versão → clientes deixam de receber 304 “falso-positivo”

---

## 7. Arquitetura

```text
Cliente → FastAPI (Gzip) → SQLite (índices: id, uf+id)
         ↓
    OpenAPI /docs
```

---

## 8. Demo ao vivo — roteiro

1. Abrir **Swagger**: `http://127.0.0.1:8000/docs`
2. `GET /items?limit=20` — mostrar **ETag** e corpo **minimal**
3. Repetir com **mesmos parâmetros** e cabeçalho `If-None-Match: "<etag>"` → **304**
4. (Opcional) `ENABLE_BENCHMARKS=1` — comparar `offset=0` vs `offset` alto no `/items/debug/offset-page`

### Comandos `curl` (Windows)

```powershell
curl.exe -sD - "http://127.0.0.1:8000/items?limit=20" -o NUL
# Copie o valor de ETag da resposta, depois:
curl.exe -sD - -H "If-None-Match: \"<ETAG_AQUI>\"" "http://127.0.0.1:8000/items?limit=20" -o NUL
```

---

## 9. OpenAPI

- Contrato gerado automaticamente: **Swagger UI** + `openapi.json`
- Documenta filtros, limites, códigos **304**

---

## 10. Resultados (preencher com suas medições)

- Latência média por página (cursor)
- Pico de tempo com OFFSET alto
- Bytes: gzip on/off; minimal vs full
- Taxa de **304** em cliente que reconsulta

---

## 11. Conclusão

- Paginação + índices + compressão + **validação condicional** escalam melhor que “JSON gigante”
- **304** economiza banda quando nada mudou na “visão” daquela página

---

## 12. Perguntas

- Obrigado.
