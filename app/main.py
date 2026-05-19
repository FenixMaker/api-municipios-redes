from contextlib import asynccontextmanager
from pathlib import Path

import brotli
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import DATA_DIR
from app.database import Base, engine
from app.routers import items


class BrotliMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        minimum_size: int = 500,
        quality: int = 5,
    ) -> None:
        self.app = app
        self.minimum_size = minimum_size
        self.quality = quality

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        if method == "HEAD":
            await self.app(scope, receive, send)
            return

        accept_encoding = b""
        for k, v in scope.get("headers", []):
            if k.lower() == b"accept-encoding":
                accept_encoding = v.lower()
                break

        if b"br" not in accept_encoding:
            await self.app(scope, receive, send)
            return

        start_message: Message | None = None
        body_parts: list[bytes] = []

        async def send_wrapper(message: Message) -> None:
            nonlocal start_message
            if message["type"] == "http.response.start":
                start_message = {
                    "type": "http.response.start",
                    "status": message["status"],
                    "headers": list(message.get("headers", [])),
                }
                return

            if message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    body_parts.append(body)

                if message.get("more_body", False):
                    return

                if start_message is None:
                    await send(message)
                    return

                status = int(start_message.get("status", 200))
                headers: list[tuple[bytes, bytes]] = list(start_message.get("headers", []))

                if status in (204, 304) or status < 200:
                    await send(start_message)
                    await send(
                        {
                            "type": "http.response.body",
                            "body": b"".join(body_parts),
                            "more_body": False,
                        }
                    )
                    return

                content_encoding = None
                content_type = None
                for k, v in headers:
                    kl = k.lower()
                    if kl == b"content-encoding":
                        content_encoding = v.lower()
                    elif kl == b"content-type":
                        content_type = v.lower()

                joined = b"".join(body_parts)
                is_compressible = content_type is None or b"application/json" in content_type or content_type.startswith(b"text/")
                should_compress = (
                    (content_encoding is None)
                    and is_compressible
                    and len(joined) >= self.minimum_size
                )

                if not should_compress:
                    await send(start_message)
                    await send({"type": "http.response.body", "body": joined, "more_body": False})
                    return

                compressed = brotli.compress(joined, quality=self.quality)

                new_headers: list[tuple[bytes, bytes]] = []
                vary_values: list[bytes] = []
                for k, v in headers:
                    kl = k.lower()
                    if kl == b"content-length":
                        continue
                    if kl == b"vary":
                        vary_values.append(v)
                        continue
                    new_headers.append((k, v))

                new_headers.append((b"content-encoding", b"br"))
                new_headers.append((b"content-length", str(len(compressed)).encode()))

                vary_joined = b", ".join(vary_values).decode(errors="ignore")
                vary_tokens = {t.strip().lower() for t in vary_joined.split(",") if t.strip()}
                vary_tokens.add("accept-encoding")
                new_headers.append((b"vary", ", ".join(sorted(vary_tokens)).encode()))

                await send(
                    {
                        "type": "http.response.start",
                        "status": status,
                        "headers": new_headers,
                    }
                )
                await send({"type": "http.response.body", "body": compressed, "more_body": False})
                return

            await send(message)

        await self.app(scope, receive, send_wrapper)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de municípios",
    version="1.0.0",
    description=(
        "Listagem paginada por **cursor**, filtros (`uf`, `q`), **ETag** e **304**, "
        "**Cache-Control**, compressão **Gzip/Brotli** e documentação **OpenAPI**."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(BrotliMiddleware, minimum_size=500, quality=5)
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
app.include_router(items.router)


@app.get("/", response_class=HTMLResponse, tags=["info"], summary="Página inicial com links")
def root() -> str:
    """Evita 404 ao abrir http://127.0.0.1:8000 no navegador; aponta para a documentação e exemplos."""
    return """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>API de municípios</title>
<style>
body{font-family:system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem 3rem;line-height:1.55;color:#1c1917}
h1{font-size:1.35rem;margin-bottom:.25rem}a{color:#0f766e}code{background:#f4f4f5;padding:.1rem .35rem;border-radius:4px;font-size:.9em}
.lead{color:#444;margin-top:0}.box{border:1px solid #e7e5e4;border-radius:10px;padding:.85rem 1rem;margin:1rem 0;background:#fafaf9}
.box h2{margin:0 0 .35rem;font-size:1rem}.box p{margin:.35rem 0 0;font-size:.9rem;color:#444}
.box p:first-of-type{margin-top:.5rem}
footer{margin-top:2rem;font-size:.85rem;color:#57534e}
</style></head><body>
<h1>API de municípios (REDES)</h1>
<p class="lead">Isto é uma <strong>API REST</strong>: o servidor responde pedidos HTTP com <strong>JSON</strong> para programas (ou para você testar). Não é um “site” com várias páginas HTML para navegar.</p>

<div class="box"><h2><a href="/docs">Swagger UI</a> <code>/docs</code></h2>
<p><strong>O que é:</strong> painel gerado automaticamente a partir da especificação OpenAPI.</p>
<p><strong>Para que serve:</strong> abrir cada rota (ex.: <code>GET /items</code>), preencher <code>limit</code>, <code>cursor</code>, etc., clicar em <strong>Execute</strong> e ver <strong>Response body</strong> (JSON) e <strong>Response headers</strong> (ETag, cache…).</p></div>

<div class="box"><h2><a href="/redoc">ReDoc</a> <code>/redoc</code></h2>
<p><strong>O que é:</strong> outra visualização da <em>mesma</em> documentação, em formato de manual longo.</p>
<p><strong>Para que serve:</strong> ler descrições com calma. Para <strong>testar</strong> cliques, prefira o Swagger.</p></div>

<div class="box"><h2><a href="/openapi.json">OpenAPI JSON</a> <code>/openapi.json</code></h2>
<p><strong>O que é:</strong> arquivo JSON grande que descreve todas as rotas e parâmetros (a “planta” da API).</p>
<p><strong>Para que serve:</strong> ferramentas (Swagger, Postman…) leem isso sozinhas. Você não precisa decorar o arquivo na prova — só saber que é a fonte da documentação.</p></div>

<div class="box"><h2><a href="/health"><code>/health</code></a></h2>
<p><strong>O que é:</strong> rota mínima de “está no ar?”.</p>
<p><strong>Resposta típica:</strong> <code>{"status":"ok"}</code>. Em produção, monitoramento consulta isso o tempo todo.</p></div>

<div class="box"><h2>Exemplo <a href="/items?limit=5"><code>/items?limit=5</code></a></h2>
<p><strong>O que é:</strong> primeira “página” da lista de municípios, no máximo 5 registros.</p>
<p><strong>Partes da URL:</strong> <code>/items</code> = recurso lista; <code>?</code> = início dos parâmetros; <code>limit=5</code> = tamanho da página. No navegador você vê JSON puro — normal parecer “feio”; no Swagger fica organizado.</p></div>

<footer>Guia detalhado (cada termo, cada tela do Swagger): arquivo <code>COMO_USAR_E_APRESENTAR.md</code> na pasta do projeto — seções 2 e 3.</footer>
</body></html>"""


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
