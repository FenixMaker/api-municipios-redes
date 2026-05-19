# REDES (API de municípios) — Entender do zero + onde mostrar + o que falar

Use este arquivo como **roteiro de ensaio**. As seções **2 e 3** explicam **cada link** da página inicial e **cada parte do Swagger**; a seção **6** é o script da apresentação. A API devolve **JSON** (dados para programas); a demonstração na aula costuma ser no **Swagger** em **`/docs`**.

---

## 0. Antes de apresentar (checklist)

| Verificação | Onde / como |
|-------------|-------------|
| API rodando | Pasta `REDES`, terminal com `uvicorn` ou duplo clique em **`iniciar-api.bat`**. Deve aparecer algo como `Uvicorn running on http://127.0.0.1:8000`. |
| Navegador | Abra **`http://127.0.0.1:8000/docs`** (Swagger). Guarde também **`http://127.0.0.1:8000`** — página com links. |
| VS Code (opcional) | Abra `app/routers/items.py` para mostrar o **304** se pedirem código. |
| Banco existe | Se a API subir sem erro, em geral já existe `data\ibge_api.db` ou o `.bat` criou um banco pequeno. |

---

## 1. Entenda em 2 minutos (o que esse projeto **é**)

Pense em um **garçom** (a API) e um **cliente** (navegador, app, ou Swagger):

- O cliente pede: “me dê **alguns** municípios, não todos”.
- O garçom traz um **JSON** (texto estruturado) com uma **página** de resultados e uma **dica** de como pedir a próxima página (`next_cursor`).
- Se o cliente disser: “eu **já tenho** essa página; minha etiqueta é **esta**” (`If-None-Match` com o mesmo **ETag** de antes) e **nada mudou** no servidor, o garçom responde **304 Not Modified** e **não manda o prato de novo** (corpo vazio) — economiza banda e trabalho.

**Uma frase para abrir a boca:**  
“É uma **API REST** em FastAPI sobre SQLite que expõe municípios com **paginação por cursor**, **filtros**, **JSON compacto ou completo**, **compressão Gzip/Brotli**, cabeçalhos de **cache**, e **ETag com 304** para o cliente não baixar de novo o que não mudou.”

---

## 2. A página `http://127.0.0.1:8000` — o que é **cada coisa** da lista

Quando você abre só o **endereço raiz** da API, aparece uma página HTML **simples** com links. Isso **não** é o “sistema completo”; é um **índice** para você não se perder.

### Por que diz “API REST, não um site”?

| Ideia | Explicação |
|-------|------------|
| **Site comum** (loja, Netflix, portal) | Muitas páginas HTML, botões, imagens — feito para **humano** clicar. |
| **API REST** | Um **serviço** no servidor que **responde pedidos HTTP** (URLs + método **GET**, etc.) e devolve principalmente **JSON** para **outro programa** (celular, front-end, Swagger). O navegador **pode** mostrar JSON “cru”; não é o foco de UX. |

### Cada link da lista — o que é e quando usar

#### Swagger UI → `/docs`

| Você vê o nome… | O que é, na prática |
|-----------------|---------------------|
| **Swagger** | Nome popular de uma **ferramenta visual** que lê a especificação **OpenAPI** e deixa **testar** a API com cliques (sem Postman obrigatório). |
| **UI** | “User interface” — interface gráfica. |

**Dentro do Swagger** (detalhado na **§3**): aparecem **GET**, **Parameters**, **Try it out**, **Execute**, **Response body**, etc. Tudo isso é “vocabário” de API; a **§3** explica linha por linha.

#### ReDoc → `/redoc`

| O que é | Diferença do Swagger |
|---------|----------------------|
| Outra página que lê a **mesma** especificação OpenAPI. | Texto em formato **manual** (rolagem longa). Ótimo para **ler** definições; para **clicar e testar**, prefira o **Swagger**. |

#### OpenAPI JSON → `/openapi.json`

| O que é | Por que existe |
|---------|----------------|
| Um arquivo **JSON** (muito texto) descrevendo **todas** as rotas, parâmetros, tipos de dados e respostas. | É a “**planta baixa**” em formato **máquina**. O Swagger e o ReDoc **montam a tela** a partir desse arquivo. Você **não** precisa entender cada linha do JSON na prova; precisa saber que é a **documentação oficial gerada**. |

#### `/health`

| O que é | O que aparece |
|---------|----------------|
| Rota **mínima** de “está vivo?”. | Geralmente `{"status":"ok"}`. Em servidores reais, **monitoramento** chama isso de minuto em minuto. |

#### Exemplo `/items?limit=5`

| Parte da URL | Significado |
|----------------|-------------|
| `/items` | Caminho (**path**) do recurso: **lista** de municípios. |
| `?` | Começo dos **query parameters** (parâmetros na própria URL). |
| `limit=5` | “Devolva **no máximo 5** itens nesta página.” |

Abrir isso no navegador mostra **JSON puro** — normal parecer “código estranho”.

#### `COMO_USAR_E_APRESENTAR.md`

Este arquivo (em parte) — guia longo na pasta do projeto para estudo e apresentação.

---

## 3. Dentro do Swagger (`/docs`) — o que cada parte da tela significa

Ao abrir o Swagger você vê **tags** (grupos), por exemplo **items** e **health**. Cada rota é um bloco expansível.

### `GET /items` — o que significa essa linha?

| Trecho | Significado |
|--------|-------------|
| **GET** | Método HTTP de **leitura**: “me **mostre** dados”. Não é usado aqui para apagar ou alterar banco. |
| **`/items`** | Recurso “**coleção**” de itens (municípios). |

### Botões e blocos que você pode nunca ter visto

| Nome na tela | O que faz |
|--------------|-----------|
| **Try it out** | Libera edição dos parâmetros e o botão de enviar o pedido. Sem isso, a documentação é só leitura. |
| **Execute** | Envia o pedido HTTP para `http://127.0.0.1:8000/...` e mostra o resultado embaixo. |
| **Parameters** | Campos que viram **query string** (`?limit=5`) ou **cabeçalhos** HTTP, conforme a rota. |
| **Responses** / **Curl** | Mostra como repetir o mesmo pedido no **terminal** (programa `curl`) — é o pedido “de verdade”. |
| **Request URL** | A URL completa gerada (com `?` e `&`). |
| **Code** (em “Server response”) | **Código de status HTTP**: `200` OK com corpo, `304` sem mudança, `404` não encontrado, etc. |
| **Response headers** | Metadados da resposta (**antes** do JSON): `content-type`, `etag`, `cache-control`… |
| **Response body** | O **JSON** (ou vazio no 304). |
| **Authorize** (cadeado) | Em APIs com login/token. **Este projeto não usa** — pode ignorar. |

### Parâmetros comuns em `GET /items` (o que cada um faz)

| Parâmetro | Função |
|-----------|--------|
| `cursor` | “Traga registros **depois** deste `id`” — continuação da lista (**paginação por cursor**). |
| `limit` | Tamanho **máximo** da página (quantos itens). |
| `uf` | Filtra por **estado** (duas letras, ex.: `SP`). |
| `q` | Prefixo do **nome** do município (busca por começo do nome). |
| `fields` | `minimal` = JSON com chaves curtas; `full` = nomes longos nos campos. |
| `if_none_match` | No Swagger, costuma representar o cabeçalho **If-None-Match** (valor do **ETag** que você já tinha). Se bater com o servidor → resposta **304**. |

### O que você vê no **JSON** da primeira página (`GET /items`)

| Nome no JSON | O que é |
|--------------|---------|
| `data` | **Array** (lista) de municípios nesta página. |
| `meta` | Informações **sobre** a página: `limit`, `next_cursor` (próximo cursor ou `null`), `dataset_version` (versão do dataset para cache/ETag). |
| Chaves `i`, `c`, `n`, `u` (em `minimal`) | Abreviações: id interno, código estilo IBGE, nome, UF — para **menos bytes** na rede. |

---

## 4. Onde clicar (mapa rápido no Swagger)

Quando você abrir **`http://127.0.0.1:8000/docs`**:

| O que você quer mostrar | Onde clicar |
|-------------------------|-------------|
| Listar itens paginados | Seção **items** → **`GET /items`** → **Try it out** → preencha `limit` (ex.: `5`) → **Execute** |
| Ver JSON e cabeçalhos | Depois de **Execute**, role até **Response body** e **Response headers** |
| Segunda página (cursor) | No JSON da resposta, copie o valor de **`meta.next_cursor`**. De novo em **`GET /items`**, cole em **`cursor`** e **Execute** |
| Filtro por estado | Parâmetro **`uf`** = `SP` (duas letras) |
| JSON mais enxuto ou mais legível | Parâmetro **`fields`**: `minimal` ou `full` |
| Testar **304** | Primeiro **Execute** sem header; copie **`etag`** dos **Response headers**. Segunda vez: preencha **`if_none_match`** com o **mesmo** valor (com aspas se vier assim) → **Execute** → **Code** `304` |
| Um município só | **`GET /items/{item_id}`** com `item_id` = `1` |

**Dica:** o campo **`if_none_match`** pode aparecer no final dos parâmetros (é um **header** HTTP exposto pelo Swagger).

---

## 5. O que o trabalho pede ↔ onde mostrar

| Tema da disciplina | Onde **demonstrar** | Onde está no **código** (se abrirem o projeto) |
|--------------------|---------------------|-----------------------------------------------|
| Paginação por **cursor** | Swagger: `GET /items` com `limit`, depois `cursor` com `next_cursor` | `app/routers/items.py` + `app/services/items_query.py` |
| Paginação por **offset** (comparação) | Só se configurou `ENABLE_BENCHMARKS=1` — rota de debug no `README` | `items.py` — `debug/offset-page` |
| **ETag** + **304** | Swagger: duas chamadas `GET /items` com `If-None-Match` | `items.py` — `if_none_match` e `Response(status_code=304)` |
| **Cache-Control** | Response headers da mesma chamada | `_cache_headers` em `items.py` |
| **Gzip / Brotli** | Falar e, se quiser prova, `curl` com `Accept-Encoding` (README) | `app/main.py` — middlewares |
| JSON **menos verboso** | Parâmetro `fields=minimal` vs `full` | `app/schemas.py` |
| **OpenAPI** | A própria URL **`/docs`** + link **`/openapi.json`** | Gerado pelo FastAPI |

---

## 6. Apresentação passo a passo (script com tempos)

**Tempo sugerido:** 4 a 6 minutos.

---

### Momento A — O que é isso (40 s)

**Onde mostrar:** `http://127.0.0.1:8000` (página com links) **ou** direto `/docs`.

**O que falar:**  
“Isso não é um site com páginas HTML para humanos; é uma **API REST**. Quem consome é outro programa. Eu documentei com **OpenAPI**; o Swagger em **`/docs`** deixa testar os endpoints na hora.”

*(Clique no link **Swagger UI** se estiver na página inicial.)*

---

### Momento B — Paginação por cursor (90 s)

**Onde mostrar:** Swagger → **`GET /items`** → **Try it out**.

**O que fazer:**

1. `limit` = **5**. Deixe `cursor` vazio. **Execute**.
2. Mostre no **Response body**: array `data` com 5 itens e objeto **`meta`** com **`next_cursor`**.
3. Copie **`next_cursor`**. Rode de novo **`GET /items`** com **`cursor`** = esse número e mesmo `limit`.

**O que falar:**  
“Em vez de pedir ‘página 20.000’ com **offset**, que obriga o banco a **pular** muitas linhas, eu peço ‘me dê registros **com id maior que X**’. O **`next_cursor`** é o último id desta página; na próxima requisição continuo **do mesmo lugar** sem custo de offset alto.”

---

### Momento C — ETag e 304 (90 s)

**Onde mostrar:** ainda em **`GET /items`** (mesmos parâmetros, ex.: `limit=5`, `fields=minimal`).

**O que fazer:**

1. **Execute** a primeira vez. Em **Response headers**, localize **`etag`** (ex.: `"abc123..."`).
2. Copie o valor **completo** do ETag (com aspas duplas, se vier assim).
3. Rode **de novo** a mesma rota com os **mesmos** parâmetros, mas preencha **`if_none_match`** com esse valor. **Execute**.

**O que falar:**  
“O servidor manda um **ETag**, uma espécie de **versão** da resposta. Se o cliente manda **`If-None-Match`** com o mesmo valor e os dados não mudaram, a resposta é **304 Not Modified** — **sem corpo JSON**. Assim quem já tem a página em cache **não baixa de novo** milhões de registros.”

**Se der 200 em vez de 304:** confira se os parâmetros são **idênticos** (incluindo `fields`, `uf`, `q`) e se o ETag foi colado **inteiro**.

---

### Momento D — Filtros e JSON compacto (45 s)

**Onde mostrar:** Swagger, `GET /items`.

**O que fazer:**

1. `uf` = **`SP`**, `limit` = **10**, **Execute**.
2. Troque `fields` para **`full`** e **Execute** — mostre que os nomes dos campos no JSON mudam.

**O que falar:**  
“Os filtros vêm na **query string** (`uf`, `q` para prefixo do nome). O parâmetro **`fields`** troca entre JSON **minimal** — menos bytes na rede — e **full**, mais legível.”

---

### Momento E — Compressão e cache (30 s) — mais oral

**Onde mostrar:** pode ser só fala, ou os headers da resposta no Swagger.

**O que falar:**  
“Tem **middleware** de **Gzip** e **Brotli** conforme `Accept-Encoding`. Nos headers também mando **Cache-Control** para o cliente saber por quanto tempo pode reutilizar a resposta em cache local.”

---

### Momento F — Código (30 s) — se pedirem “mostre onde está”

**Onde mostrar:** VS Code → `app/routers/items.py`.

**O que fazer:** role até ver **`If-None-Match`** e **`status_code=304`**.

**O que falar:**  
“Aqui está a decisão: se o header bate com o ETag calculado, devolvo **304** sem montar o payload de novo.”

---

## 7. Glossário rápido

| Termo | Explicação curta |
|-------|-------------------|
| REST / API | Serviço por **HTTP** (URLs + verbos como GET) que devolve dados (aqui, JSON). |
| Paginação | Não mandar tudo; mandar **um pedaço** por vez. |
| Cursor | “Continuar **depois deste id**”; combina bem com índice e datasets grandes. |
| Offset | “Pular **N** linhas do início”; simples, mas pode ficar **lento** com N gigante. |
| ETag | Identificador da **versão** daquele recurso / daquela combinação de parâmetros. |
| 304 Not Modified | “Continue usando o que você já tem”; **sem corpo** na resposta. |
| OpenAPI | Descrição formal da API; o Swagger é uma **interface** em cima disso. |

---

## 8. Se você “não entendeu nada” — memorize só isto

1. **`GET /items`** devolve **uma página** de municípios em JSON, não o banco inteiro.  
2. **`next_cursor`** diz como pedir a **próxima** página.  
3. **ETag** + **`If-None-Match`** → **304** = “não preciso mandar o JSON de novo”.  
4. **`/docs`** prova tudo **sem Postman**.

---

## 9. Perguntas que o professor pode fazer

**“Por que SQLite?”**  
É um protótipo local; os **conceitos HTTP** são os mesmos em produção com PostgreSQL.

**“São 4 milhões de municípios?”**  
Não. O IBGE real tem ~**5,5 mil** municípios. O script **`seed_db.py`** gera dados **sintéticos** para testar **volume** (ex.: 4M). O README explica os dois modos.

**“Onde está a compressão?”**  
`app/main.py` — classes/middlewares **GZip** e **Brotli**.

---

## 10. Sobre uso de IA

Frase honesta:  
“Usei ferramentas para acelerar implementação e documentação, mas consigo **demonstrar** paginação, ETag/304 e filtros no Swagger e **apontar** no `items.py` onde a lógica acontece.”

---

*Ensaie uma vez: abra só o Swagger e faça os Momentos B e C sem olhar para baixo — isso fixa a apresentação.*
